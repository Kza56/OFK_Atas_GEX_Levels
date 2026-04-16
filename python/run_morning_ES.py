"""
run_morning_ES.py — Main orchestrator for ES E-mini S&P500
Steps: CME ES -> CBOE SPY -> merge -> Claude briefing -> PDF

Usage: py run_morning_ES.py
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

GEX_JSON    = Path.home() / "AppData/Roaming/ATAS/data/ES_gex_latest.json"
LEVELS_JSON = Path("data/levels_ES.json")
FULL_JSON   = Path("data/full_levels_ES.json")
PROJECT_DIR = Path(r"C:\gex_agent")


def step(msg: str):
    print(f"\n{'─'*55}")
    print(f"  {msg}")
    print(f"{'─'*55}")


def run_cme():
    """Launch CME ES script (opens visible Chromium browser)."""
    step("STEP 1 — Fetch CME ES options")
    result = subprocess.run(
        [sys.executable, "cme_ES_browser_fetch.py"],
        cwd=r"C:\gex_agent"
    )
    if result.returncode != 0:
        raise RuntimeError("CME ES fetch failed")
    print("  CME ES -> ES_gex_latest.json OK")


def run_cboe():
    """Fetch CBOE SPY options chain (ES proxy)."""
    step("STEP 2 — Fetch CBOE SPY options")
    from data_fetcher_ES import build_levels_ES
    return build_levels_ES()


def merge_levels() -> dict:
    """Merge CME ES (native levels) + CBOE SPY (missing metrics)."""
    step("STEP 3 — Merge data sources")

    cme  = json.loads(GEX_JSON.read_text())   if GEX_JSON.exists()   else {}
    cboe = json.loads(LEVELS_JSON.read_text()) if LEVELS_JSON.exists() else {}

    es_spot  = cme.get("spot", 0)
    spy_spot = cboe.get("spot", 0)

    # SPY/ES ratio: SPY ~= ES / 10 (e.g. SPY 700 = ES 7000)
    # Use the real ratio computed from both spot prices
    ratio = es_spot / spy_spot if spy_spot > 0 else 10.0

    def spy_to_es(val):
        return round(val * ratio) if val else None

    full = {
        # Metadata
        "generated_at"       : datetime.now(timezone.utc).isoformat(),
        "trade_date"         : cme.get("trade_date"),
        "spot_es"            : es_spot,
        "spot_spy"           : spy_spot,
        "spy_es_ratio"       : round(ratio, 4),

        # Native ES levels (CME)
        "gamma_flip"         : cme.get("gamma_flip"),
        "vol_trigger"        : cme.get("vol_trigger"),
        "call_wall"          : cme.get("call_wall"),
        "put_wall"           : cme.get("put_wall"),
        "risk_pivot"         : cme.get("risk_pivot"),
        "vanna_flip"         : cme.get("vanna_flip"),
        "charm_magnet"       : cme.get("charm_magnet"),

        # Greeks exposures (CME)
        "total_gex"          : cme.get("total_gex"),
        "total_vex"          : cme.get("total_vex"),
        "total_cex"          : cme.get("total_cex"),
        "total_dex"          : cme.get("total_dex"),
        "gex_regime"         : cme.get("gex_regime"),
        "vex_regime"         : cme.get("vex_regime"),

        # Call/Put Wall GEX values (CBOE SPY)
        "call_wall_gex"      : cboe.get("call_wall_gex"),
        "put_wall_gex"       : cboe.get("put_wall_gex"),

        # CBOE metrics converted to ES
        "max_pain_spy"       : cboe.get("max_pain"),
        "max_pain_es"        : spy_to_es(cboe.get("max_pain")),
        "expected_move_spy"  : cboe.get("expected_move"),
        "expected_move_es"   : spy_to_es(cboe.get("expected_move")),
        "range_bas_spy"      : cboe.get("range_bas"),
        "range_haut_spy"     : cboe.get("range_haut"),
        "range_bas_es"       : spy_to_es(cboe.get("range_bas")),
        "range_haut_es"      : spy_to_es(cboe.get("range_haut")),
        "pcr"                : cboe.get("pcr"),

        # Top OI strikes SPY -> ES
        "top_oi_strikes"     : [
            {
                "strike_spy" : s["strike"],
                "strike_es"  : spy_to_es(s["strike"]),
                "call_oi"    : s["call_oi"],
                "put_oi"     : s["put_oi"],
                "total_oi"   : s["total_oi"],
            }
            for s in cboe.get("top_oi_strikes", [])
        ],
    }

    FULL_JSON.write_text(json.dumps(full, indent=2))

    # Console summary
    cw_gex = full.get("call_wall_gex")
    pw_gex = full.get("put_wall_gex")
    em_es  = full.get("expected_move_es")
    tops   = full.get("top_oi_strikes", [])

    print(f"  Spot ES          : {es_spot:.0f}")
    print(f"  Spot SPY         : {spy_spot:.2f}  (ratio {ratio:.2f})")
    print(f"  Gamma Flip ES    : {full['gamma_flip']}")
    print(f"  Vol Trigger ES   : {full['vol_trigger']}")
    if cw_gex is not None:
        print(f"  Call Wall ES     : {full['call_wall']}  (GEX {cw_gex:,.0f})")
    else:
        print(f"  Call Wall ES     : {full['call_wall']}")
    if pw_gex is not None:
        print(f"  Put Wall ES      : {full['put_wall']}  (GEX {pw_gex:,.0f})")
    else:
        print(f"  Put Wall ES      : {full['put_wall']}")
    print(f"  Risk Pivot ES    : {full['risk_pivot']}")
    print(f"  Vanna Flip ES    : {full['vanna_flip']}")
    print(f"  Charm Magnet ES  : {full['charm_magnet']}")
    print(f"  Max Pain ES      : {full['max_pain_es']}  (SPY {full['max_pain_spy']})")
    if em_es:
        print(f"  Expected Move ES : +/-{em_es} pts")
        print(f"  Range ES         : [{full['range_bas_es']} — {full['range_haut_es']}]")
    print(f"  PCR              : {full['pcr']}  ({'put-heavy' if (full['pcr'] or 0) > 1 else 'call-heavy'})")
    if len(tops) >= 3:
        print(f"  Top OI #1        : ES {tops[0]['strike_es']}  (OI {tops[0]['total_oi']:,.0f})")
        print(f"  Top OI #2        : ES {tops[1]['strike_es']}  (OI {tops[1]['total_oi']:,.0f})")
        print(f"  Top OI #3        : ES {tops[2]['strike_es']}  (OI {tops[2]['total_oi']:,.0f})")
    print(f"  -> data/full_levels_ES.json OK")
    return full


def run_agent():
    """Run Claude AI briefing for ES."""
    step("STEP 4 — Claude AI briefing ES")
    from claude_agent_ES import run_briefing_ES
    run_briefing_ES()


def run_pdf():
    """Generate ES briefing PDF."""
    step("STEP 5 — PDF generation")
    from generate_pdf_ES import build_pdf_ES
    briefing = json.loads(
        Path("data/briefing_ES.json").read_text(encoding="utf-8")
    )
    path = build_pdf_ES(briefing)
    print(f"  PDF -> {path}")


if __name__ == "__main__":
    print(f"\n{'='*55}")
    print(f"  GEX AGENT ES — Morning Run")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}")

    try:
        run_cme()
    except Exception as e:
        print(f"  WARNING: CME ES failed: {e}")
        print(f"  Continuing with existing JSON if available...")

    run_cboe()
    merge_levels()
    run_agent()
    run_pdf()
