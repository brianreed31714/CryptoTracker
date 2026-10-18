"""Credit-safe Solana public-RPC wallet observations (read-only).

Only classifies swaps with an incoming non-quote token and an outgoing
USDC/USDT balance delta owned by the watched wallet. Other activity is ignored.
No Helius requests, private keys, or transaction submissions.
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
    if not url.startswith("https://"):
        raise ValueError("Solana RPC must use HTTPS")
    delay = max(0.0, float(os.getenv("SMART_MONEY_RPC_MIN_INTERVAL_SECONDS", "1.5")))
    wait = delay - (time.monotonic() - _LAST_CALL)
    if wait > 0:
        time.sleep(wait)
    _LAST_CALL = time.monotonic()
    response = requests.post(url, json={"jsonrpc":"2.0","id":1,"method":method,"params":params}, timeout=15)
    response.raise_for_status()
    result = response.json()
    if result.get("error"):
        raise RuntimeError(f"Solana RPC {method}: {result['error']}")
    return result.get("result")

def recent_signatures(wallet, limit=10):
    limit = max(1, min(20, int(limit)))
    return rpc("getSignaturesForAddress", [wallet, {"limit":limit, "commitment":"confirmed"}]) or []

def _balances(items, wallet):
    result = {}
    for item in items or []:
        if item.get("owner") != wallet:
            continue
        mint = item.get("mint")
        amount = (item.get("uiTokenAmount") or {}).get("uiAmountString")
        try:
            quantity = float(amount)
        except (ValueError, TypeError):
            continue
        result[mint] = result.get(mint, 0.0) + quantity
    return result

def classify_swap(tx, wallet):
    if not tx or not tx.get("meta") or tx["meta"].get("err"):
        return None
    meta = tx["meta"]
    pre = _balances(meta.get("preTokenBalances"), wallet)
    post = _balances(meta.get("postTokenBalances"), wallet)
    deltas = {mint:post.get(mint,0)-pre.get(mint,0) for mint in pre.keys() | post.keys()}
    bought = [(mint, amount) for mint, amount in deltas.items() if mint not in QUOTES and amount > 0]
    spent = [(mint, -deltas.get(mint,0)) for mint in (USDC, USDT) if deltas.get(mint,0) < 0]
    if len(bought) != 1 or len(spent) != 1:
        return None  # Fail closed on ambiguous multi-token activity.
    mint, amount = bought[0]
    quote, cost = spent[0]
    if cost <= 0:
        return None
    return {"token_mint":mint,"token_amount_received":amount,
            "spend_asset":"USDC" if quote == USDC else "USDT",
            "spend_amount":cost,"estimated_spend_usd":cost}

def fetch_transaction(signature):
    return rpc("getTransaction", [signature, {"encoding":"jsonParsed","commitment":"confirmed",
                                             "maxSupportedTransactionVersion":0}])

def process_wallet(trader, state, record_buy, save_state):
    wallet = trader.wallet
    rows = recent_signatures(wallet, os.getenv("SMART_MONEY_RPC_SIGNATURE_LIMIT", "10"))
    seen = set(state["seen_signatures"])
    initialized = state["initialized"].get(wallet, False)
    if not initialized:
        state["seen_signatures"].extend(x["signature"] for x in rows if x.get("signature") not in seen)
        state["initialized"][wallet] = True
        save_state(state)
        return 0
    unseen = [x for x in rows if x.get("signature") not in seen and x.get("err") is None]
    if len(unseen) == len(rows) and len(rows) >= 10:
        # Potential history gap: do not infer continuity or backfill blindly.
        print(f"  RPC history gap possible for {trader.name}; skipping stale batch")
        state["seen_signatures"].extend(x["signature"] for x in rows if x.get("signature") not in seen)
        save_state(state)
        return 0
    detected = 0
    for item in reversed(unseen):
        sig = item["signature"]
        tx = fetch_transaction(sig)
        buy = classify_swap(tx, wallet)
        if buy:
            record_buy(trader, {"signature":sig,"timestamp":item.get("blockTime") or int(time.time()),
                                "type":"RPC_STABLECOIN_SWAP_HEURISTIC"}, buy, state)
            detected += 1
        state["seen_signatures"].append(sig)
    if unseen:
        save_state(state)
    return detected
