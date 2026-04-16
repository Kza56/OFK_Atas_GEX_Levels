"""
run_morning_NQ.py — Orchestrateur pipeline NQ E-mini
Étapes : CME NQ → CBOE QQQ → fusion → Claude briefing → PDF

Usage: py run_morning_NQ.py
"""
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

GEX_JSON    = Path.home() / "AppData/Roaming/ATAS/data/NQ_gex_latest.json"
LEVELS_JSON = Path("data/levels.json")
FULL_JSON   = Path("data/full_levels_NQ.json")
PROJECT_DIR = Path(r"C:\gex_agent")
CME_SCRIPT  = Path(r"C:\gex_agent\cme_NQ_browser_fetch.py")


def step(msg: str):
    print(f"\n{'─'*55}")
    print(f"  {msg}")
    print(f"{'─'*55}")


def run_cme():
    """Launch CME script (opens visible Chromium browser)."""
    step("STEP 1 — Fetch CME NQ options")
    result = subprocess.run(
        [sys.executable, "cme_NQ_browser_fetch.py"],
        cwd=r"C:\gex_agent"
    )
    if result.returncode != 0:
        raise RuntimeError("CME fetch failed")
    print("  CME → NQ_gex_latest.json ✓")


def run_cboe():
    """Fetch CBOE QQQ options chain."""
    step("STEP 2 — Fetch CBOE QQQ options")
    from data_fetcher_NQ import build_levels
    return build_levels()


def merge_levels() -> dict:
    """Merge CME (native NQ) + CBOE QQQ (missing metrics)."""
    step("STEP 3 — Merge data sources")

    cme  = json.loads(GEX_JSON.read_text())   if GEX_JSON.exists()   else {}
    cboe = json.loads(LEVELS_JSON.read_text()) if LEVELS_JSON.exists() else {}

    nq_spot  = cme.get("spot", 0)
    qqq_spot = cboe.get("spot", 0)
    ratio    = nq_spot / qqq_spot if qqq_spot > 0 else 20.0

    def qqq_to_nq(val):
        return round(val * ratio) if val else None

    full = {
        # Metadata
        "generated_at"       : datetime.now(timezone.utc).isoformat(),
        "trade_date"         : cme.get("trade_date"),
        "spot_nq"            : nq_spot,
        "spot_qqq"           : qqq_spot,
        "qqq_nq_ratio"       : round(ratio, 4),

        # Native NQ levels (CME)
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

        # Call/Put Wall GEX values (CBOE)
        "call_wall_gex"      : cboe.get("call_wall_gex"),
        "put_wall_gex"       : cboe.get("put_wall_gex"),

        # CBOE metrics converted to NQ
        "max_pain_qqq"       : cboe.get("max_pain"),
        "max_pain_nq"        : qqq_to_nq(cboe.get("max_pain")),
        "expected_move_qqq"  : cboe.get("expected_move"),
        "expected_move_nq"   : qqq_to_nq(cboe.get("expected_move")),
        "range_bas_qqq"      : cboe.get("range_bas"),
        "range_haut_qqq"     : cboe.get("range_haut"),
        "range_bas_nq"       : qqq_to_nq(cboe.get("range_bas")),
        "range_haut_nq"      : qqq_to_nq(cboe.get("range_haut")),
        "pcr"                : cboe.get("pcr"),

        # Top OI strikes QQQ → NQ
        "top_oi_strikes"     : [
            {
                "strike_qqq" : s["strike"],
                "strike_nq"  : qqq_to_nq(s["strike"]),
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
    em_nq  = full.get("expected_move_nq")
    tops   = full.get("top_oi_strikes", [])

    print(f"  Spot NQ          : {nq_spot:.0f}")
    print(f"  Spot QQQ         : {qqq_spot:.2f}  (ratio {ratio:.2f})")
    print(f"  Gamma Flip NQ    : {full['gamma_flip']}")
    print(f"  Vol Trigger NQ   : {full['vol_trigger']}")
    if cw_gex is not None:
        print(f"  Call Wall NQ     : {full['call_wall']}  (GEX {cw_gex:,.0f})")
    else:
        print(f"  Call Wall NQ     : {full['call_wall']}")
    if pw_gex is not None:
        print(f"  Put Wall NQ      : {full['put_wall']}  (GEX {pw_gex:,.0f})")
    else:
        print(f"  Put Wall NQ      : {full['put_wall']}")
    print(f"  Risk Pivot NQ    : {full['risk_pivot']}")
    print(f"  Vanna Flip NQ    : {full['vanna_flip']}")
    print(f"  Charm Magnet NQ  : {full['charm_magnet']}")
    print(f"  Max Pain NQ      : {full['max_pain_nq']}  (QQQ {full['max_pain_qqq']})")
    if em_nq:
        print(f"  Expected Move NQ : +/-{em_nq} pts")
        print(f"  Range NQ         : [{full['range_bas_nq']} - {full['range_haut_nq']}]")
    print(f"  PCR              : {full['pcr']}  ({'put-heavy' if (full['pcr'] or 0) > 1 else 'call-heavy'})")
    if len(tops) >= 3:
        print(f"  Top OI #1        : NQ {tops[0]['strike_nq']}  (OI {tops[0]['total_oi']:,.0f})")
        print(f"  Top OI #2        : NQ {tops[1]['strike_nq']}  (OI {tops[1]['total_oi']:,.0f})")
        print(f"  Top OI #3        : NQ {tops[2]['strike_nq']}  (OI {tops[2]['total_oi']:,.0f})")
    print(f"  -> data/full_levels_NQ.json OK")
    return full


def run_agent():
    """Run Claude AI briefing."""
    step("STEP 4 — Claude AI briefing")
    from claude_agent_NQ import run_briefing
    run_briefing()


def run_pdf():
    """Generate PDF briefing."""
    step("STEP 5 — PDF generation")
    from generate_pdf_NQ import build_pdf
    briefing = json.loads(
        Path("data/briefing_NQ.json").read_text(encoding="utf-8")
    )
    path = build_pdf(briefing)
    print(f"  PDF -> {path}")


if __name__ == "__main__":
    print(f"\n{'='*55}")
    print(f"  GEX AGENT NQ — Morning Run")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}")

    try:
        run_cme()
    except Exception as e:
        print(f"  WARNING: CME failed: {e}")
        print(f"  Continuing with existing JSON if available...")

    run_cboe()
    merge_levels()
    run_agent()
    run_pdf()
