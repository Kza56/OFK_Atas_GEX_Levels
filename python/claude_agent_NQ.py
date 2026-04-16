"""
claude_agent_NQ.py — Claude AI briefing agent NQ
Reads full_levels_NQ.json, sends to Claude Code CLI, generates JSON + displays summary

Usage: py claude_agent_NQ.py
"""
import subprocess
import json
from pathlib import Path

CLAUDE_CMD  = r"C:\Users\steph\AppData\Roaming\npm\claude.cmd"
PROJECT_DIR = r"C:\gex_agent"
FULL_JSON   = Path(r"C:\gex_agent\data\full_levels_NQ.json")


def run_briefing() -> dict:
    if not FULL_JSON.exists():
        raise FileNotFoundError(
            f"JSON not found: {FULL_JSON}\n"
            f"Run first: py run_morning_NQ.py"
        )

    prompt = (
        f"Read the file {FULL_JSON} "
        f"and apply the skill described in skills/gex_analyst_NQ.md. "
        f"Return only the briefing JSON, nothing else, "
        f"no markdown, no backticks, just raw JSON."
    )

    # Write prompt to temp file to avoid Windows escaping issues
    prompt_file = Path(PROJECT_DIR) / "data" / "_prompt_NQ.txt"
    prompt_file.write_text(prompt, encoding="utf-8")

    print("Claude Agent — generating NQ briefing...")

    result = subprocess.run(
        f'type "{prompt_file}" | "{CLAUDE_CMD}" -p',
        capture_output=True,
        cwd=PROJECT_DIR,
        shell=True
    )

    prompt_file.unlink(missing_ok=True)

    try:
        stdout = result.stdout.decode("utf-8")
        stderr = result.stderr.decode("utf-8")
    except Exception:
        stdout = result.stdout.decode("cp1252", errors="replace")
        stderr = result.stderr.decode("cp1252", errors="replace")

    if result.returncode != 0:
        raise RuntimeError(f"Claude Code error:\n{stderr}")

    # Save raw output for debug
    raw_file = Path(PROJECT_DIR) / "data" / "_briefing_NQ_raw.txt"
    raw_file.write_text(stdout, encoding="utf-8")

    raw = stdout.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    briefing = json.loads(raw)

    out = Path(PROJECT_DIR) / "data" / "briefing_NQ.json"
    out.write_text(json.dumps(briefing, indent=2, ensure_ascii=False), encoding="utf-8")

    # Helper functions — schema-agnostic
    def get_nq(d, *keys):
        if isinstance(d, dict):
            return (d.get("nq") or d.get("nq_approx") or
                    d.get("prix_nq_approx") or d.get("nq_price") or "?")
        for k in keys:
            if k in d:
                v = d[k]
                return v.get("nq") if isinstance(v, dict) else v
        return "?"

    def get_level_nq(n):
        return (n.get("nq_price") or n.get("prix_nq_approx") or
                n.get("prix_nq") or n.get("price_nq") or "?")

    def dist_fmt(n):
        d = n.get("distance_pts") or n.get("distance_spot_pct") or n.get("distance_pct")
        if d is None: return "?"
        if isinstance(d, float) and abs(d) < 50: return f"{d:+.2f}%"
        return f"{d:+.0f} pts"

    # Display summary
    r = briefing.get("regime",   briefing.get("regime",   {}))
    b = briefing.get("bias",     briefing.get("biais",    {}))
    p = briefing.get("rth_plan", briefing.get("plan_rth", {}))

    gex_label = (r.get("gex_label") or r.get("label") or "?").upper()
    net_gex   = r.get("net_gex") or r.get("total_gex") or 0
    gex_B     = r.get("total_gex_B") or (f"{net_gex/1e9:.2f}" if net_gex else "?")
    impl_vol  = r.get("vol_implication") or r.get("implication_vol") or r.get("implication") or ""

    direction  = (b.get("direction") or "?").upper()
    conviction = b.get("conviction") or "?"
    reason     = b.get("reason") or b.get("raison") or ""

    levels_key = "levels" if "levels" in briefing else "niveaux"

    print(f"\n{'='*62}")
    print(f"  NQ SCALPING BRIEFING  --  {briefing.get('date','?')}  {briefing.get('heure_generation','')}")
    print(f"{'='*62}")
    print(f"  GEX Regime : {gex_label}  ({gex_B}B)")
    print(f"  Vol        : {impl_vol}")
    print(f"{'─'*62}")
    print(f"  Bias       : {direction}  [{conviction}]")
    print(f"  Reason     : {reason}")
    print(f"{'─'*62}")
    print(f"  Key levels :")
    for n in briefing.get(levels_key, []):
        ntype = n.get("type") or "?"
        prix  = get_level_nq(n)
        d     = dist_fmt(n)
        print(f"    {ntype:22}  NQ {str(prix):>6}  ({d})")
    print(f"{'─'*62}")
    plan_buy  = get_nq(p.get("buy_zone_nq")              or p.get("zone_achat", p))
    plan_sell = get_nq(p.get("sell_zone_nq")             or p.get("zone_vente", p))
    plan_inh  = get_nq(p.get("bullish_invalidation_nq")  or p.get("invalidation_haussiere", p))
    plan_inb  = get_nq(p.get("bearish_invalidation_nq")  or p.get("invalidation_baissiere", p))
    print(f"  RTH Plan  :")
    print(f"    Buy zone       : NQ {plan_buy}")
    print(f"    Sell zone      : NQ {plan_sell}")
    print(f"    Bullish inval. : NQ {plan_inh}")
    print(f"    Bearish inval. : NQ {plan_inb}")
    print(f"{'─'*62}")
    alerts_key = "risk_alerts" if "risk_alerts" in briefing else "alertes_risque"
    print(f"  Alerts :")
    for a in briefing.get(alerts_key, []):
        print(f"    * {a}")
    print(f"{'─'*62}")
    one_liner = briefing.get("one_liner") or briefing.get("resume_une_ligne") or ""
    print(f"  >> {one_liner}")
    print(f"{'='*62}")
    print(f"  Briefing -> {out}")

    return briefing


if __name__ == "__main__":
    run_briefing()
