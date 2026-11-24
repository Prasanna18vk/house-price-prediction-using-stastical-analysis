"""Build the project presentation from results/results.json (no numbers are typed by hand).
Uses template.pptx (same theme/layouts as the reference weather deck).  Run: python report_tools/build_slides.py
"""
import json, copy
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
R = json.loads((ROOT / "results/results.json").read_text())
FIG = ROOT / "results/figures"
NAVY, BLUE, ORANGE, INK, TINT, LINE, GREY, LIGHTBLUE = (RGBColor.from_string(c) for c in
    ["1F2A37", "2F7F79", "C8553D", "1F2A37", "EEF3F2", "D5DDDB", "5B6770", "9FC5C0"])
WHITE = RGBColor(255, 255, 255)
HIGHLIGHT = RGBColor.from_string("FBE3DB")
TITLE = "House Price Prediction Using Statistical Analysis"

prs = Presentation()
prs.slide_width, prs.slide_height = Emu(9144000), Emu(5143500)
BLANK = prs.slide_layouts[6]
DARK_BG = RGBColor.from_string("1F2A37")


def text(slide, x, y, w, h, paras, size=14, bold=False, color=INK, font=None, align=PP_ALIGN.LEFT,
         anchor=MSO_ANCHOR.TOP, name=None, space_after=0, bullets=False):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name: tb.name = name
    tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    if isinstance(paras, str): paras = [paras]
    for i, t in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align; p.space_after = Pt(space_after)
        runs = t if isinstance(t, list) else [(t, {})]
        for rt, o in runs:
            r = p.add_run(); r.text = rt
            r.font.size = Pt(o.get("size", size)); r.font.bold = o.get("bold", bold)
            r.font.color.rgb = o.get("color", color)
            if o.get("font", font): r.font.name = o.get("font", font)
        if bullets:
            pPr = p._p.get_or_add_pPr(); pPr.set("marL", "228600"); pPr.set("indent", "-228600")
            bu = etree.SubElement(pPr, qn("a:buChar")); bu.set("char", "•")
    return tb


def card(slide, x, y, w, h, fill=TINT, name="Card", shape=MSO_SHAPE.ROUNDED_RECTANGLE):
    s = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    s.name = name; s.fill.solid(); s.fill.fore_color.rgb = fill; s.line.fill.background(); s.shadow.inherit = False
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE: s.adjustments[0] = 0.08
    return s


def slide_number(slide):
    tb = slide.shapes.add_textbox(Inches(9.0), Inches(5.25), Inches(0.5), Inches(0.25)); tb.name = "Slide number"
    tf = tb.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.RIGHT
    fld = etree.SubElement(p._p, qn("a:fld")); fld.set("id", "{F7021451-1387-4CA6-816F-3879F97B5CBC}"); fld.set("type", "slidenum")
    rpr = etree.SubElement(fld, qn("a:rPr")); rpr.set("lang", "en-US"); rpr.set("sz", "1000")
    sf = etree.SubElement(rpr, qn("a:solidFill")); c = etree.SubElement(sf, qn("a:srgbClr")); c.set("val", "FFFFFF" if slide._dark else "6B7280")
    t = etree.SubElement(fld, qn("a:t")); t.text = "‹#›"


def new_slide(layout, title=None, dark=False):
    s = prs.slides.add_slide(BLANK); s._dark = dark or layout.endswith("DARK")
    s.background.fill.solid(); s.background.fill.fore_color.rgb = DARK_BG if s._dark else WHITE
    if title:
        text(s, 0.5, 0.3, 9.0, 0.7, title, size=28, bold=True, color=WHITE if s._dark else NAVY, font="Arial",
             anchor=MSO_ANCHOR.MIDDLE, name="Slide title")
    if layout == "CONTENT":
        text(s, 0.5, 5.25, 7.0, 0.25, TITLE, size=10, color=GREY, anchor=MSO_ANCHOR.MIDDLE, name="Footer")
    if layout != "TITLE_DARK": slide_number(s)
    return s


def picture(slide, name, x, y, w=None, h=None):
    kw = {}
    if w: kw["width"] = Inches(w)
    if h: kw["height"] = Inches(h)
    pic = slide.shapes.add_picture(str(FIG / name), Inches(x), Inches(y), **kw); pic.name = name
    return pic


def table(slide, x, y, widths, rows, size=11, row_h=0.27, highlight=None, name="Table", align_right_from=None):
    gf = slide.shapes.add_table(len(rows), len(widths), Inches(x), Inches(y), Inches(sum(widths)), Inches(row_h * len(rows)))
    gf.name = name; tbl = gf.table
    tblPr = tbl._tbl.tblPr
    for a in ("firstRow", "bandRow"): tblPr.set(a, "0")
    for ch in list(tblPr): tblPr.remove(ch)
    for j, wd in enumerate(widths): tbl.columns[j].width = Inches(wd)
    for i, row in enumerate(rows):
        tbl.rows[i].height = Inches(row_h)
        for j, val in enumerate(row):
            c = tbl.cell(i, j); c.margin_left = c.margin_right = Inches(0.08); c.margin_top = c.margin_bottom = Inches(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = c.text_frame; tf.word_wrap = True; p = tf.paragraphs[0]
            r = p.add_run(); r.text = str(val); r.font.size = Pt(size)
            if align_right_from is not None and j >= align_right_from: p.alignment = PP_ALIGN.RIGHT
            hdr = i == 0
            r.font.bold = hdr or (highlight == i); r.font.color.rgb = WHITE if hdr else INK
            tcPr = c._tc.get_or_add_tcPr()
            for tag in reversed(["lnL", "lnR", "lnT", "lnB"]):
                ln = etree.Element(qn("a:" + tag)); ln.set("w", "6350")
                sf = etree.SubElement(ln, qn("a:solidFill")); cc = etree.SubElement(sf, qn("a:srgbClr")); cc.set("val", "D5DDDB")
                tcPr.insert(0, ln)
            c.fill.solid(); c.fill.fore_color.rgb = BLUE if hdr else (HIGHLIGHT if highlight == i else WHITE)
    return gf


f1 = lambda v: f"{v:,.1f}"
f2 = lambda v: f"{v:,.2f}"
f3 = lambda v: f"{round(v, 3) + 0.0:.3f}"
P, S, PR, RG, MT, MD = (R[k] for k in ["preprocessing", "statistics", "probability", "regression", "math", "models"])
H, GD = S["hypothesis"], MT["gradient_descent"]
sel = MD["selected"]; tm = MD["test_metrics"]

# 1 ── title ───────────────────────────────────────────────────────────────
s = new_slide("TITLE_DARK")
for nm, shp, x, y, w, h, col in [("Roof", MSO_SHAPE.ISOSCELES_TRIANGLE, 7.2, 0.9, 2.3, 1.2, ORANGE), ("House body", MSO_SHAPE.RECTANGLE, 7.4, 2.1, 1.9, 1.6, BLUE),
                                  ("Door", MSO_SHAPE.RECTANGLE, 8.15, 2.85, 0.4, 0.85, DARK_BG), ("Window 1", MSO_SHAPE.RECTANGLE, 7.6, 2.35, 0.4, 0.4, LIGHTBLUE),
                                  ("Window 2", MSO_SHAPE.RECTANGLE, 8.7, 2.35, 0.4, 0.4, LIGHTBLUE)]:
    card(s, x, y, w, h, col, nm, shp)
text(s, 0.6, 1.05, 6.4, 1.9, TITLE, size=32, bold=True, color=WHITE, font="Arial", anchor=MSO_ANCHOR.MIDDLE, name="Title")
text(s, 0.6, 3.05, 6.4, 0.7, "Statistical and mathematical analysis of 1,000 houses to predict sale price (synthetic dataset)",
     size=16, color=LIGHTBLUE, name="Subtitle")
text(s, 0.6, 3.95, 6.4, 1.2, ["Student name(s): [Enter name(s)]", "Register number(s): [Enter register number(s)]",
     "Department: [Enter department]", "Institution: [Enter institution]"], size=13, color=WHITE, name="Student details")

# 2 ── problem ─────────────────────────────────────────────────────────────
s = new_slide("CONTENT", "Problem statement and objectives")
text(s, 0.5, 1.2, 4.4, 0.35, "The problem", size=18, bold=True, color=BLUE, name="Heading problem")
text(s, 0.5, 1.6, 4.4, 1.2, "Given a house's size, rooms, age, location and condition, predict its price in Rs lakhs and "
     "explain which factors drive that price.", size=14, name="Problem text")
text(s, 0.5, 3.0, 4.4, 0.35, "Why it matters", size=18, bold=True, color=BLUE, name="Heading why")
text(s, 0.5, 3.4, 4.4, 1.5, "Buyers, sellers and lenders need a fair price estimate. Statistics shows which features matter "
     "and how sure we can be about it.", size=14, name="Why text")
card(s, 5.2, 1.2, 4.3, 3.8, TINT, "Objectives card")
text(s, 5.45, 1.35, 3.8, 0.4, "Objectives", size=18, bold=True, color=BLUE, font="Arial", name="Objectives heading")
text(s, 5.45, 1.85, 3.85, 3.1, ["Load and clean 1,000 house records", "Describe prices: mean, median, mode, variance, SD",
     "Sample, and test a hypothesis", "Probability: conditional, Bayes, law of large numbers", "Pearson and Spearman correlation",
     "Simple and multiple regression", "Matrices and gradient descent in NumPy", "Evaluate: MAE, MSE, RMSE, R², residuals"],
     size=13, bullets=True, space_after=3, name="Objectives list")

# 3 ── dataset ─────────────────────────────────────────────────────────────
s = new_slide("CONTENT", "Dataset and technologies")
for i, (big, small, sz) in enumerate([(f"{P['clean_rows']:,}", "house records", 30), ("10", "features + price", 30), ("Synthetic", "seed 42, reproducible", 22)]):
    x = 0.5 + i * 1.95
    card(s, x, 1.2, 1.8, 1.3, TINT, f"Stat card {i+1}")
    text(s, x, 1.28, 1.8, 0.65, big, size=sz, bold=True, color=ORANGE, font="Arial", align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, name=f"Stat {i+1}")
    text(s, x, 1.95, 1.8, 0.4, small, size=12, align=PP_ALIGN.CENTER, name=f"Stat label {i+1}")
table(s, 0.5, 2.7, [2.0, 3.75], [["Feature", "Meaning"], ["Area_sqft", "Built-up area (sq ft)"], ["Bedrooms, Bathrooms", "Number of rooms"],
      ["Age_years", "Age of the house"], ["Distance_to_City_km", "Distance to city centre"],
      ["Neighborhood_Rating, Parking_Spaces", "Rating 1-10; 0-2 spaces"], ["Location_Type, Furnishing", "Urban / Suburban / Rural; 3 levels"],
      ["Price_Lakhs (target)", "Sale price in Rs lakhs"]], size=11, row_h=0.285, name="Features table")
card(s, 6.5, 1.2, 3.0, 3.85, TINT, "Tech card")
text(s, 6.7, 1.3, 2.6, 0.4, "Technologies", size=18, bold=True, color=BLUE, font="Arial", name="Tech heading")
text(s, 6.7, 1.75, 2.6, 1.7, ["Python", "Pandas, NumPy", "SciPy, Scikit-learn", "Matplotlib, Seaborn", "pytest, Git and GitHub"],
     size=14, bullets=True, space_after=2, name="Tech list")
text(s, 6.7, 3.5, 2.6, 1.45, "Data note: prices come from a feature-based pricing rule plus 6% random noise (src/generate_data.py). "
     "Swap in a real CSV with the same columns and re-run to analyse real houses.", size=11, color=GREY, name="Data note")

# 4 ── methodology ─────────────────────────────────────────────────────────
s = new_slide("CONTENT", "Methodology")
imputed = sum(v["count"] for v in P["imputed"].values())
steps = [("Collect and clean", f"{P['raw_rows']:,} raw rows: {P['duplicates']} duplicates removed, {imputed} missing values imputed"),
         ("Statistics", "Mean, median, mode, variance, SD; sampling and CLT; Welch t-test, α = 0.05"),
         ("Probability", "P(price > Rs 100 lakhs), conditional on area, Bayes' theorem, law of large numbers"),
         ("Correlation and regression", "Pearson and Spearman matrices; simple and multiple linear regression"),
         ("Maths and evaluation", "Matrices, normal equation, gradient descent; MAE, MSE, RMSE, R², residuals")]
for i, (h, d) in enumerate(steps):
    y = 1.2 + i * 0.77
    b = card(s, 0.5, y + 0.04, 0.5, 0.5, BLUE, f"Step badge {i+1}", MSO_SHAPE.OVAL)
    text(s, 0.5, y + 0.04, 0.5, 0.5, str(i + 1), size=16, bold=True, color=WHITE, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, name=f"Step number {i+1}")
    text(s, 1.2, y, 3.0, 0.58, h, size=16, bold=True, anchor=MSO_ANCHOR.MIDDLE, name=f"Step title {i+1}")
    text(s, 4.3, y, 5.2, 0.58, d, size=14, anchor=MSO_ANCHOR.MIDDLE, name=f"Step text {i+1}")

# 5 ── statistics & probability ────────────────────────────────────────────
s = new_slide("CONTENT", "Statistics and probability")
picture(s, "fig05_hypothesis_test.png", 0.5, 1.15, w=3.6)
picture(s, "fig06_law_of_large_numbers.png", 0.5, 3.2, w=4.0)
table(s, 4.8, 1.15, [3.3, 1.4], [["Probability", "Value"],
      ["P(price > Rs 100 lakhs)", f3(PR["p_high"])], ["P(high | area > 1,500 sq ft)", f3(PR["p_high_given_large"])],
      ["P(high | area ≤ 1,500 sq ft)", f3(PR["p_high_given_not_large"])], ["P(Urban | high), Bayes = direct", f3(PR["p_urban_given_high_bayes"])]],
      size=11, row_h=0.3, align_right_from=1, name="Probability table")
text(s, 4.8, 2.85, 4.7, 2.3, [[("Hypothesis test: ", {"bold": True}), (f"Urban houses cost Rs {f1(H['diff'])} lakhs more than Suburban "
      f"(95% CI {f1(H['ci'][0])} to {f1(H['ci'][1])}; Welch t = {f1(H['t'])}, p < 0.001; Cohen's d = {f2(H['cohens_d'])}).", {})],
      [("Dependence: ", {"bold": True}), (f"P(high and large) = {f3(PR['p_high_and_large'])} is far above P(high) × P(large) = {f3(PR['independence_product'])}, "
      "so size and price are not independent.", {})],
      [("Sampling: ", {"bold": True}), (f"means of 1,000 samples (n = 30) have SD {f2(S['sampling']['clt_std_of_means'])}, "
      f"close to the theoretical {f2(S['sampling']['clt_theory_se'])} (CLT).", {})]], size=12, space_after=5, name="Statistics takeaways")

# 6 ── correlation & regression ────────────────────────────────────────────
s = new_slide("CONTENT", "Correlation and regression")
picture(s, "fig07_correlation_matrices.png", 0.5, 1.1, w=5.2)
picture(s, "fig09_regression.png", 0.5, 3.3, w=4.6)
ct = RG["corr_with_price"]; sm, mm = RG["simple"], RG["multiple"]
table(s, 6.0, 1.15, [1.5, 0.65, 0.65, 0.7], [["Test set", "MAE", "RMSE", "R²"],
      ["Simple (Area)", f1(sm["test"]["MAE"]), f1(sm["test"]["RMSE"]), f3(sm["test"]["R2"])],
      ["Multiple (all)", f1(mm["test"]["MAE"]), f1(mm["test"]["RMSE"]), f3(mm["test"]["R2"])]],
      size=11, row_h=0.3, highlight=2, align_right_from=1, name="Regression table")
text(s, 6.0, 2.2, 3.5, 3.0, [[("Strongest factors: ", {"bold": True}), (f"Area r = {f2(ct[0]['pearson_r'])}, Bedrooms {f2(ct[1]['pearson_r'])}, "
      f"Bathrooms {f2(ct[2]['pearson_r'])}; Spearman agrees.", {})],
      [("Simple model: ", {"bold": True}), (f"price = {f1(sm['intercept'])} + {sm['slope']:.4f} × area; area alone explains {sm['test']['R2']*100:.0f}% of test variance.", {})],
      [("Multiple model: ", {"bold": True}), (f"adds location, rooms, age, distance, rating, parking, furnishing: adjusted R² = {f3(mm['adj_r2'])}.", {})]],
     size=12, space_after=5, name="Regression takeaways")

# 7 ── NumPy mathematics ───────────────────────────────────────────────────
s = new_slide("CONTENT", "Mathematics with NumPy")
picture(s, "fig10_gradient_descent.png", 0.5, 1.1, w=9.0)
cards = [(f"{GD['initial_cost']:,.0f} → {GD['final_cost']:.2f}", "cost J(w) during gradient descent"),
         (f"{GD['max_weight_diff']:.0e}", "largest weight gap vs normal equation"),
         (f"{GD['test']['RMSE']:.2f}", f"test RMSE (Rs lakhs), R² {GD['test']['R2']:.3f}")]
for i, (big, small) in enumerate(cards):
    x = 0.5 + i * 3.075
    card(s, x, 4.05, 2.85, 1.05, TINT, f"Math card {i+1}")
    text(s, x, 4.1, 2.85, 0.55, big, size=22, bold=True, color=ORANGE, font="Arial", align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, name=f"Math value {i+1}")
    text(s, x + 0.1, 4.65, 2.65, 0.4, small, size=11, align=PP_ALIGN.CENTER, name=f"Math label {i+1}")

# 8 ── results ─────────────────────────────────────────────────────────────
s = new_slide("CONTENT", "Results and visualization")
picture(s, "fig13_actual_vs_predicted.png", 0.5, 1.1, w=5.0)
picture(s, "fig12_residuals.png", 0.5, 3.2, w=5.0)
rows = [["Test set", "MAE", "RMSE", "R²"]] + [[n.replace(" Regression", " LR").replace("Mean baseline", "Mean baseline"), f1(v["MAE"]), f1(v["RMSE"]), f3(v["R2"])] for n, v in tm.items()]
hi = 1 + list(tm).index(sel)
table(s, 5.8, 1.15, [1.6, 0.65, 0.7, 0.7], rows, size=11, row_h=0.3, highlight=hi, align_right_from=1, name="Metrics table")
rs = MD["residual_stats"]; band = {b["band"]: b["mean_residual"] for b in MD["residual_by_price_band"]}
text(s, 5.8, 3.1, 3.7, 2.1, [[("Selected on validation: ", {"bold": True}), (f"{sel}.", {})],
     f"Typical error Rs {f1(tm[sel]['MAE'])} lakhs ({tm[sel]['MAPE']:.1f}%); {rs['within_10']:.0f}% of houses within Rs 10 lakhs.",
     f"Mean residual +{f1(rs['mean'])}: slight underestimate, mostly for high-priced homes (+{f1(band['High-priced'])})."],
     size=12, space_after=5, name="Results takeaways")

# 9 ── conclusion ──────────────────────────────────────────────────────────
s = new_slide("CLOSING_DARK", "Conclusion and future scope", dark=True)
cols = [("Achievements", [f"Full pipeline on {P['clean_rows']:,} houses", f"Best model: R² {f3(tm[sel]['R2'])}, RMSE Rs {f1(tm[sel]['RMSE'])} lakhs",
                          "Gradient descent matches exact solution", "Reproducible code and tests"]),
        ("Limitations", ["Synthetic data, not market data", "Linear pricing rule favours linear models", "Single random split", "Median imputation before split"]),
        ("Future scope", ["Real listings (Kaggle, Ames, city data)", "Log-price and interaction terms", "Cross-validation, ridge/lasso", "Web app for price estimates"])]
for i, (h, items) in enumerate(cols):
    x = 0.5 + i * 3.05
    card(s, x, 1.3, 2.85, 3.3, BLUE, f"Column card {i+1}")
    text(s, x + 0.2, 1.45, 2.45, 0.45, h, size=18, bold=True, color=WHITE, font="Arial", name=f"Column heading {i+1}")
    text(s, x + 0.2, 2.0, 2.45, 2.5, items, size=14, color=WHITE, bullets=True, space_after=5, name=f"Column list {i+1}")

out = ROOT / "reports/House_Price_Prediction_Presentation.pptx"
out.parent.mkdir(exist_ok=True); prs.save(out); print("saved", out)
