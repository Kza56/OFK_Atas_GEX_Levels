# Skill: GEX Analyst ES — RTH Scalping Briefing for ES E-mini S&P500

## Instruction
Read the file C:\gex_agent\data\full_levels_ES.json and generate the briefing
according to the schema below.

## Key field mapping from JSON source

### Native ES levels (CME)
- gamma_flip       -> Gamma Flip ES
- vol_trigger      -> Vol Trigger ES
- call_wall        -> Call Wall ES
- put_wall         -> Put Wall ES
- risk_pivot       -> Risk Pivot ES (trapdoor)
- vanna_flip       -> Vanna Flip ES
- charm_magnet     -> Charm Magnet ES (0DTE end-of-session magnet)
- total_gex        -> total GEX (positive = pinning, negative = amplification)
- total_vex        -> total VEX (positive = IV drop = bullish pressure)
- gex_regime       -> 1 = positive, -1 or 0 = negative
- call_wall_gex    -> GEX value at Call Wall (CBOE SPY)
- put_wall_gex     -> GEX value at Put Wall (CBOE SPY, negative)

### CBOE metrics converted to ES
- max_pain_es      -> Max Pain in ES points
- expected_move_es -> Expected Move +/-pts ES
- range_bas_es     -> lower bound of expected range
- range_haut_es    -> upper bound of expected range
- pcr              -> Put/Call OI Ratio (>1 = put-heavy)
- top_oi_strikes   -> list of highest OI strikes (strike_es, call_oi, put_oi, total_oi)

## Permanent context
- Instrument    : ES E-mini S&P500 (CME, $50/point)
- Target session: RTH 09:30-16:00 ET
- Style         : scalping 5-30 minutes

## JSON response schema (strict - nothing else)

{
  "date": "YYYY-MM-DD",
  "spot_es": 0,
  "trade_date": "YYYYMMDD",

  "regime": {
    "gex_label": "positive" | "negative",
    "total_gex_B": 0.00,
    "total_vex_B": 0.00,
    "vol_implication": "short text - compressed or expansive vol and why"
  },

  "bias": {
    "direction": "bullish" | "bearish" | "neutral",
    "conviction": "low" | "moderate" | "high",
    "reason": "short text - justification based on GEX/VEX/PCR/positioning"
  },

  "levels": [
    {
      "type": "gamma_flip" | "vol_trigger" | "call_wall" | "put_wall" | "risk_pivot" | "vanna_flip" | "charm_magnet" | "max_pain" | "expected_move_high" | "expected_move_low",
      "es_price": 0,
      "distance_pct": 0.00,
      "dealer_behavior": "short text - mechanical dealer action at this level"
    }
  ],

  "rth_plan": {
    "buy_zone_es": 0,
    "sell_zone_es": 0,
    "bullish_invalidation_es": 0,
    "bearish_invalidation_es": 0
  },

  "top_oi_context": "short text - what the top 3 OI strikes imply for the session",

  "risk_alerts": [
    "short text - max 3 priority alerts"
  ],

  "one_liner": "short text - today actionable setup in one sentence"
}
