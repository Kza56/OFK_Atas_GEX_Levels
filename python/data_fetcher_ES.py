"""
data_fetcher_ES.py — CBOE SPY options chain fetcher (ES proxy)
Computes: Max Pain, Expected Move, PCR, GEX per strike, Top OI strikes
Converts SPY values to ES using the live SPY/ES ratio

Usage: py data_fetcher_ES.py
"""
import requests
import json
import re
import math
from datetime import datetime, timezone
from pathlib import Path

CBOE_URL = "https://cdn.cboe.com/api/global/delayed_quotes/options/SPY.json"
HEADERS  = {"User-Agent": "Mozilla/5.0"}

OCC_RE = re.compile(r'^(.+?)(\d{6})([CP])(\d{8})$')

def parse_symbol(symbol: str) -> dict:
    m = OCC_RE.match(symbol)
    if not m:
        return {}
    ticker, date_str, cp, strike_raw = m.groups()
    return {
        "ticker"  : ticker,
        "expiry"  : datetime.strptime(date_str, "%y%m%d").date(),
        "type"    : "call" if cp == "C" else "put",
        "strike"  : int(strike_raw) / 1000
    }

def bs_gamma(S, K, T, r, sigma):
    """Black-Scholes gamma — used when CBOE gamma is missing."""
    if T <= 0 or sigma <= 0:
        return 0.0
    try:
        d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))
        return math.exp(-0.5 * d1**2) / (S * sigma * math.sqrt(T) * math.sqrt(2 * math.pi))
    except Exception:
        return 0.0

def fetch_chain() -> dict:
    r = requests.get(CBOE_URL, headers=HEADERS, timeout=30)
    r.raise_for_status()
    raw   = r.json()["data"]
    spot  = float(raw["current_price"])
    today = datetime.now(timezone.utc).date()

    contracts = []
    for opt in raw["options"]:
        parsed = parse_symbol(opt.get("option", ""))
        if not parsed:
            continue
        oi     = float(opt.get("open_interest") or 0)
        iv     = float(opt.get("iv")            or 0)
        gamma  = float(opt.get("gamma")         or 0)
        strike = parsed["strike"]
        expiry = parsed["expiry"]
        dte    = (expiry - today).days

        if gamma == 0 and iv > 0 and dte > 0:
            T     = dte / 365
            gamma = bs_gamma(spot, strike, T, 0.05, iv)

        contracts.append({
            "symbol" : opt.get("option"),
            "type"   : parsed["type"],
            "strike" : strike,
            "expiry" : str(expiry),
            "dte"    : dte,
            "oi"     : oi,
            "volume" : float(opt.get("volume") or 0),
            "iv"     : iv,
            "gamma"  : gamma,
            "delta"  : float(opt.get("delta") or 0),
            "bid"    : float(opt.get("bid")   or 0),
            "ask"    : float(opt.get("ask")   or 0),
        })

    return {
        "spot"       : spot,
        "contracts"  : contracts,
        "fetched_at" : datetime.now(timezone.utc).isoformat()
    }

def calc_gex(contracts: list, spot: float) -> dict:
    """Compute Gamma Exposure: Gamma Flip, Call Wall, Put Wall, Net GEX."""
    by_strike = {}
    for c in contracts:
        k = c["strike"]
        if k not in by_strike:
            by_strike[k] = {"strike": k, "call_gex": 0.0, "put_gex": 0.0, "net_gex": 0.0}
        gex = c["gamma"] * c["oi"] * 100 * spot ** 2 * 0.01
        if c["type"] == "call":
            by_strike[k]["call_gex"] += gex
        else:
            by_strike[k]["put_gex"]  -= gex

    for k in by_strike:
        by_strike[k]["net_gex"] = by_strike[k]["call_gex"] + by_strike[k]["put_gex"]

    strikes = sorted(by_strike.values(), key=lambda x: x["strike"])

    # Gamma Flip
    gamma_flip = None
    cumulative = 0.0
    for s in strikes:
        prev       = cumulative
        cumulative += s["net_gex"]
        if prev != 0 and (prev < 0) != (cumulative < 0):
            gamma_flip = s["strike"]
            break

    call_wall_s = max(strikes, key=lambda x: x["call_gex"])
    put_wall_s  = min(strikes, key=lambda x: x["put_gex"])
    net_gex     = sum(s["net_gex"] for s in strikes)
    regime      = "positive" if net_gex >= 0 else "negative"

    return {
        "gamma_flip"    : gamma_flip,
        "call_wall"     : call_wall_s["strike"],
        "call_wall_gex" : round(call_wall_s["call_gex"], 0),
        "put_wall"      : put_wall_s["strike"],
        "put_wall_gex"  : round(put_wall_s["put_gex"], 0),
        "net_gex"       : round(net_gex, 0),
        "regime"        : regime,
    }

def calc_max_pain(contracts: list) -> float:
    strikes = sorted(set(c["strike"] for c in contracts))
    min_pain, max_pain_strike = float("inf"), strikes[0]
    for s in strikes:
        pain = 0.0
        for c in contracts:
            if c["type"] == "call" and s > c["strike"]:
                pain += (s - c["strike"]) * c["oi"] * 100
            elif c["type"] == "put" and s < c["strike"]:
                pain += (c["strike"] - s) * c["oi"] * 100
        if pain < min_pain:
            min_pain        = pain
            max_pain_strike = s
    return max_pain_strike

def calc_expected_move(spot: float, contracts: list) -> float:
    valid = [c for c in contracts if c["dte"] > 0 and c["iv"] > 0]
    if not valid:
        return 0.0
    nearest_expiry = min(valid, key=lambda x: x["dte"])["expiry"]
    dte = next(c["dte"] for c in valid if c["expiry"] == nearest_expiry)
    atm = [c for c in valid if c["expiry"] == nearest_expiry
           and abs(c["strike"] - spot) / spot < 0.02]
    if not atm:
        return 0.0
    avg_iv = sum(c["iv"] for c in atm) / len(atm)
    return round(spot * avg_iv * math.sqrt(dte / 365), 2)

def calc_pcr(contracts: list) -> float:
    call_oi = sum(c["oi"] for c in contracts if c["type"] == "call")
    put_oi  = sum(c["oi"] for c in contracts if c["type"] == "put")
    return round(put_oi / call_oi, 3) if call_oi > 0 else 0.0

def calc_top_strikes(contracts: list, n: int = 10) -> list:
    by_strike = {}
    for c in contracts:
        k = c["strike"]
        if k not in by_strike:
            by_strike[k] = {"strike": k, "call_oi": 0, "put_oi": 0, "total_oi": 0}
        if c["type"] == "call":
            by_strike[k]["call_oi"] += c["oi"]
        else:
            by_strike[k]["put_oi"]  += c["oi"]
        by_strike[k]["total_oi"] += c["oi"]
    return sorted(by_strike.values(), key=lambda x: x["total_oi"], reverse=True)[:n]

def build_levels_ES() -> dict:
    print("=" * 55)
    print("  GEX AGENT — CBOE SPY fetch (ES proxy)")
    print("=" * 55)

    chain     = fetch_chain()
    spot      = chain["spot"]
    contracts = chain["contracts"]
    print(f"Contracts fetched: {len(contracts)}")

    gex           = calc_gex(contracts, spot)
    max_pain      = calc_max_pain(contracts)
    expected_move = calc_expected_move(spot, contracts)
    pcr           = calc_pcr(contracts)
    top_strikes   = calc_top_strikes(contracts)

    levels = {
        "spot"           : spot,
        "fetched_at"     : chain["fetched_at"],
        "gamma_flip"     : gex["gamma_flip"],
        "call_wall"      : gex["call_wall"],
        "call_wall_gex"  : gex["call_wall_gex"],
        "put_wall"       : gex["put_wall"],
        "put_wall_gex"   : gex["put_wall_gex"],
        "net_gex"        : gex["net_gex"],
        "regime"         : gex["regime"],
        "max_pain"       : max_pain,
        "expected_move"  : expected_move,
        "range_bas"      : round(spot - expected_move, 2),
        "range_haut"     : round(spot + expected_move, 2),
        "pcr"            : pcr,
        "top_oi_strikes" : top_strikes,
    }

    Path("data/levels_ES.json").write_text(json.dumps(levels, indent=2))

    print(f"\n{'─'*55}")
    print(f"  Spot SPY      : ${spot:.2f}")
    print(f"  Regime        : {gex['regime'].upper()} GEX")
    print(f"  Net GEX       : ${gex['net_gex']:,.0f}")
    print(f"{'─'*55}")
    if gex["gamma_flip"]:
        print(f"  Gamma Flip    : ${gex['gamma_flip']:.2f}")
    print(f"  Call Wall     : ${gex['call_wall']:.2f}  (GEX {gex['call_wall_gex']:,.0f})")
    print(f"  Put Wall      : ${gex['put_wall']:.2f}  (GEX {gex['put_wall_gex']:,.0f})")
    print(f"{'─'*55}")
    print(f"  Max Pain      : ${max_pain:.2f}")
    print(f"  Expected Move : +/-${expected_move:.2f}")
    print(f"  Range         : [${levels['range_bas']} — ${levels['range_haut']}]")
    print(f"  PCR           : {pcr}  ({'put-heavy' if pcr > 1 else 'call-heavy'})")
    print(f"{'─'*55}")
    print(f"  Top OI #1     : ${top_strikes[0]['strike']} (OI {top_strikes[0]['total_oi']:,.0f})")
    print(f"  Top OI #2     : ${top_strikes[1]['strike']} (OI {top_strikes[1]['total_oi']:,.0f})")
    print(f"  Top OI #3     : ${top_strikes[2]['strike']} (OI {top_strikes[2]['total_oi']:,.0f})")
    print(f"{'─'*55}")
    print(f"  Saved -> data/levels_ES.json")
    print(f"{'='*55}")
    return levels

if __name__ == "__main__":
    build_levels_ES()
