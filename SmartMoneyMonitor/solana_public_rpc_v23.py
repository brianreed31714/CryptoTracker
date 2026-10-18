"""Read-only, credit-safe Solana wallet observation via public JSON-RPC.

Conservative evidence: watched wallet must sign a successful transaction,
spend exactly one USDC/USDT quote token and receive exactly one non-quote
token. This is a swap *heuristic*, not authoritative DEX trade classification.
Never sends a transaction or accesses Helius.
"""
import os
import time
import requests

USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
USDT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
WSOL = "So11111111111111111111111111111111111111112"
QUOTES = {USDC, USDT, WSOL}
_LAST_CALL = 0.0

def rpc(method, params):
    global _LAST_CALL
    url = os.getenv("SMART_MONEY_SOLANA_RPC_URL", "https://api.mainnet-beta.solana.com")
    if not url.startswith("https://") or "helius" in url.lower():
        raise ValueError("Smart Money public RPC must use HTTPS and may not use Helius")
    interval = max(1.0, float(os.getenv("SMART_MONEY_RPC_MIN_INTERVAL_SECONDS", "3")))
    wait = interval - (time.monotonic() - _LAST_CALL)
    if wait > 0:
        time.sleep(wait)
    _LAST_CALL = time.monotonic()
    response = requests.post(url, json={"jsonrpc":"2.0", "id":1,
                                        "method":method, "params":params}, timeout=15)
    response.raise_for_status()
    data = response.json()
    if data.get("error"):
        raise RuntimeError("Solana RPC %s: %s" % (method, data["error"]))
    return data.get("result")

def recent_signatures(wallet, limit=10):
    n = max(1, min(20, int(limit)))
    return rpc("getSignaturesForAddress",
               [wallet, {"limit":n, "commitment":"confirmed"}]) or []

def _balances(items, wallet):
    result = {}
    for item in items or []:
        if item.get("owner") != wallet:
            continue
        mint = item.get("mint")
        raw = (item.get("uiTokenAmount") or {}).get("uiAmountString")
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if not mint:
            continue
        result[mint] = result.get(mint, 0.0) + value
    return result

def _signed_by_wallet(tx, wallet):
    message = ((tx.get("transaction") or {}).get("message") or {})
    keys = message.get("accountKeys") or []
    return any(isinstance(item, dict) and item.get("pubkey") == wallet
               and item.get("signer") is True for item in keys)

def classify_swap(tx, wallet):
    if not tx or not tx.get("meta") or tx["meta"].get("err") is not None:
        return None
    if not _signed_by_wallet(tx, wallet):
        return None
    meta = tx["meta"]
    pre = _balances(meta.get("preTokenBalances"), wallet)
    post = _balances(meta.get("postTokenBalances"), wallet)
    delta = {mint:post.get(mint,0) - pre.get(mint,0) for mint in pre.keys() | post.keys()}
    bought = [(mint,qty) for mint,qty in delta.items() if mint not in QUOTES and qty > 0]
    spent = [(mint,-delta.get(mint,0)) for mint in (USDC,USDT) if delta.get(mint,0) < 0]
    if len(bought) != 1 or len(spent) != 1:
        return None
    mint, amount = bought[0]
    quote, cost = spent[0]
    if cost <= 0:
        return None
    return {"token_mint":mint, "token_amount_received":amount,
            "spend_asset":"USDC" if quote == USDC else "USDT",
            "spend_amount":cost, "estimated_spend_usd":cost}

def fetch_transaction(signature):
    return rpc("getTransaction", [signature, {"encoding":"jsonParsed",
                  "commitment":"confirmed", "maxSupportedTransactionVersion":0}])

def process_wallet(trader, state, record_buy, save_state):
    wallet = trader.wallet
    rows = recent_signatures(wallet, os.getenv("SMART_MONEY_RPC_SIGNATURE_LIMIT","10"))
    if not rows:
        return 0  # Empty RPC response does not establish an initial baseline.
    initialized = state.setdefault("rpc_initialized", {})
    history = state.setdefault("rpc_seen_signatures", {})
    seen_list = history.setdefault(wallet, [])
    seen = set(seen_list)
    signatures = [r.get("signature") for r in rows if r.get("signature")]
    if not initialized.get(wallet):
        seen_list.extend(sig for sig in signatures if sig not in seen)
        history[wallet] = seen_list[-2000:]
        initialized[wallet] = True
        save_state(state)
        print("  Public RPC baseline saved for %s (%d signatures); no history replay" %
              (trader.name, len(signatures)))
        return 0
    unseen = [r for r in rows if r.get("signature") and r["signature"] not in seen]
    if len(rows) >= max(1, min(20, int(os.getenv("SMART_MONEY_RPC_SIGNATURE_LIMIT","10")))) and len(unseen) == len(rows):
        print("  Possible public RPC history gap for %s: skipping stale page" % trader.name)
        seen_list.extend(r["signature"] for r in unseen)
        history[wallet] = seen_list[-2000:]
        save_state(state)
        return 0
    detected = 0
    for row in reversed(unseen):
        sig = row["signature"]
        if row.get("err") is None:
            tx = fetch_transaction(sig)
            if tx is None:
                raise RuntimeError("Solana transaction temporarily unavailable: %s" % sig[:12])
            buy = classify_swap(tx, wallet)
            if buy:
                record_buy(trader, {"signature":sig,
                          "timestamp":row.get("blockTime") or int(time.time()),
                          "type":"RPC_STABLECOIN_SWAP_HEURISTIC"}, buy, state)
                detected += 1
        seen_list.append(sig)
        history[wallet] = seen_list[-2000:]
        save_state(state)
    return detected
