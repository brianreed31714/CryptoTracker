"""Disabled-by-default paper adapter. No signer, transaction or order submission.

The existing caller injects its quote-only GET function without a taker. This
module never imports the trader or a network client. Activation is a separate
local paper release manifest; no manifest is shipped or created by this PR.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import tempfile

from research.strategy16_paper import (
    IMPLEMENTATION_SHA256, PaperStudy, ProspectiveCollector, StudyPolicy, digest, number,
)

PRODUCER='auto_trader_with_alerts_v11_10_research_fairness.py'
ADAPTER_SHA256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def release_identity(root):
    root=Path(root)
    return {'implementation_sha256':hashlib.sha256(
                Path(__file__).with_name('strategy16_paper.py').read_bytes()+
                Path(__file__).with_name('strategy16_shadow.py').read_bytes()).hexdigest(),
            'adapter_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'lab_sha256':hashlib.sha256((root/'paper_research_lab_v11_10.py').read_bytes()).hexdigest(),
            'producer_sha256':hashlib.sha256((root/PRODUCER).read_bytes()).hexdigest()}


class SizedQuoteAdapter:
    def __init__(self, get_quote, usdc_mint, *, clock=None):
        self.get_quote=get_quote
        self.usdc_mint=usdc_mint
        self.clock=clock or (lambda:datetime.now(timezone.utc))

    def __call__(self, token, side, amount):
        if not token or token==self.usdc_mint or side not in ('BUY','SELL'):
            raise ValueError('Invalid quote direction/token')
        raw=number(amount)*(1000000 if side=='BUY' else 1)
        if raw<=0 or raw!=int(raw):
            raise ValueError('Quote amount must be positive raw units')
        source,target=(self.usdc_mint,token) if side=='BUY' else (token,self.usdc_mint)
        # Deliberately accepts only three arguments: no taker or signer.
        response=self.get_quote(source,target,int(raw))
        if (not isinstance(response,dict) or response.get('errorCode') or response.get('error')
            or response.get('inputMint')!=source or response.get('outputMint')!=target
            or number(response.get('inAmount'))!=raw):
            raise ValueError('Quote response identity/size/error mismatch')
        output=number(response.get('outAmount'))
        if output<=0 or output!=int(output):
            raise ValueError('Invalid raw quote output')
        if response.get('otherAmountThreshold') is not None:
            threshold=number(response['otherAmountThreshold'])
            if threshold<=0 or threshold>output or threshold!=int(threshold):
                raise ValueError('Invalid conservative output threshold')
            output=threshold
        # Without a threshold, outAmount remains an indicative quote; the
        # explicit study slippage/fee assumptions still apply. Never a fill.
        output=output/(1000000 if side=='SELL' else 1)
        provenance={k:response.get(k) for k in ('inputMint','outputMint','inAmount','outAmount',
                                             'otherAmountThreshold','requestId','router','slippageBps')}
        return dict(status='OK',token_address=token,side=side,input_amount=str(amount),
                    output_amount=str(output),timestamp=self.clock().isoformat(),
                    source_sha256=digest(provenance),data_quality_flags='')


def configured_observer(root, get_quote, usdc_mint, *, live_trading=False,
                        loaded_lab_sha256=None, loaded_producer_sha256=None):
    """Return None without touching state/network unless a local opt-in exists."""
    root=Path(root)
    directory=root/'data/strategy16'
    activation=directory/'activation.json'
    if not activation.exists():
        return None
    manifest=json.loads(activation.read_text(encoding='utf-8'))
    if live_trading is not False or manifest.get('mode')!='PAPER_ONLY':
        raise ValueError('Strategy16 activation is paper-only')
    release=release_identity(root)
    if (manifest.get('release')!=release or release['implementation_sha256']!=IMPLEMENTATION_SHA256
        or release['adapter_sha256']!=ADAPTER_SHA256 or release['lab_sha256']!=loaded_lab_sha256
        or release['producer_sha256']!=loaded_producer_sha256):
        raise ValueError('Strategy16 release identity mismatch')
    study=PaperStudy(directory/'study.sqlite3',StudyPolicy(**manifest['policy']))
    collector=ProspectiveCollector(study,SizedQuoteAdapter(get_quote,usdc_mint))

    def observe(**kwargs):
        report=collector(**kwargs)
        # Database is authoritative. Publish a separate atomic private view;
        # no account amounts or raw provider response enter source control.
        temp=None
        try:
            with tempfile.NamedTemporaryFile(mode='w',encoding='utf-8',dir=directory,
                                             suffix='.tmp',delete=False) as handle:
                temp=Path(handle.name)
                json.dump(study.report(),handle,indent=2)
            temp.replace(directory/'latest.json')
        finally:
            if temp is not None and temp.exists():
                temp.unlink()
        return report
    return observe
