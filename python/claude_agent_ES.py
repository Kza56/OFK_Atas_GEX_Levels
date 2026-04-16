"""
claude_agent_ES.py — Claude AI briefing agent for ES E-mini S&P500
Reads full_levels_ES.json and generates the briefing via Claude Code CLI
"""
import subprocess
import json
from pathlib import Path

CLAUDE_CMD  = r"C:\Users\steph\AppData\Roaming\npm\claude.cmd"
PROJECT_DIR = r"C:\gex_agent"
FULL_JSON   = Path(r"C:\gex_agent\data\full_levels_ES.json")


def run_briefing_ES() -> dict:
    if not FULL_JSON.exists():
        raise FileNotFoundError(f"JSON not found: {FULL_JSON}")

    prompt = (
        f"Read the file {FULL_JSON} "
        f"and apply the skill described in skills/gex_analyst_ES.md. "
        f"Return only the briefing JSON, nothing else, "
        f"no markdown, no backticks, just raw JSON."
    )

    prompt_file = Path(PROJECT_DIR) / "data" / "_prompt_ES.txt"
    prompt_file.write_text(prompt, encoding="utf-8")

    print("Claude Agent ES — generating briefing...")

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

    raw_file = Path(PROJECT_DIR) / "data" / "_briefing_ES_raw.txt"
    raw_file.write_text(stdout, encoding="utf-8")

    raw = stdout.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    briefing = json.loads(raw)

    out = Path(PROJECT_DIR) / "data" / "briefing_ES.json"
    out.write_text(json.dumps(briefing, indent=2, ensure_ascii=False), encoding="utf-8")

    # Résumé console
    r = briefing.get("regime", {})
    b = briefing.get("biais",  {})

    gex_label = (r.get("gex_label") or r.get("label") or "?").upper()
    gex_B     = r.get("total_gex_B") or "?"
    direction = (b.get("direction") or "?").upper()
    conviction= b.get("conviction") or "?"
    one_liner = briefing.get("resume_une_ligne") or briefing.get("one_liner") or ""

    print(f"\n{'='*62}")
    print(f"  BRIEFING ES  —  {briefing.get('date','?')}")
    print(f"{'='*62}")
    print(f"  GEX Regime : {gex_label}  ({gex_B}B)")
    print(f"  Biais      : {direction}  [{conviction}]")
    print(f"  >> {one_liner}")
    print(f"{'='*62}")
    print(f"  Briefing -> {out}")

    return briefing


if __name__ == "__main__":
    run_briefing_ES()
