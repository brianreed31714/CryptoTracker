import os
import csv
import json
import time
import requests
from datetime import datetime

# =========================================================
# CRYPTO TRACKER - MARKET SCANNER V4
# Cross-scan momentum detection
# =========================================================

DEXSCREENER_BASE = "https://api.dexscreener.com"

DATA_DIR = "data"
SNAPSHOT_DIR = os.path.join(DATA_DIR, "snapshots")
UNIVERSE_FILE = os.path.join(DATA_DIR, "token_universe.json")

MIN_LIQUIDITY = 25_000
MIN_MARKET_CAP = 250_000
MAX_MARKET_CAP = 100_000_000
MIN_24H_VOLUME = 25_000

TOP_RESULTS = 20
MAX_TOKENS_PER_RUN = 150
REQUEST_DELAY = 0.08


# =========================================================
# SETUP
# =========================================================

def ensure_directories():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    if not os.path.exists(UNIVERSE_FILE):
        with open(UNIVERSE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2)


def load_universe():
    try:
        with open(UNIVERSE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_universe(universe):
    with open(UNIVERSE_FILE, "w", encoding="utf-8") as f:
        json.dump(universe, f, indent=2)


def safe_number(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def money(value):
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:.0f}"


def pct_change(current, previous):
    if previous <= 0:
        return 0.0

    return ((current - previous) / previous) * 100


# =========================================================
# DEX SCREENER
# =========================================================

def request_json(url):
    response = requests.get(
        url,
        timeout=20,
        headers={"User-Agent": "CryptoTracker/4.0"}
    )
    response.raise_for_status()
    return response.json()


def get_discovery_feed(endpoint):
    data = request_json(
        f"{DEXSCREENER_BASE}/{endpoint}"
    )

    results = []

    for item in data:
        if item.get("chainId") == "solana":
            address = item.get("tokenAddress")
            if address:
                results.append(address)

    return results


def discover_tokens():
    discovered = set()

    sources = [
        ("latest profiles", "token-profiles/latest/v1"),
        ("latest boosted", "token-boosts/latest/v1"),
        ("top boosted", "token-boosts/top/v1"),
    ]

    for name, endpoint in sources:
        try:
            addresses = get_discovery_feed(endpoint)
            discovered.update(addresses)

            print(
                f"{name:<20}: "
                f"{len(addresses)} Solana tokens"
            )

        except Exception as e:
            print(f"Warning - {name} failed: {e}")

    return list(discovered)


def get_token_pairs(address):
    return request_json(
        f"{DEXSCREENER_BASE}/token-pairs/v1/"
        f"solana/{address}"
    )


def choose_best_pair(pairs):
    if not pairs:
        return None

    pairs = [
        p for p in pairs
        if p.get("chainId") == "solana"
    ]

    if not pairs:
        return None

    return max(
        pairs,
        key=lambda p: safe_number(
            p.get("liquidity", {}).get("usd")
        )
    )


# =========================================================
# METRICS
# =========================================================

def calculate_metrics(pair):
    pc = pair.get("priceChange", {})
    vol = pair.get("volume", {})
    tx = pair.get("txns", {})

    price_5m = safe_number(pc.get("m5"))
    price_1h = safe_number(pc.get("h1"))
    price_6h = safe_number(pc.get("h6"))
    price_24h = safe_number(pc.get("h24"))

    volume_5m = safe_number(vol.get("m5"))
    volume_1h = safe_number(vol.get("h1"))
    volume_6h = safe_number(vol.get("h6"))
    volume_24h = safe_number(vol.get("h24"))

    buys_5m = safe_number(
        tx.get("m5", {}).get("buys")
    )
    sells_5m = safe_number(
        tx.get("m5", {}).get("sells")
    )

    buys_1h = safe_number(
        tx.get("h1", {}).get("buys")
    )
    sells_1h = safe_number(
        tx.get("h1", {}).get("sells")
    )

    ratio_5m = buys_5m / max(sells_5m, 1)
    ratio_1h = buys_1h / max(sells_1h, 1)

    avg_5m = volume_1h / 12 if volume_1h else 0

    volume_acceleration = (
        volume_5m / avg_5m
        if avg_5m > 0
        else 0
    )

    return {
        "price_5m": price_5m,
        "price_1h": price_1h,
        "price_6h": price_6h,
        "price_24h": price_24h,
        "volume_5m": volume_5m,
        "volume_1h": volume_1h,
        "volume_6h": volume_6h,
        "volume_24h": volume_24h,
        "buys_5m": buys_5m,
        "sells_5m": sells_5m,
        "buys_1h": buys_1h,
        "sells_1h": sells_1h,
        "buy_sell_ratio_5m": ratio_5m,
        "buy_sell_ratio_1h": ratio_1h,
        "volume_acceleration": volume_acceleration,
    }


# =========================================================
# SCORE
# =========================================================

def calculate_score(m):
    score = 0

    p5 = m["price_5m"]
    p1 = m["price_1h"]
    v5 = m["volume_5m"]
    ratio = m["buy_sell_ratio_5m"]
    accel = m["volume_acceleration"]

    # Price momentum
    if p5 > 1:
        score += 5
    if p5 > 3:
        score += 10
    if p5 > 5:
        score += 15
    if p5 > 10:
        score += 10

    if p1 > 5:
        score += 5
    if p1 > 10:
        score += 10
    if p1 > 20:
        score += 10

    # Alignment
    if p5 > 1 and p1 > 3:
        score += 10

    if p5 > 3 and p1 > 8:
        score += 10

    # Negative trend penalties
    if p1 < -5:
        score -= 10

    if p1 < -10:
        score -= 15

    if p1 < -20:
        score -= 20

    if p5 > 0 and p1 < -10:
        score -= 10

    # Buy pressure
    if ratio > 1.25:
        score += 5

    if ratio > 1.75:
        score += 10

    if ratio > 2.5:
        score += 15

    if ratio > 4:
        score += 10

    # Volume
    if v5 > 2_500:
        score += 5

    if v5 > 10_000:
        score += 10

    if v5 > 25_000:
        score += 15

    if v5 > 50_000:
        score += 10

    # Volume acceleration
    if accel > 1.25:
        score += 5

    if accel > 1.75:
        score += 10

    if accel > 2.5:
        score += 15

    if accel > 4:
        score += 10

    # Weak-volume penalties
    if accel < 0.75:
        score -= 10

    if accel < 0.40:
        score -= 10

    # Strong combined signal
    if (
        p5 > 2
        and p1 > 5
        and ratio > 1.5
        and accel > 1.5
    ):
        score += 20

    return max(score, 0)


# =========================================================
# FILTERS
# =========================================================

def passes_filters(pair, m):
    liquidity = safe_number(
        pair.get("liquidity", {}).get("usd")
    )

    market_cap = safe_number(pair.get("marketCap"))
    fdv = safe_number(pair.get("fdv"))

    valuation = market_cap if market_cap else fdv

    if liquidity < MIN_LIQUIDITY:
        return False

    if valuation < MIN_MARKET_CAP:
        return False

    if valuation > MAX_MARKET_CAP:
        return False

    if m["volume_24h"] < MIN_24H_VOLUME:
        return False

    return True


# =========================================================
# PREVIOUS SNAPSHOTS
# =========================================================

def get_snapshot_file():
    date_string = datetime.now().strftime("%Y-%m-%d")

    return os.path.join(
        SNAPSHOT_DIR,
        f"{date_string}.csv"
    )


def load_previous_snapshots():
    """
    Return the most recent saved observation for
    each token from today's CSV.
    """

    filename = get_snapshot_file()

    previous = {}

    if not os.path.exists(filename):
        return previous

    try:
        with open(
            filename,
            "r",
            newline="",
            encoding="utf-8"
        ) as f:

            reader = csv.DictReader(f)

            for row in reader:
                address = row.get("token_address")

                if address:
                    previous[address] = row

    except Exception as e:
        print(
            f"Warning reading previous snapshots: {e}"
        )

    return previous


def calculate_cross_scan(
    current,
    previous
):
    if not previous:
        return {
            "elapsed_minutes": 0,
            "score_delta": 0,
            "price_delta_pct": 0,
            "volume_delta_pct": 0,
            "liquidity_delta_pct": 0,
        }

    try:
        current_time = datetime.fromisoformat(
            current["timestamp"]
        )

        previous_time = datetime.fromisoformat(
            previous["timestamp"]
        )

        elapsed = (
            current_time - previous_time
        ).total_seconds() / 60

    except Exception:
        elapsed = 0

    score_delta = (
        safe_number(current["momentum_score"])
        - safe_number(previous["momentum_score"])
    )

    price_delta = pct_change(
        safe_number(current["price_usd"]),
        safe_number(previous["price_usd"])
    )

    volume_delta = pct_change(
        safe_number(current["volume_5m"]),
        safe_number(previous["volume_5m"])
    )

    liquidity_delta = pct_change(
        safe_number(current["liquidity"]),
        safe_number(previous["liquidity"])
    )

    return {
        "elapsed_minutes": round(elapsed, 2),
        "score_delta": round(score_delta, 2),
        "price_delta_pct": round(price_delta, 2),
        "volume_delta_pct": round(volume_delta, 2),
        "liquidity_delta_pct": round(
            liquidity_delta,
            2
        ),
    }


# =========================================================
# STATE CLASSIFICATION
# =========================================================

def classify_state(row):
    score = row["momentum_score"]
    delta = row["score_delta"]

    p5 = row["price_5m"]
    p1 = row["price_1h"]

    accel = row["volume_acceleration"]
    ratio = row["buy_sell_ratio_5m"]

    # Strong acceleration from one scan to next
    if (
        score >= 55
        and delta >= 15
        and p5 > 1
        and accel > 1.5
    ):
        return "SURGING"

    # Score is rapidly deteriorating
    if delta <= -15:
        return "FADING"

    # Bounce against a negative hourly trend
    if p5 > 0 and p1 < -5:
        return "BOUNCE"

    # Strong existing momentum
    if (
        score >= 70
        and p5 > 2
        and p1 > 5
        and accel > 1.5
        and ratio > 1.5
    ):
        return "STRONG"

    # Developing momentum
    if (
        score >= 40
        and p5 > 0
        and p1 > 0
    ):
        return "BUILDING"

    # Decent score, but not accelerating
    if score >= 40:
        return "STEADY"

    return "NEUTRAL"


# =========================================================
# CSV
# =========================================================

FIELDNAMES = [
    "timestamp",
    "symbol",
    "name",
    "token_address",
    "pair_address",
    "dex",
    "price_usd",
    "market_cap",
    "liquidity",
    "volume_5m",
    "volume_1h",
    "volume_6h",
    "volume_24h",
    "price_5m",
    "price_1h",
    "price_6h",
    "price_24h",
    "buys_5m",
    "sells_5m",
    "buys_1h",
    "sells_1h",
    "buy_sell_ratio_5m",
    "buy_sell_ratio_1h",
    "volume_acceleration",
    "momentum_score",
    "elapsed_minutes",
    "score_delta",
    "price_delta_pct",
    "volume_delta_pct",
    "liquidity_delta_pct",
    "momentum_state",
    "pair_url",
]


def append_snapshot(row):
    filename = get_snapshot_file()

    file_exists = os.path.exists(filename)

    with open(
        filename,
        "a",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=FIELDNAMES
        )

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


# =========================================================
# SCAN
# =========================================================

def scan_market():
    ensure_directories()

    print()
    print("=" * 125)
    print(
        "CRYPTO TRACKER - SOLANA MOMENTUM SCANNER V4 "
        + datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )
    print("=" * 125)
    print()

    # Load previous observations BEFORE writing
    # anything from this scan.
    previous_snapshots = load_previous_snapshots()

    universe = load_universe()

    discovered = discover_tokens()

    now_text = datetime.now().isoformat()

    new_count = 0

    for address in discovered:

        if address not in universe:
            universe[address] = {
                "first_seen": now_text,
                "last_seen": now_text,
            }

            new_count += 1

        else:
            universe[address]["last_seen"] = now_text

    save_universe(universe)

    print()
    print(
        f"New tokens added to universe: {new_count}"
    )

    print(
        f"Total token universe: {len(universe)}"
    )

    print(
        f"Previous token observations available: "
        f"{len(previous_snapshots)}"
    )

    print()

    discovered_set = set(discovered)

    addresses = list(universe.keys())

    addresses.sort(
        key=lambda x: (
            x not in discovered_set,
            universe[x].get("last_seen", "")
        )
    )

    addresses = addresses[:MAX_TOKENS_PER_RUN]

    print(
        f"Tokens being analyzed this run: "
        f"{len(addresses)}"
    )

    candidates = []

    analyzed = 0
    qualified = 0

    for token_address in addresses:

        try:
            pairs = get_token_pairs(token_address)

            pair = choose_best_pair(pairs)

            if not pair:
                continue

            analyzed += 1

            metrics = calculate_metrics(pair)

            if not passes_filters(pair, metrics):
                continue

            qualified += 1

            base = pair.get("baseToken", {})

            actual_address = base.get(
                "address",
                token_address
            )

            market_cap = safe_number(
                pair.get("marketCap")
            )

            fdv = safe_number(
                pair.get("fdv")
            )

            valuation = (
                market_cap
                if market_cap > 0
                else fdv
            )

            score = calculate_score(metrics)

            row = {
                "timestamp": datetime.now().isoformat(),

                "symbol": base.get("symbol", "?"),
                "name": base.get("name", "?"),

                "token_address": actual_address,

                "pair_address": pair.get(
                    "pairAddress",
                    ""
                ),

                "dex": pair.get("dexId", "?"),

                "price_usd": safe_number(
                    pair.get("priceUsd")
                ),

                "market_cap": valuation,

                "liquidity": safe_number(
                    pair.get(
                        "liquidity",
                        {}
                    ).get("usd")
                ),

                "volume_5m": metrics["volume_5m"],
                "volume_1h": metrics["volume_1h"],
                "volume_6h": metrics["volume_6h"],
                "volume_24h": metrics["volume_24h"],

                "price_5m": metrics["price_5m"],
                "price_1h": metrics["price_1h"],
                "price_6h": metrics["price_6h"],
                "price_24h": metrics["price_24h"],

                "buys_5m": metrics["buys_5m"],
                "sells_5m": metrics["sells_5m"],

                "buys_1h": metrics["buys_1h"],
                "sells_1h": metrics["sells_1h"],

                "buy_sell_ratio_5m": round(
                    metrics["buy_sell_ratio_5m"],
                    4
                ),

                "buy_sell_ratio_1h": round(
                    metrics["buy_sell_ratio_1h"],
                    4
                ),

                "volume_acceleration": round(
                    metrics["volume_acceleration"],
                    4
                ),

                "momentum_score": score,

                "pair_url": pair.get("url", ""),
            }

            previous = previous_snapshots.get(
                actual_address
            )

            cross = calculate_cross_scan(
                row,
                previous
            )

            row.update(cross)

            row["momentum_state"] = (
                classify_state(row)
            )

            append_snapshot(row)

            candidates.append(row)

        except Exception as e:
            print(
                f"Error scanning "
                f"{token_address[:8]}... {e}"
            )

        time.sleep(REQUEST_DELAY)

    print()
    print(f"Pairs analyzed: {analyzed}")
    print(f"Passed base filters: {qualified}")

    candidates.sort(
        key=lambda x: (
            x["momentum_state"] == "SURGING",
            x["score_delta"],
            x["momentum_score"],
        ),
        reverse=True
    )

    show_candidates(
        candidates[:TOP_RESULTS]
    )


# =========================================================
# DISPLAY
# =========================================================

def show_candidates(candidates):

    print()
    print("=" * 125)
    print("TOP MOMENTUM CANDIDATES")
    print("=" * 125)
    print()

    if not candidates:
        print(
            "No tokens passed the current filters."
        )
        return

    header = (
        f"{'TOKEN':<12}"
        f"{'SCORE':>7}"
        f"{'DELTA':>8}"
        f"{'STATE':>11}"
        f"{'MCAP':>11}"
        f"{'5M VOL':>11}"
        f"{'5M %':>8}"
        f"{'B/S':>8}"
        f"{'VOL X':>8}"
        f"{'VOL DELTA':>11}"
    )

    print(header)
    print("-" * len(header))

    for c in candidates:

        print(
            f"{c['symbol'][:11]:<12}"
            f"{c['momentum_score']:>7.0f}"
            f"{c['score_delta']:>+8.0f}"
            f"{c['momentum_state']:>11}"
            f"{money(c['market_cap']):>11}"
            f"{money(c['volume_5m']):>11}"
            f"{c['price_5m']:>7.1f}%"
            f"{c['buy_sell_ratio_5m']:>8.2f}"
            f"{c['volume_acceleration']:>7.2f}x"
            f"{c['volume_delta_pct']:>+10.1f}%"
        )

    print()
    print("TOP CANDIDATE")
    print("-" * 65)

    top = candidates[0]

    print(
        f"Token: {top['name']} "
        f"({top['symbol']})"
    )

    print(
        f"State: {top['momentum_state']}"
    )

    print(
        f"Score: {top['momentum_score']}"
    )

    print(
        f"Score change: "
        f"{top['score_delta']:+.0f}"
    )

    print(
        f"Minutes since previous observation: "
        f"{top['elapsed_minutes']:.1f}"
    )

    print(
        f"Price since previous scan: "
        f"{top['price_delta_pct']:+.2f}%"
    )

    print(
        f"5m volume since previous scan: "
        f"{top['volume_delta_pct']:+.2f}%"
    )

    print(
        f"Liquidity since previous scan: "
        f"{top['liquidity_delta_pct']:+.2f}%"
    )

    print(
        f"Market cap: "
        f"{money(top['market_cap'])}"
    )

    print(
        f"Liquidity: "
        f"{money(top['liquidity'])}"
    )

    print(
        f"5m price: "
        f"{top['price_5m']:+.2f}%"
    )

    print(
        f"1h price: "
        f"{top['price_1h']:+.2f}%"
    )

    print(
        f"5m volume: "
        f"{money(top['volume_5m'])}"
    )

    print(
        f"Buy/Sell ratio: "
        f"{top['buy_sell_ratio_5m']:.2f}"
    )

    print(
        f"Volume acceleration: "
        f"{top['volume_acceleration']:.2f}x"
    )

    print(
        f"DEX: {top['dex']}"
    )

    print(
        f"DEX Screener: "
        f"{top['pair_url']}"
    )

    print()
    print(
        f"Snapshot saved to: "
        f"{get_snapshot_file()}"
    )


if __name__ == "__main__":
    scan_market()