"""
generate_pdf_NQ.py — Génère le briefing NQ en PDF fond sombre
Usage  : py generate_pdf_NQ.py
Output : C:\gex_agent\data\briefing_YYYY-MM-DD.pdf
"""
import json
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)

BRIEFING_JSON = Path(r"C:\gex_agent\data\briefing_NQ.json")
OUTPUT_DIR    = Path(r"C:\gex_agent\data")

# Dark theme palette
BG          = colors.HexColor("#0d1117")
BG2         = colors.HexColor("#161b22")
BG3         = colors.HexColor("#1c2128")
C_WHITE     = colors.HexColor("#e6edf3")
C_BORDER    = colors.HexColor("#30363d")
C_GREEN     = colors.HexColor("#3fb950")
C_GREEN_BG  = colors.HexColor("#0d2e18")
C_RED       = colors.HexColor("#f85149")
C_RED_BG    = colors.HexColor("#2e0d0d")
C_ORANGE    = colors.HexColor("#d29922")
C_ORANGE_BG = colors.HexColor("#2e1f00")
C_YELLOW    = colors.HexColor("#e3b341")
C_BLUE      = colors.HexColor("#58a6ff")
C_PURPLE    = colors.HexColor("#bc8cff")
C_TEAL      = colors.HexColor("#39d353")

LEVEL_CFG = {
    "gamma_flip"        : ("Gamma Flip",   C_YELLOW),
    "hvl"               : ("HVL/Trigger",  C_ORANGE),
    "vol_trigger"       : ("Vol Trigger",  C_ORANGE),
    "call_wall"         : ("Call Wall",    C_GREEN),
    "put_wall"          : ("Put Wall",     C_RED),
    "risk_pivot"        : ("Risk Pivot",   colors.HexColor("#ff6b6b")),
    "vanna_flip"        : ("Vanna Flip",   C_PURPLE),
    "charm_magnet"      : ("Charm Magnet", C_BLUE),
    "max_pain"          : ("Max Pain",     C_WHITE),
    "expected_move_high": ("EM High",      C_TEAL),
    "expected_move_low" : ("EM Low",       C_TEAL),
}

def S(name, **kw):
    return ParagraphStyle(name, **kw)

def nq_val(d):
    if isinstance(d, dict):
        return (d.get("nq") or d.get("nq_approx") or
                d.get("prix_nq_approx") or d.get("prix_nq") or "?")
    return d or "?"

def build_pdf(briefing: dict) -> Path:
    date_str = briefing.get("date", "YYYY-MM-DD")
    output   = OUTPUT_DIR / f"briefing_NQ_{date_str}.pdf"

    W_PAGE, H_PAGE = A4
    M = 12*mm
    W = W_PAGE - 2*M

    doc = SimpleDocTemplate(str(output), pagesize=A4,
        topMargin=M, bottomMargin=M, leftMargin=M, rightMargin=M)

    story = []
    PAD  = 5
    LPAD = 10

    T_H1   = S("h1",  fontName="Helvetica-Bold",       fontSize=16,  textColor=C_WHITE, alignment=TA_CENTER, leading=20)
    T_SUB  = S("sub", fontName="Helvetica",             fontSize=8.5, textColor=C_WHITE, alignment=TA_CENTER, leading=11)
    T_SECT = S("sec", fontName="Helvetica-Bold",        fontSize=7.5, textColor=C_WHITE, leading=10, spaceBefore=2, letterSpacing=1.2)
    T_IMPL = S("im",  fontName="Helvetica",             fontSize=9,   textColor=C_WHITE, leading=13)
    T_BODY = S("bd",  fontName="Helvetica",             fontSize=9,   textColor=C_WHITE, leading=13)
    T_CMPT = S("cm",  fontName="Helvetica",             fontSize=8,   textColor=C_WHITE, leading=11)
    T_PLAN = S("pl",  fontName="Helvetica-Bold",        fontSize=9,   textColor=C_WHITE, leading=12)
    T_ALT  = S("al",  fontName="Helvetica",             fontSize=8.5, textColor=C_WHITE, leading=12)
    T_RES  = S("re",  fontName="Helvetica-BoldOblique", fontSize=9.5, textColor=C_WHITE, alignment=TA_CENTER, leading=14)
    T_FOOT = S("ft",  fontName="Helvetica",             fontSize=7,   textColor=C_WHITE, alignment=TA_CENTER)

    def rs(bg, border=True):
        st = [
            ("BACKGROUND",   (0,0),(-1,-1), bg),
            ("TOPPADDING",   (0,0),(-1,-1), PAD),
            ("BOTTOMPADDING",(0,0),(-1,-1), PAD),
            ("LEFTPADDING",  (0,0),(-1,-1), LPAD),
            ("RIGHTPADDING", (0,0),(-1,-1), LPAD),
        ]
        if border:
            st.append(("LINEBELOW",(0,0),(-1,-1),0.3,C_BORDER))
        return TableStyle(st)

    heure = (briefing.get("heure_generation") or "").replace(" ET","").strip()

    # Header
    hdr = Table([[Paragraph("GEX AGENT — NQ SCALPING BRIEFING", T_H1)]], colWidths=[W])
    hdr.setStyle(rs(BG2)); story.append(hdr)

    sub = Table([[Paragraph(
        f"RTH Session  .  {date_str}  .  {heure} ET  .  NQ E-mini Futures (CME)", T_SUB
    )]], colWidths=[W])
    sub.setStyle(rs(BG3)); story.append(sub)

    acc = Table([[""]], colWidths=[W])
    acc.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),C_BLUE),
                              ("TOPPADDING",(0,0),(-1,-1),1),("BOTTOMPADDING",(0,0),(-1,-1),1)]))
    story.append(acc); story.append(Spacer(1, 2*mm))

    # Regime
    r = briefing.get("regime", {})
    gex_label  = (r.get("gex_label") or r.get("label") or "?").upper()
    net_gex    = r.get("net_gex") or 0
    gex_B      = r.get("total_gex_B") or (f"{net_gex/1e9:.2f}" if net_gex else "?")
    impl       = r.get("vol_implication") or r.get("implication_vol") or r.get("implication") or ""
    regime_bg  = C_GREEN_BG if gex_label == "POSITIVE" else C_RED_BG
    regime_col = C_GREEN    if gex_label == "POSITIVE" else C_RED

    story.append(Paragraph("GEX REGIME", T_SECT))
    reg = Table([[
        Paragraph(f"<b>GEX REGIME : {gex_label}</b>",
            S("rl",fontName="Helvetica-Bold",fontSize=13,textColor=regime_col,leading=17)),
        Paragraph(f"<b>{gex_B}B</b>",
            S("rb",fontName="Helvetica-Bold",fontSize=13,textColor=regime_col,alignment=TA_RIGHT,leading=17)),
    ]], colWidths=[W*0.7, W*0.3])
    reg.setStyle(rs(regime_bg)); story.append(reg)
    impl_t = Table([[Paragraph(impl, T_IMPL)]], colWidths=[W])
    impl_t.setStyle(rs(BG2)); story.append(impl_t)
    story.append(Spacer(1, 2*mm))

    # Bias
    b = briefing.get("bias", briefing.get("biais", {}))
    direction  = (b.get("direction") or "?").upper()
    conviction = b.get("conviction") or "?"
    reason     = b.get("reason") or b.get("raison") or ""
    biais_bg   = {"BULLISH":C_GREEN_BG,"BEARISH":C_RED_BG}.get(direction,C_ORANGE_BG)
    biais_col  = {"BULLISH":C_GREEN,   "BEARISH":C_RED  }.get(direction,C_ORANGE)

    story.append(Paragraph("BIAS", T_SECT))
    bt = Table([[
        Paragraph(f"<b>BIAS : {direction}</b>",
            S("bl",fontName="Helvetica-Bold",fontSize=13,textColor=biais_col,leading=17)),
        Paragraph(f"conviction : <b>{conviction}</b>",
            S("bc",fontName="Helvetica",fontSize=9,textColor=biais_col,alignment=TA_RIGHT,leading=17)),
    ]], colWidths=[W*0.6, W*0.4])
    bt.setStyle(rs(biais_bg)); story.append(bt)
    rt = Table([[Paragraph(reason, T_BODY)]], colWidths=[W])
    rt.setStyle(rs(BG2)); story.append(rt)
    story.append(Spacer(1, 2*mm))

    # Key Levels
    story.append(Paragraph("KEY LEVELS", T_SECT))
    hdr_row = [
        Paragraph("<b>Type</b>",             S("nh1",fontName="Helvetica-Bold",fontSize=7.5,textColor=C_WHITE)),
        Paragraph("<b>NQ</b>",               S("nh2",fontName="Helvetica-Bold",fontSize=7.5,textColor=C_WHITE,alignment=TA_CENTER)),
        Paragraph("<b>Dist.</b>",            S("nh3",fontName="Helvetica-Bold",fontSize=7.5,textColor=C_WHITE,alignment=TA_CENTER)),
        Paragraph("<b>Dealer behavior</b>",  S("nh4",fontName="Helvetica-Bold",fontSize=7.5,textColor=C_WHITE)),
    ]
    rows = [hdr_row]

    levels_key = "levels" if "levels" in briefing else "niveaux"
    for i, n in enumerate(briefing.get(levels_key, [])):
        ntype = n.get("type", "?")
        prix  = (n.get("nq_price") or n.get("prix_nq_approx") or
                 n.get("prix_nq") or "?")
        dist  = n.get("distance_pct") or n.get("distance_spot_pct") or 0
        compt = (n.get("dealer_behavior") or n.get("comportement_dealers") or "")
        label, col = LEVEL_CFG.get(ntype, (ntype, C_WHITE))
        dist_str = f"{dist:+.2f}%" if isinstance(dist,(int,float)) else "?"
        dist_col = (C_GREEN if isinstance(dist,(int,float)) and dist > 0
                    else C_RED if isinstance(dist,(int,float)) and dist < 0
                    else C_WHITE)
        rows.append([
            Paragraph(f"<b>{label}</b>",
                S(f"lt{i}",fontName="Helvetica-Bold",fontSize=9,textColor=col,leading=12)),
            Paragraph(f"<b>{prix}</b>",
                S(f"nq{i}",fontName="Helvetica-Bold",fontSize=11,textColor=C_WHITE,alignment=TA_CENTER,leading=14)),
            Paragraph(dist_str,
                S(f"dd{i}",fontName="Helvetica-Bold",fontSize=9,textColor=dist_col,alignment=TA_CENTER,leading=12)),
            Paragraph(compt, T_CMPT),
        ])

    niv = Table(rows, colWidths=[W*0.14,W*0.10,W*0.09,W*0.67], repeatRows=1)
    ts = [
        ("BACKGROUND",   (0,0),(-1,0), BG),
        ("TOPPADDING",   (0,0),(-1,-1), 4),("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("LEFTPADDING",  (0,0),(-1,-1), 8),("RIGHTPADDING", (0,0),(-1,-1), 6),
        ("VALIGN",       (0,0),(-1,-1),"MIDDLE"),
        ("LINEBELOW",    (0,0),(-1,-1), 0.3, C_BORDER),
    ]
    for i in range(1, len(rows)):
        ts.append(("BACKGROUND",(0,i),(-1,i), BG2 if (i-1)%2==0 else BG3))
    niv.setStyle(TableStyle(ts)); story.append(niv)
    story.append(Spacer(1, 2*mm))

    # RTH Plan
    p = briefing.get("rth_plan", briefing.get("plan_rth", {}))
    za = nq_val(p.get("buy_zone_nq")             or p.get("zone_achat"))
    zv = nq_val(p.get("sell_zone_nq")            or p.get("zone_vente"))
    ih = nq_val(p.get("bullish_invalidation_nq") or p.get("invalidation_haussiere"))
    ib = nq_val(p.get("bearish_invalidation_nq") or p.get("invalidation_baissiere"))

    story.append(Paragraph("RTH PLAN", T_SECT))
    plan_items = [
        ("Buy zone",             za, C_GREEN),
        ("Sell zone",            zv, C_RED),
        ("Bullish invalidation", ih, C_ORANGE),
        ("Bearish invalidation", ib, C_ORANGE),
    ]
    plan_data = []
    for lbl, val, col in plan_items:
        plan_data.append([
            Paragraph(lbl, T_PLAN),
            Paragraph(f"<b>NQ {val}</b>",
                S(f"pv{lbl}",fontName="Helvetica-Bold",fontSize=10,textColor=col,alignment=TA_LEFT,leading=13)),
        ])
    plan_t = Table(plan_data, colWidths=[W*0.5, W*0.5])
    plan_t.setStyle(TableStyle([
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[BG2,BG3]),
        ("TOPPADDING",   (0,0),(-1,-1), 5),("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",  (0,0),(-1,-1), LPAD),("RIGHTPADDING",(0,0),(-1,-1), LPAD),
        ("LINEBELOW",    (0,0),(-1,-1), 0.3, C_BORDER),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
    ]))
    story.append(plan_t); story.append(Spacer(1, 2*mm))

    # Risk Alerts
    alerts_key = "risk_alerts" if "risk_alerts" in briefing else "alertes_risque"
    alertes = briefing.get(alerts_key, [])
    if alertes:
        story.append(Paragraph("RISK ALERTS", T_SECT))
        alert_data = []
        for i, a in enumerate(alertes, 1):
            alert_data.append([
                Paragraph(f"<b>{i}</b>",
                    S(f"ai{i}",fontName="Helvetica-Bold",fontSize=10,textColor=C_WHITE,alignment=TA_CENTER,leading=13)),
                Paragraph(a, T_ALT),
            ])
        at = Table(alert_data, colWidths=[W*0.05, W*0.95])
        at.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(0,-1),  C_RED_BG),
            ("ROWBACKGROUNDS",(1,0),(1,-1),  [BG2,BG3]),
            ("TOPPADDING",    (0,0),(-1,-1), 5),("BOTTOMPADDING",(0,0),(-1,-1), 5),
            ("LEFTPADDING",   (0,0),(-1,-1), 8),("RIGHTPADDING", (0,0),(-1,-1),10),
            ("LINEBELOW",     (0,0),(-1,-1), 0.3, C_BORDER),("VALIGN",(0,0),(-1,-1),"TOP"),
        ]))
        story.append(at); story.append(Spacer(1, 2*mm))

    # One-liner
    one_liner = briefing.get("one_liner") or briefing.get("resume_une_ligne") or ""
    if one_liner:
        res = Table([[Paragraph(f">>  {one_liner}", T_RES)]], colWidths=[W])
        res.setStyle(TableStyle([
            ("BACKGROUND",   (0,0),(-1,-1), C_BLUE),
            ("TOPPADDING",   (0,0),(-1,-1), 8),("BOTTOMPADDING",(0,0),(-1,-1), 8),
            ("LEFTPADDING",  (0,0),(-1,-1), 14),
        ]))
        story.append(res); story.append(Spacer(1, 2*mm))

    # Footer
    story.append(HRFlowable(width=W, thickness=0.3, color=C_BORDER))
    story.append(Paragraph(
        "GEX Agent NQ  |  CME NQ Options + CBOE QQQ  |  Usage personnel — pas un conseil financier",
        T_FOOT))


    # Auto-nettoyage : supprimer les anciens PDF NQ du même contrat
    for old_pdf in OUTPUT_DIR.glob("briefing_NQ_*.pdf"):
        if old_pdf != output:
            try:
                old_pdf.unlink()
            except Exception:
                pass

    def on_page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(BG)
        canvas.rect(0,0,W_PAGE,H_PAGE,fill=1,stroke=0)
        canvas.restoreState()

    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return output


if __name__ == "__main__":
    print("Loading briefing...")
    briefing = json.loads(BRIEFING_JSON.read_text(encoding="utf-8"))
    print("Generating PDF...")
    path = build_pdf(briefing)
    print(f"PDF generated: {path}")
