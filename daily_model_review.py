#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, json, math, os, re, statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import requests
from review_delivery import deliver_once, record_publication, provider_status, require_completed_crypto_day
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
ANALYSIS_DIR = ROOT / "analysis" / "daily"

load_dotenv(ROOT / ".env.config")
load_dotenv(ROOT / ".env", override=True)

MODEL = os.getenv("DAILY_REVIEW_MODEL", "gpt-5.6-sol").strip()
MIN_SAMPLES = int(os.getenv("DAILY_REVIEW_MIN_PROPOSAL_SAMPLES", "12"))
PUSH_ENABLED = os.getenv("DAILY_REVIEW_PUSHOVER_ENABLED", "1").strip().lower() not in {"0","false","no"}

PUSH_TOKEN = (
    os.getenv("PUSHOVER_DAILY_REVIEW_TOKEN", "").strip()
    or os.getenv("PUSHOVER_CRYPTO_EOD_TOKEN", "").strip()
    or os.getenv("PUSHOVER_API_TOKEN", "").strip()
)
PUSH_USER = (
    os.getenv("PUSHOVER_DAILY_REVIEW_GROUP_KEY", "").strip()
    or os.getenv("PUSHOVER_CRYPTO_EOD_GROUP_KEY", "").strip()
    or os.getenv("PUSHOVER_USER_KEY", "").strip()
)

def args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date")
    ap.add_argument("--no-ai", action="store_true")
    phase = ap.add_mutually_exclusive_group()
    phase.add_argument("--defer-notification", action="store_true")
    phase.add_argument("--record-publication", action="store_true")
    phase.add_argument("--notify-only", action="store_true")
    return ap.parse_args()

def fnum(v: Any) -> Optional[float]:
    try:
        x = float(v)
        return x if math.isfinite(x) else None
    except Exception:
        return None

def read_csv(path: Path):
    if not path.exists():
        return []
    try:
        with path.open("r", newline="", encoding="utf-8-sig", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []

def read_json(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default

def med(vals):
    vals = [x for x in vals if x is not None and math.isfinite(x)]
    return statistics.median(vals) if vals else None

def pct(n,d):
    return 100*n/d if d else None

def summarize_trades(rows):
    buys = [r for r in rows if str(r.get("action","")).upper()=="BUY"]
    sells = [r for r in rows if str(r.get("action","")).upper()=="SELL"]
    pnl = [fnum(r.get("realized_pnl_usd")) for r in sells]
    pnl = [x for x in pnl if x is not None]
    rt = [fnum(r.get("roundtrip_preflight_pct")) for r in buys]
    rt = [x for x in rt if x is not None]
    reasons = defaultdict(int)
    for r in sells:
        reasons[str(r.get("reason") or "UNKNOWN")] += 1
    return {
        "buys":len(buys),"sells":len(sells),
        "realized_pnl_usd":round(sum(pnl),6) if pnl else 0.0,
        "win_rate_pct":round(pct(sum(x>0 for x in pnl),len(pnl)) or 0,2),
        "median_trade_pnl_usd":round(med(pnl) or 0,6),
        "median_preflight_roundtrip_pct":round(med(rt) or 0,4),
        "sell_reasons":dict(sorted(reasons.items(), key=lambda kv:(-kv[1],kv[0])))
    }

def summarize_followups(rows):
    if not rows:
        return {"rows":0}
    score_key = next((k for k in ("score","momentum_score") if k in rows[0]), None)
    path_key = next((k for k in ("entry_path","path","state") if k in rows[0]), None)
    horizon_fields = []
    for h in (5,15,30,60):
        for k in (f"return_{h}m_pct",f"return_{h}m",f"ret_{h}m_pct"):
            if k in rows[0]:
                horizon_fields.append((h,k)); break

    by_path = {}
    if path_key:
        groups = defaultdict(list)
        for r in rows:
            groups[str(r.get(path_key) or "UNKNOWN").upper()].append(r)
        for path, items in groups.items():
            d = {"n":len(items)}
            for h,k in horizon_fields:
                vals = [fnum(x.get(k)) for x in items]
                vals = [v for v in vals if v is not None]
                d[f"median_{h}m_return_pct"] = round(med(vals),3) if vals else None
                d[f"positive_{h}m_pct"] = round(pct(sum(v>0 for v in vals),len(vals)),2) if vals else None
            by_path[path]=d

    score_bands = {}
    if score_key:
        for lo,hi in ((0,79),(80,99),(100,119),(120,139),(140,9999)):
            items = []
            for r in rows:
                s = fnum(r.get(score_key))
                if s is not None and lo <= s <= hi:
                    items.append(r)
            if items:
                d={"n":len(items)}
                for h,k in horizon_fields:
                    vals=[fnum(x.get(k)) for x in items]
                    vals=[v for v in vals if v is not None]
                    d[f"median_{h}m_return_pct"]=round(med(vals),3) if vals else None
                score_bands[f"{lo}-{hi if hi<9999 else '+'}"]=d
    return {"rows":len(rows),"by_path":by_path,"score_bands":score_bands,
            "horizons_found":[h for h,_ in horizon_fields]}

def summarize_ai(rows):
    if not rows: return {"rows":0}
    counts=defaultdict(int); conf=[]
    for r in rows:
        counts[str(r.get("setup_type") or r.get("assessment") or "UNKNOWN").upper()] += 1
        x=fnum(r.get("confidence"))
        if x is not None: conf.append(x)
    return {"rows":len(rows),"setup_counts":dict(counts),
            "median_confidence":round(med(conf),2) if conf else None}

def summarize_smart_money(campaigns, scorecard):
    latest={}
    for r in campaigns:
        cid=str(r.get("campaign_id") or "")
        if cid: latest[cid]=r
    strengths=[fnum(r.get("campaign_strength_score")) for r in latest.values()]
    strengths=[x for x in strengths if x is not None]
    convergence=sum((fnum(r.get("converging_trader_count")) or 0)>=2 for r in latest.values())

    perf=[]
    for r in scorecard:
        if int(fnum(r.get("horizon_minutes")) or 0)==30:
            perf.append({
                "trader":r.get("trader_name"),
                "sample_count":int(fnum(r.get("sample_count")) or 0),
                "median_return_pct":fnum(r.get("median_return_pct")),
                "positive_rate_pct":fnum(r.get("positive_rate_pct")),
                "return_10plus_rate_pct":fnum(r.get("return_10plus_rate_pct")),
                "median_strength_score":fnum(r.get("median_strength_score")),
            })
    return {
        "campaign_rows":len(campaigns),"unique_campaigns":len(latest),
        "median_campaign_strength":round(med(strengths),3) if strengths else None,
        "multi_wallet_convergence_count":convergence,
        "wallet_30m_scorecard":perf
    }

def summarize_luna_outcomes(rows):
    if not rows:
        return {"rows":0,"signals":0,"labeled_rows":0}
    signal_ids={str(r.get("signal_id") or "") for r in rows if r.get("signal_id")}
    labeled=[r for r in rows if int(fnum(r.get("outcome_labeled")) or 0)==1]
    groups={}
    grouped=defaultdict(list)
    for r in labeled:
        key=(
            str(r.get("ai_assessment") or "UNKNOWN").upper(),
            str(r.get("ai_confidence_band") or "UNKNOWN").upper(),
            int(fnum(r.get("horizon_minutes")) or 0),
        )
        grouped[key].append(r)
    for key,items in grouped.items():
        vals=[fnum(x.get("return_pct")) for x in items]
        vals=[v for v in vals if v is not None]
        mfe=[fnum(x.get("mfe_pct")) for x in items]
        mfe=[v for v in mfe if v is not None]
        mae=[fnum(x.get("mae_pct")) for x in items]
        mae=[v for v in mae if v is not None]
        groups["|".join(map(str,key))]={
            "n":len(items),
            "median_return_pct":round(med(vals),3) if vals else None,
            "positive_rate_pct":round(pct(sum(v>0 for v in vals),len(vals)),2) if vals else None,
            "median_mfe_pct":round(med(mfe),3) if mfe else None,
            "median_mae_pct":round(med(mae),3) if mae else None,
        }
    return {
        "rows":len(rows),
        "signals":len(signal_ids),
        "labeled_rows":len(labeled),
        "groups":groups,
    }


def summarize_feed_health(rows):
    if not rows:
        return {"rows":0}
    coverage=[fnum(r.get("wallet_coverage_pct")) for r in rows]
    coverage=[x for x in coverage if x is not None]
    failed=sum(int(fnum(r.get("failed_wallet_checks")) or 0) for r in rows)
    event_delta=sum(int(fnum(r.get("event_rows_delta")) or 0) for r in rows)
    campaign_delta=sum(int(fnum(r.get("campaign_rows_delta")) or 0) for r in rows)
    propagation_issues=sum(
        str(r.get("event_to_campaign_status") or "").upper()=="EVENTS_WITHOUT_CAMPAIGN_UPDATE"
        for r in rows
    )
    latest=rows[-1]
    return {
        "rows":len(rows),
        "latest_status":str(latest.get("status") or "UNKNOWN").upper(),
        "latest_wallet_coverage_pct":fnum(latest.get("wallet_coverage_pct")),
        "median_wallet_coverage_pct":round(med(coverage),2) if coverage else None,
        "failed_wallet_checks":failed,
        "event_rows_delta":event_delta,
        "campaign_rows_delta":campaign_delta,
        "event_without_campaign_cycles":propagation_issues,
        "latest_error":str(latest.get("last_error") or "")[:300],
    }


def summarize_missed_audit(rows):
    if not rows:
        return {"rows":0}
    latest=rows[-1]
    return {
        "rows":len(rows),
        "latest_status":str(latest.get("status") or "UNKNOWN").upper(),
        "signal_rows":int(fnum(latest.get("signal_rows")) or 0),
        "rejected_signal_rows":int(fnum(latest.get("rejected_signal_rows")) or 0),
        "usable_rejected_signals":int(fnum(latest.get("usable_rejected_signals")) or 0),
        "report_exists":int(fnum(latest.get("report_exists")) or 0),
        "sample_30_rows":int(fnum(latest.get("sample_30_rows")) or 0),
        "sample_60_rows":int(fnum(latest.get("sample_60_rows")) or 0),
    }


def summarize_paper_models(rows):
    models = defaultdict(list)
    for row in rows:
        if str(row.get("action") or "").upper() == "SELL":
            models[str(row.get("model") or "UNKNOWN")].append(row)

    def max_drawdown(returns):
        equity = 1.0
        peak = 1.0
        worst = 0.0
        for value in returns:
            equity *= max(0.000001, 1.0 + value / 100.0)
            peak = max(peak, equity)
            if peak > 0:
                worst = max(worst, (peak - equity) / peak * 100.0)
        return worst

    result = []
    for name, items in models.items():
        returns = [fnum(r.get("net_return_pct")) for r in items]
        returns = [x for x in returns if x is not None]
        pnls = [fnum(r.get("realized_pnl_usd")) for r in items]
        pnls = [x for x in pnls if x is not None]

        # Shadow cohorts do not have dollar PnL; use return sign for W/L
        # and keep realized PnL at zero so they remain research-only.
        sign_source = pnls if pnls else returns
        gross_win = sum(x for x in sign_source if x > 0)
        gross_loss = abs(sum(x for x in sign_source if x < 0))
        result.append({
            "model": name,
            "completed": len(items),
            "wins": sum(x > 0 for x in sign_source),
            "losses": sum(x < 0 for x in sign_source),
            "win_rate_pct": round(
                pct(sum(x > 0 for x in sign_source), len(sign_source)) or 0,
                2,
            ),
            "realized_pnl_usd": round(sum(pnls), 8),
            "avg_net_return_pct": round(
                sum(returns) / len(returns),
                4,
            ) if returns else 0.0,
            "median_net_return_pct": round(med(returns) or 0, 4),
            "profit_factor": (
                round(gross_win / gross_loss, 4)
                if gross_loss
                else (999.0 if gross_win else 0.0)
            ),
            "max_drawdown_pct": round(max_drawdown(returns), 4),
        })

    ranked = sorted(
        result,
        key=lambda x: (
            x["completed"] >= 12,
            x["avg_net_return_pct"],
            min(x["profit_factor"], 10.0),
            -x["max_drawdown_pct"],
            x["median_net_return_pct"],
            x["realized_pnl_usd"],
        ),
        reverse=True,
    )
    return {
        "models": ranked,
        "completed_across_models": sum(x["completed"] for x in ranked),
        "preliminary_leader": (
            ranked[0]["model"]
            if ranked and ranked[0]["completed"] >= 12
            else None
        ),
        "promotion_candidates": [
            x["model"]
            for x in ranked
            if x["completed"] >= 30
            and x["avg_net_return_pct"] > 0
            and x["profit_factor"] >= 1.3
            and x["max_drawdown_pct"] <= 15
        ],
    }

def build_metrics(raw: Path):
    trade_files = sorted(raw.glob("trades_*.csv"))
    trades = read_csv(trade_files[-1]) if trade_files else []
    followups = read_csv(raw/"surge_followup_log.csv")
    ai = read_csv(raw/"ai_confirmation_log.csv")
    luna_outcome_files = sorted(raw.glob("luna_outcomes_*.csv"))
    luna_outcomes = read_csv(luna_outcome_files[-1]) if luna_outcome_files else []
    feed_health = read_csv(raw/"smart_money_feed_health_v23.csv")
    missed_audit = read_csv(raw/"missed_opportunity_audit.csv")
    paper_trades = read_csv(raw/"paper_trades.csv")
    shadow_trades = read_csv(raw/"shadow_trades.csv")
    campaigns = read_csv(raw/"smart_money_campaigns_v22.csv") or read_csv(raw/"smart_money_campaigns_v21.csv")
    scorecard = read_csv(raw/"wallet_scorecard_v22.csv")
    return {
        "trades":summarize_trades(trades),
        "followups":summarize_followups(followups),
        "luna":summarize_ai(ai),
        "luna_outcomes":summarize_luna_outcomes(luna_outcomes),
        "smart_money":summarize_smart_money(campaigns,scorecard),
        "smart_money_feed_health":summarize_feed_health(feed_health),
        "missed_opportunity_audit":summarize_missed_audit(missed_audit),
        "paper_research":summarize_paper_models(paper_trades),
        "paper_shadow_research":summarize_paper_models(shadow_trades),
        "files_present":sorted(p.name for p in raw.glob("*") if p.is_file())
    }

def deterministic_findings(metrics):
    out=[]
    t=metrics["trades"]
    if t["sells"]:
        out.append(f"{t['sells']} completed sells; realized P/L ${t['realized_pnl_usd']:.4f}; win rate {t['win_rate_pct']:.1f}%.")
    f=metrics["followups"]
    if f.get("rows"):
        out.append(f"{f['rows']} follow-up observations available across horizons {f.get('horizons_found',[])}.")
    s=metrics["smart_money"]
    if s.get("unique_campaigns"):
        out.append(f"{s['unique_campaigns']} smart-money campaigns; {s['multi_wallet_convergence_count']} multi-wallet convergence events.")
    fh=metrics.get("smart_money_feed_health",{})
    if fh.get("rows"):
        out.append(
            f"Smart-money feed health {fh.get('latest_status','UNKNOWN')}; "
            f"latest wallet coverage {fh.get('latest_wallet_coverage_pct')}%; "
            f"failed wallet checks {fh.get('failed_wallet_checks',0)}."
        )
    lo=metrics.get("luna_outcomes",{})
    if lo.get("rows"):
        out.append(
            f"Luna outcome scorecard has {lo.get('signals',0)} signal(s) and "
            f"{lo.get('labeled_rows',0)} labeled horizon rows."
        )
    ma=metrics.get("missed_opportunity_audit",{})
    if ma.get("rows"):
        out.append(
            f"Missed-opportunity audit status {ma.get('latest_status','UNKNOWN')}; "
            f"{ma.get('usable_rejected_signals',0)} rejected signal(s) have usable forward horizons."
        )
    pr=metrics.get("paper_research",{})
    if pr.get("completed_across_models"):
        out.append(
            f"Executable paper laboratory completed {pr['completed_across_models']} exits across models; "
            f"preliminary leader {pr.get('preliminary_leader') or 'not established'}."
        )
    ps=metrics.get("paper_shadow_research",{})
    if ps.get("completed_across_models"):
        out.append(
            f"Multi-candidate shadow laboratory completed {ps['completed_across_models']} exits; "
            f"preliminary shadow leader {ps.get('preliminary_leader') or 'not established'}."
        )
    if not out:
        out.append("Insufficient same-day data for a reliable deterministic conclusion.")
    return out

def ai_review(date_str, metrics, manifest, config_text):
    try:
        from openai import OpenAI
    except Exception as e:
        return {"error":f"OpenAI SDK unavailable: {e}","proposals":[]}
    if not os.getenv("OPENAI_API_KEY","").strip():
        return {"error":"OPENAI_API_KEY not configured.","proposals":[]}

    schema = {
        "proposal_id":"P-YYYYMMDD-NN","title":"short title",
        "change_type":"CONFIG|CODE|RESEARCH","target":"setting/component",
        "current":"current value/state","proposed":"proposed value/state",
        "evidence":["fact 1","fact 2"],"risk":"specific downside",
        "confidence":"LOW|MEDIUM|HIGH","recommended_mode":"SHADOW|PAPER|LIVE",
        "approval_required":True
    }

    prompt=f"""
You are the quantitative research reviewer for CryptoTracker, a live momentum
trading research system. Review the DAILY evidence and propose only evidence-
supported improvements.

Rules:
- Never present a small sample as proven.
- If fewer than {MIN_SAMPLES} relevant observations exist, prefer RESEARCH/SHADOW.
- Analyze entry quality, execution, exits, Luna calibration, smart-money
  campaign strength, and missed opportunities separately.
- Use medians, hit rates, sample sizes, MFE/MAE when available, and false-positive cost.
- Prefer one-variable-at-a-time changes.
- Every proposal requires explicit human approval.
- Never edit code or deploy.
- Return STRICT JSON only:
{{
 "executive_summary":["..."],
 "diagnostics":["..."],
 "proposals":[{json.dumps(schema)}],
 "no_change_recommended":false
}}

DATE:
{date_str}

MANIFEST:
{json.dumps(manifest,indent=2)[:12000]}

METRICS:
{json.dumps(metrics,indent=2)[:30000]}

NON-SECRET CONFIG:
{config_text[:16000]}
"""
    try:
        client=OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        r=client.responses.create(model=MODEL,reasoning={"effort":"high"},input=prompt)
        text=(getattr(r,"output_text","") or "").strip()
        text=re.sub(r"^```(?:json)?\s*","",text)
        text=re.sub(r"\s*```$","",text)
        data=json.loads(text)
        data.setdefault("proposals",[])
        return data
    except Exception as e:
        return {"error":f"AI review failed: {e}","proposals":[]}

def assign_ids(date_str, proposals):
    ymd=date_str.replace("-","")
    out=[]
    for i,p in enumerate(proposals,1):
        q=dict(p)
        q["proposal_id"]=f"P-{ymd}-{i:02d}"
        q["approval_required"]=True
        out.append(q)
    return out

def render_md(date_str, findings, review):
    lines=[f"# CryptoTracker Daily Model Review — {date_str}","",
           "## Deterministic findings"]
    lines += [f"- {x}" for x in findings]
    lines += ["","## Executive summary"]
    lines += [f"- {x}" for x in review.get("executive_summary",[])]
    lines += ["","## Diagnostics"]
    lines += [f"- {x}" for x in review.get("diagnostics",[])]
    ps=review.get("proposals",[])
    lines += ["",f"## Proposed changes ({len(ps)})"]
    if not ps: lines.append("No model changes proposed.")
    for p in ps:
        lines += [
            "",f"### {p.get('proposal_id')} — {p.get('title','Untitled')}",
            f"- **Type:** {p.get('change_type')}",
            f"- **Target:** `{p.get('target')}`",
            f"- **Current:** {p.get('current')}",
            f"- **Proposed:** {p.get('proposed')}",
            f"- **Confidence:** {p.get('confidence')}",
            f"- **Mode:** {p.get('recommended_mode')}",
            f"- **Risk:** {p.get('risk')}",
            "- **Evidence:**"
        ]
        lines += [f"  - {e}" for e in p.get("evidence",[])]
        lines.append("- **Approval required:** YES")
    if review.get("error"):
        lines += ["","## Review engine note",review["error"]]
    lines += ["","## Approval",
              "Reply in ChatGPT with exact proposal IDs, for example:",
              "`Approve P-YYYYMMDD-01; decline P-YYYYMMDD-02; shadow-test P-YYYYMMDD-03.`",
              "","**No code is changed by this review script.**"]
    return "\n".join(lines)+"\n"

def send_push(date_str, review):
    if not PUSH_ENABLED: return "DISABLED"
    if not PUSH_TOKEN or not PUSH_USER: return "CONFIG_MISSING"
    ps=review.get("proposals",[])
    lines=[f"CryptoTracker Daily Review {date_str}",f"{len(ps)} proposal(s) ready."]
    if review.get("executive_summary"):
        lines.append(str(review["executive_summary"][0])[:350])
    for p in ps[:4]:
        lines.append(f"{p.get('proposal_id')}: {p.get('title')} [{p.get('confidence')}/{p.get('recommended_mode')}]")
    lines.append("Open ChatGPT to approve/decline.")
    try:
        r=requests.post("https://api.pushover.net/1/messages.json",data={
            "token":PUSH_TOKEN,"user":PUSH_USER,
            "title":"CryptoTracker Daily Model Review",
            "message":"\n".join(lines)[:1024],"priority":0
        },timeout=20)
        return provider_status(r)
    except Exception:
        return "UNCONFIRMED"


def handle_notification_phase(args, day):
    if not (args.record_publication or args.notify_only):
        return False
    path = ANALYSIS_DIR / day / "daily_model_review.json"
    state = ROOT / "deploy" / "state" / "eod_review_delivery"
    if args.record_publication:
        record_publication(ROOT, state, "CryptoTracker", day, path)
        print("Publication verified for " + day)
    else:
        review = json.loads(path.read_text(encoding="utf-8"))
        status = deliver_once(state, "CryptoTracker", day, path,
                              lambda saved_review: send_push(day, saved_review))
        print("Model-review provider status: " + status)
        if status != "API_ACCEPTED":
            raise SystemExit(4)
    return True


def main():
    a=args()
    if not a.date:
        raise SystemExit("An explicit completed Pacific --date is required")
    date_str=a.date
    require_completed_crypto_day(date_str)
    if handle_notification_phase(a, date_str):
        return
    bundle=ANALYSIS_DIR/date_str
    manifest=read_json(bundle/"manifest.json",{}) or {}
    if not manifest:
        print(f"ERROR: no bundle for {date_str}. Run build_daily_review_bundle.py first.")
        raise SystemExit(2)

    raw=bundle/"raw"
    cfg=bundle/"meta"/".env.config"
    config_text=cfg.read_text(encoding="utf-8",errors="replace") if cfg.exists() else ""
    metrics=build_metrics(raw)
    findings=deterministic_findings(metrics)

    review = ({
        "executive_summary":findings,"diagnostics":[],"proposals":[],
        "no_change_recommended":True,"error":"AI review skipped by --no-ai."
    } if a.no_ai else ai_review(date_str,metrics,manifest,config_text))

    review["proposals"]=assign_ids(date_str,review.get("proposals",[]))
    review["review_date"]=date_str
    review["model"]=MODEL
    review["deterministic_metrics"]=metrics
    review["deterministic_findings"]=findings

    (bundle/"daily_model_review.json").write_text(json.dumps(review,indent=2),encoding="utf-8")
    (bundle/"daily_model_review.md").write_text(render_md(date_str,findings,review),encoding="utf-8")
    status="DEFERRED_UNTIL_PUBLICATION"

    print(f"Daily review written: {bundle/'daily_model_review.md'}")
    print(f"Proposals: {len(review.get('proposals',[]))}")
    print(f"Pushover: {status}")

if __name__=="__main__":
    main()
