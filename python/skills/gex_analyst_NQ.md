# Skill: GEX Analyst NQ — Briefing Scalping NQ E-mini

## Instruction
Read C:\gex_agent\data\full_levels.json and generate the briefing
according to the schema below.

## Key field mapping from JSON source

### Native NQ levels (CME)
- gamma_flip       → Gamma Flip NQ
- vol_trigger      → Vol Trigger NQ
- call_wall        → Call Wall NQ
- put_wall         → Put Wall NQ
- risk_pivot       → Risk Pivot NQ (trapdoor)
- vanna_flip       → Vanna Flip NQ
- charm_magnet     → Charm Magnet NQ (0DTE end-of-session magnet)
- total_gex        → total GEX (positive = pinning, negative = amplification)
- total_vex        → total VEX (positive = IV drop = bullish pressure)
- total_cex        → total CEX (charm time-driven flows)
- total_dex        → total DEX (directional)
- gex_regime       → 1 = positive, -1 or 0 = negative
- call_wall_gex    → GEX value at Call Wall (CBOE)
- put_wall_gex     → GEX value at Put Wall (CBOE, negative)

### CBOE metrics converted to NQ
- max_pain_nq      → Max Pain in NQ points
- expected_move_nq → Expected Move ±pts NQ
- range_bas_nq     → lower bound of expected range
- range_haut_nq    → upper bound of expected range
- pcr              → Put/Call OI Ratio (>1 = put-heavy)
- top_oi_strikes   → list of highest OI strikes (strike_nq, call_oi, put_oi, total_oi)

## JSON response schema (strict — nothing else)

{
  "date": "YYYY-MM-DD",
  "spot_nq": 0,
  "trade_date": "YYYYMMDD",

  "regime": {
    "gex_label": "positive" | "negative",
    "vex_label": "positive" | "negative",
    "total_gex_B": 0.00,
    "total_vex_B": 0.00,
    "vol_implication": "short text — compressed or expansive vol and why",
    "vex_implication": "short text — IV flow impact on intraday direction"
  },

  "levels": [
    {
      "type": "gamma_flip" | "vol_trigger" | "call_wall" | "put_wall" | "risk_pivot" | "vanna_flip" | "charm_magnet" | "max_pain" | "expected_move_high" | "expected_move_low",
      "nq_price": 0,
      "distance_pts": 0,
      "distance_pct": 0.00,
      "dealer_behavior": "short text — mechanical dealer action at this level"
    }
  ],

  "bias": {
    "direction": "bullish" | "bearish" | "neutral",
    "conviction": "low" | "moderate" | "high",
    "reason": "short text — justification based on GEX/VEX/PCR/positioning"
  },

  "rth_plan": {
    "buy_zone_nq": 0,
    "sell_zone_nq": 0,
    "bullish_invalidation_nq": 0,
    "bearish_invalidation_nq": 0,
    "critical_stop_nq": 0
  },

  "top_oi_context": "short text — what the top 3 OI strikes imply for the session",

  "risk_alerts": [
    "short text — max 3 priority alerts"
  ],

  "one_liner": "short text — today's actionable setup in one sentence"
}
