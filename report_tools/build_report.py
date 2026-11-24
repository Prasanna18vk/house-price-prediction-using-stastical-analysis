"""Build the project report (DOCX, then PDF via LibreOffice) from results/results.json.
Run:  python report_tools/build_report.py   (PDF export needs LibreOffice: soffice)
"""
import json, re, subprocess
from pathlib import Path
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm, Twips
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = Path(__file__).resolve().parents[1]
R = json.loads((ROOT / "results/results.json").read_text())
FIG = ROOT / "results/figures"
TITLE = "House Price Prediction Using Statistical Analysis"
NAVY, BLUE, GREYT = RGBColor(0x16, 0x36, 0x5C), RGBColor(0x22, 0x60, 0x8F), RGBColor(0x6B, 0x72, 0x80)

doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.left_margin = sec.right_margin = Cm(2.3); sec.top_margin = Cm(2.2); sec.bottom_margin = Cm(2.2)
TEXT_W = 21 - 4.6   # cm

st = doc.styles
st["Normal"].font.name = "Calibri"; st["Normal"].font.size = Pt(11)
st["Normal"].element.rPr.rFonts.set(qn("w:eastAsia"), "Calibri")
st["Normal"].paragraph_format.space_after = Pt(6); st["Normal"].paragraph_format.line_spacing = 1.12
for name, size, col, before in [("Heading 1", 17, NAVY, 14), ("Heading 2", 13, BLUE, 8)]:
    h = st[name]; h.font.name = "Calibri"; h.font.size = Pt(size); h.font.bold = True; h.font.color.rgb = col
    h.element.rPr.rFonts.set(qn("w:ascii"), "Calibri"); h.element.rPr.rFonts.set(qn("w:hAnsi"), "Calibri")
    h.paragraph_format.space_before = Pt(before); h.paragraph_format.space_after = Pt(5); h.paragraph_format.keep_with_next = True

counters = {"fig": 0, "tab": 0}


def runs(p, text, size=None, color=None, italic=False):
    for i, part in enumerate(re.split(r"\*\*", text)):
        if not part: continue
        r = p.add_run(part); r.bold = i % 2 == 1; r.italic = italic
        if size: r.font.size = Pt(size)
        if color: r.font.color.rgb = color
    return p


def para(text, align=WD_ALIGN_PARAGRAPH.JUSTIFY, **kw):
    p = doc.add_paragraph(); p.alignment = align; return runs(p, text, **kw)


def bullet(text):
    p = doc.add_paragraph(style="List Bullet"); p.paragraph_format.space_after = Pt(3); return runs(p, text)


def h1(t): return doc.add_heading(t, 1)
def h2(t): return doc.add_heading(t, 2)


def shade(cell, hex_):
    tcPr = cell._tc.get_or_add_tcPr(); sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear"); sh.set(qn("w:color"), "auto"); sh.set(qn("w:fill"), hex_); tcPr.append(sh)


def borders(tbl, color="C9D6E3"):
    tblPr = tbl._tbl.tblPr; b = OxmlElement("w:tblBorders")
    for e in ("top", "left", "bottom", "right", "insideH", "insideV"):
        x = OxmlElement(f"w:{e}"); x.set(qn("w:val"), "single"); x.set(qn("w:sz"), "4"); x.set(qn("w:color"), color); b.append(x)
    tblPr.append(b)


def caption(text):
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.space_after = Pt(10)
    r = p.add_run(text); r.italic = True; r.font.size = Pt(9); r.font.color.rgb = GREYT


def table(rows, widths_cm, cap, size=9, highlight=None, right_from=None):
    counters["tab"] += 1
    t = doc.add_table(rows=len(rows), cols=len(rows[0])); t.alignment = WD_TABLE_ALIGNMENT.CENTER; t.autofit = False
    borders(t)
    for j, wd in enumerate(widths_cm): t.columns[j].width = Cm(wd)
    for i, row in enumerate(rows):
        tr = t.rows[i]
        trPr = tr._tr.get_or_add_trPr(); cs = OxmlElement("w:cantSplit"); trPr.append(cs)
        for j, v in enumerate(row):
            c = tr.cells[j]; c.width = Cm(widths_cm[j])
            p = c.paragraphs[0]; p.paragraph_format.space_after = Pt(1); p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.line_spacing = 1.0
            if right_from is not None and j >= right_from: p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            r = p.add_run(str(v)); r.font.size = Pt(size)
            if i == 0: r.bold = True; r.font.color.rgb = RGBColor(255, 255, 255); shade(c, "22608F")
            elif highlight == i: r.bold = True; shade(c, "FCE9D6")
            elif i % 2 == 0: shade(c, "EAF1F8")
        if i < len(rows) - 1:
            for c in tr.cells: c.paragraphs[0].paragraph_format.keep_with_next = True
    caption(f"Table {counters['tab']}: {cap}")


def figure(name, width_cm, cap):
    counters["fig"] += 1
    p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.paragraph_format.keep_with_next = True
    p.paragraph_format.space_after = Pt(2); p.add_run().add_picture(str(FIG / name), width=Cm(width_cm))
    caption(f"Figure {counters['fig']}: {cap}")


def field(par, code):
    r = par.add_run(); b = OxmlElement("w:fldChar"); b.set(qn("w:fldCharType"), "begin"); r._r.append(b)
    r2 = par.add_run(); it = OxmlElement("w:instrText"); it.set(qn("xml:space"), "preserve"); it.text = code; r2._r.append(it)
    r3 = par.add_run(); e = OxmlElement("w:fldChar"); e.set(qn("w:fldCharType"), "end"); r3._r.append(e)
    for x in (r, r2, r3): x.font.size = Pt(9); x.font.color.rgb = GREYT


# footer (not on the title page)
sec.different_first_page_header_footer = True
fp = sec.footer.paragraphs[0]
for tw in (4680, 9360): fp.paragraph_format.tab_stops.add_tab_stop(Twips(tw), WD_TAB_ALIGNMENT.CLEAR)
fp.paragraph_format.tab_stops.add_tab_stop(Cm(TEXT_W), WD_TAB_ALIGNMENT.RIGHT)
r = fp.add_run(TITLE + "\tPage "); r.font.size = Pt(9); r.font.color.rgb = GREYT; field(fp, "PAGE")

f1 = lambda v: f"{v:,.1f}"; f2 = lambda v: f"{v:,.2f}"; f3 = lambda v: f"{round(v, 3) + 0.0:.3f}"
P, S, PR, RG, MT, MD = (R[k] for k in ["preprocessing", "statistics", "probability", "regression", "math", "models"])
H, GD, SA = S["hypothesis"], MT["gradient_descent"], S["sampling"]
sel, tm, vm = MD["selected"], MD["test_metrics"], MD["val_metrics"]
sm, mm, rs = RG["simple"], RG["multiple"], MD["residual_stats"]
imputed = sum(v["count"] for v in P["imputed"].values())
pv = lambda p: "< 0.001" if p < 0.001 else f"{p:.3f}"

# ── title page ─────────────────────────────────────────────────────────────
for _ in range(6): doc.add_paragraph()
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("House Price Prediction\nUsing Statistical Analysis"); r.bold = True; r.font.size = Pt(30); r.font.color.rgb = NAVY
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("Statistical and Mathematical Techniques with Regression Modelling"); r.bold = True; r.font.size = Pt(14); r.font.color.rgb = BLUE
doc.add_paragraph(); p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER; p.add_run("Academic Project Report").font.size = Pt(14)
doc.add_paragraph()
info = [("Student name(s):", "[Enter name(s) here]"), ("Register number(s):", "[Enter register number(s)]"), ("Department:", "[Enter department]"),
        ("Institution:", "[Enter institution]"), ("Guide / Faculty:", "[Enter guide name]"), ("Academic year:", "[Enter academic year]")]
t = doc.add_table(rows=len(info), cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER
t.autofit = False; t.columns[0].width = Cm(5); t.columns[1].width = Cm(9.5)
for i, (a, b) in enumerate(info):
    for j, v in enumerate((a, b)):
        c = t.rows[i].cells[j]; c.width = Cm(5 if j == 0 else 9.5); c.paragraphs[0].add_run(v).font.size = Pt(11)
        pPr = c._tc.get_or_add_tcPr(); bd = OxmlElement("w:tcBorders"); x = OxmlElement("w:bottom")
        x.set(qn("w:val"), "single"); x.set(qn("w:sz"), "4"); x.set(qn("w:color"), "999999"); bd.append(x); pPr.append(bd)
for _ in range(3): doc.add_paragraph()
p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run(f"Dataset: {P['clean_rows']:,} house records (synthetic, reproducible with seed 42; see Section 6)"); r.italic = True; r.font.size = Pt(9.5); r.font.color.rgb = GREYT
doc.add_page_break()

# ── contents ───────────────────────────────────────────────────────────────
c = doc.add_heading("Contents", 1)
secs = ["Abstract", "Introduction", "Problem statement", "Objectives", "Literature and background overview", "Dataset description",
        "Methodology", "Data preprocessing", "Statistical analysis", "Probability and hypothesis testing", "Correlation and regression",
        "Mathematical implementation", "Machine learning models", "Model evaluation", "Results and discussion", "Limitations",
        "Future enhancements", "Conclusion", "References"]
for i, s_ in enumerate(secs, 1):
    p = doc.add_paragraph(f"{i}. {s_}"); p.paragraph_format.left_indent = Cm(1); p.paragraph_format.space_after = Pt(4)
doc.add_page_break()

# ── 1 Abstract ─────────────────────────────────────────────────────────────
h1("1. Abstract")
para(f"This project studies {P['clean_rows']:,} house records and builds models that predict the sale price in Rs lakhs from the size, rooms, age, location, "
     f"neighbourhood rating, parking and furnishing of each house. The data were cleaned ({P['duplicates']} duplicate rows removed, {imputed} missing values imputed), "
     f"summarised with descriptive statistics and sampling, and examined with probability theory, a Welch t-test, Pearson and Spearman correlation and regression. "
     f"Linear regression was also implemented from scratch with NumPy matrices and gradient descent, which reached the same solution as the closed-form normal equation. "
     f"Five models were compared on a random 70/15/15 split: a mean baseline, simple linear regression (area only), multiple linear regression, random forest and gradient boosting. "
     f"The model chosen on validation data was **{sel}**, with test MAE = Rs {f2(tm[sel]['MAE'])} lakhs, RMSE = Rs {f2(tm[sel]['RMSE'])} lakhs and R² = {f3(tm[sel]['R2'])}. "
     f"Area alone explains only {sm['test']['R2']*100:.0f}% of the variation in price, so the full set of features is needed. "
     f"The dataset is synthetic (generated from a known pricing rule plus noise), so the results demonstrate the methods rather than describe a real housing market.")
para("**Keywords:** house price prediction, descriptive statistics, hypothesis testing, correlation, multiple linear regression, gradient descent, residual analysis.")

h1("2. Introduction")
para("A house is usually the largest purchase a family makes, so a fair price estimate matters to buyers, sellers, banks and tax authorities. Prices depend on many things at once: "
     "how big the house is, how many rooms it has, how old it is, how far it is from the city and how good the neighbourhood is. Statistics helps to describe these patterns and to test "
     "whether they are real; mathematics (linear algebra and calculus) explains how a prediction model is built; and regression turns both into a price estimate. "
     "This project follows the full data-science workflow, from raw data to a report, using only open tools: Python, Pandas, NumPy, SciPy, Matplotlib, Seaborn and Scikit-learn.")

h1("3. Problem statement")
para("**Problem:** Given the features of a house, predict its price in Rs lakhs and explain which features are significantly related to price.")
para("**Why analyse house prices?** Statistical analysis shows typical price ranges, the effect of location, and how strongly size, age and distance influence price. "
     "**Why predict the price?** A prediction gives a reference value for negotiation, valuation and lending. **The machine-learning task** is supervised regression: "
     "the inputs are the ten house features and the output is a continuous value (price in Rs lakhs).")

h1("4. Objectives")
for b in ["Load and clean a dataset of at least 1,000 house records; identify numerical and categorical variables.",
          "Compute mean, median, mode, variance and standard deviation; study the price distribution and apply sampling techniques.",
          "Test a hypothesis comparing prices between two groups of houses.",
          "Calculate probability, conditional probability and Bayes' theorem for house prices; illustrate the law of large numbers.",
          "Measure relationships with Pearson and Spearman correlation and a correlation matrix.",
          "Build a simple and a multiple linear regression model and compare them.",
          "Implement matrix operations, the normal equation and gradient descent with NumPy.",
          "Evaluate models with MAE, MSE, RMSE, R² and residual analysis."]: bullet(b)

h1("5. Literature and background overview")
para("The standard economic framework for house prices is the hedonic model (Rosen, 1974): the price of a house is the sum of the values the market places on its characteristics, such as size, "
     "location and quality. Harrison and Rubinfeld (1978) applied it to Boston housing data, and De Cock (2011) proposed the Ames, Iowa data as a modern teaching alternative. "
     "Multiple linear regression is the usual way to estimate hedonic prices because each coefficient reads as the price change for one extra unit of a feature. "
     "Tree ensembles such as random forests (Breiman, 2001) and gradient boosting (Friedman, 2001) can capture non-linear effects and interactions but are harder to interpret. "
     "Good practice is to compare every model against a simple baseline and to keep a test set untouched until the final evaluation. "
     "The tools used are NumPy (Harris et al., 2020), SciPy (Virtanen et al., 2020), Scikit-learn (Pedregosa et al., 2011), Pandas (McKinney, 2010) and Matplotlib (Hunter, 2007).")

h1("6. Dataset description")
para(f"**Important: the dataset is synthetic.** It could not be downloaded from a public source in the environment where this project was prepared, so it was generated by the script "
     f"src/generate_data.py with a fixed random seed (42). Each house gets random features, and its price is computed from a hedonic pricing rule (a base value plus amounts for area, "
     f"bedrooms, bathrooms, age, distance, neighbourhood rating, parking, furnishing and location) with 6% random noise. The raw file has {P['raw_rows']:,} rows: {P['clean_rows']:,} unique houses, "
     f"{P['duplicates']} duplicate rows and {imputed} missing values that were injected on purpose so that the cleaning step has real work to do. "
     f"Because the pricing rule is known, the analysis shows how the methods behave; conclusions apply to this dataset, not to a real city. "
     f"To analyse real houses, replace data/house_prices_raw.csv with a CSV that has the same columns and run the pipeline again.")
table([["Feature", "Type", "Meaning"],
       ["House_ID", "Identifier", "Unique house ID"], ["Location_Type", "Categorical", "Urban, Suburban or Rural"],
       ["Area_sqft", "Numerical", "Built-up area in square feet"], ["Bedrooms", "Numerical (discrete)", "Number of bedrooms (1-5)"],
       ["Bathrooms", "Numerical (discrete)", "Number of bathrooms (1-4)"], ["Age_years", "Numerical", "Age of the house in years"],
       ["Distance_to_City_km", "Numerical", "Distance to the city centre (km)"], ["Neighborhood_Rating", "Numerical (ordinal)", "Neighbourhood quality, 1 (low) to 10 (high)"],
       ["Parking_Spaces", "Numerical (discrete)", "Number of parking spaces (0-2)"], ["Furnishing", "Categorical", "Unfurnished, Semi-Furnished or Furnished"],
       ["Price_Lakhs", "Numerical (target)", "Sale price in Rs lakhs (1 lakh = 100,000 rupees)"]], [4.2, 3.8, 8.4], "Dataset features", size=9.5)

h1("7. Methodology")
para("The project follows the workflow below. Each step is a separate Python module in the src folder so that it can be read, tested and re-run independently.")
for b in ["**1-2.** Define the problem; collect and inspect the dataset.", "**3.** Clean the data and split it into training, validation and test sets.",
          "**4.** Descriptive statistics, sampling and hypothesis testing.", "**5.** Probability analysis: conditional probability, Bayes' theorem, law of large numbers.",
          "**6.** Correlation, simple and multiple regression.", "**7.** NumPy linear algebra, cost function and gradient descent.",
          "**8.** Model development and tuning; **9.** evaluation with four metrics and residual analysis; **10.** report and presentation."]: bullet(b)
para(f"**Prediction set-up.** The target is Price_Lakhs. The inputs are the seven numerical features plus dummy variables for location (baseline: Rural) and furnishing (baseline: Unfurnished). "
     f"The data are split at random into training ({P['split']['train']} houses), validation ({P['split']['val']}) and test ({P['split']['test']}) sets. Models are fitted on the training set, "
     f"the best one is chosen on the validation set, and the test set is used once for the final report.")
table([["Split", "Houses", "Share", "Used for"], ["Training", P["split"]["train"], "70%", "Fitting and tuning"],
       ["Validation", P["split"]["val"], "15%", "Choosing the model"], ["Test", P["split"]["test"], "15%", "Final evaluation"]],
      [3.5, 3, 3, 6], "Random split of the 1,000 houses (seed 42)", size=10)

h1("8. Data preprocessing")
para(f"**Duplicates:** {P['duplicates']} exact duplicate rows were found and removed, leaving {P['clean_rows']:,} houses. "
     f"**Missing values:** {P['missing_before'].get('Age_years', 0)} in Age_years and {P['missing_before'].get('Neighborhood_Rating', 0)} in Neighborhood_Rating; "
     f"they were filled with the column median (Age_years = {P['imputed']['Age_years']['value']:.0f}, Neighborhood_Rating = {P['imputed']['Neighborhood_Rating']['value']:.0f}). "
     f"**Impossible values** (non-positive area or price, negative age, rating outside 1-10): {P['impossible_values']} found. "
     f"**Variable types:** {len(P['numeric_vars'])} numerical variables (including the target), 2 categorical variables (Location_Type, Furnishing) and one identifier.")
table([["Variable", "Lower fence", "Upper fence", "Outliers (IQR rule)"]] + [[o["variable"], f2(o["lower"]), f2(o["upper"]), o["outliers"]] for o in P["outliers"]],
      [5, 3.5, 3.5, 4], "Outlier detection with the 1.5 × IQR rule", size=10, right_from=1)
para("The outliers flagged by the 1.5 × IQR rule were kept: very large or distant houses and very expensive houses are genuine cases that a price model must handle, "
     "and the metrics used (MAE, RMSE) keep their effect visible.")

h1("9. Statistical analysis")
rows = [["Variable", "Mean", "Median", "Mode", "Var.", "Std", "Min", "Q1", "Q3", "Max"]]
fmt = lambda v: f"{v:,.0f}" if abs(v) >= 1000 else f"{v:,.2f}" if abs(v) < 100 else f"{v:,.1f}"
for d in S["descriptive"]:
    rows.append([d["variable"]] + [fmt(d[k]) for k in ["mean", "median", "mode", "variance", "std", "min", "q1", "q3", "max"]])
table(rows, [3.6, 1.4, 1.4, 1.2, 1.7, 1.2, 1.2, 1.2, 1.3, 1.4][:10], "Descriptive statistics (variance and standard deviation use n − 1)", size=8, right_from=1)
pz = S["price"]
para(f"**Observations.** The mean price is Rs {f1(pz['mean'])} lakhs and the median Rs {f1(pz['median'])} lakhs, with a standard deviation of Rs {f1(pz['std'])} lakhs. "
     f"The distribution is almost symmetric (skewness {pz['skew']:.2f}, kurtosis {pz['kurtosis']:.2f}); the Shapiro-Wilk p-value of {pz['shapiro_p']:.3f} shows a small departure from perfect normality. "
     f"Prices range from Rs {f1(pz['min'])} to Rs {f1(pz['max'])} lakhs.")
figure("fig01_price_distribution.png", 15, "Price distribution and price by location type")
bl = {d["Location_Type"]: d for d in S["by_location"]}
para(f"Urban houses are the most expensive (mean Rs {f1(bl['Urban']['mean_price'])} lakhs), followed by Suburban (Rs {f1(bl['Suburban']['mean_price'])}) and Rural (Rs {f1(bl['Rural']['mean_price'])}). "
     f"Mean price also rises with the number of bedrooms and with furnishing level (Figure 2).")
figure("fig02_group_means.png", 15.5, "Mean price by location, furnishing and number of bedrooms")
figure("fig03_feature_distributions.png", 14.5, "Distributions of the main numerical features")
h2("Sampling techniques")
para(f"A simple random sample of {SA['srs_n']} houses gave a mean price of Rs {f1(SA['srs_mean'])} lakhs (standard error {f2(SA['srs_se'])}; 95% confidence interval {f1(SA['srs_ci'][0])} to {f1(SA['srs_ci'][1])}), "
     f"which contains the population mean of Rs {f1(SA['population_mean'])} lakhs. A proportional stratified sample ({SA['strat_n']} houses, strata = location type) gave Rs {f1(SA['strat_mean'])} lakhs. "
     f"Drawing {SA['clt_samples']:,} samples of n = {SA['clt_n']} and averaging each gave means with a standard deviation of {f2(SA['clt_std_of_means'])}, close to the theoretical σ/√n = {f2(SA['clt_theory_se'])}; "
     f"their distribution is bell-shaped (skewness {SA['clt_skew_of_means']:.2f}), which is the central limit theorem at work.")
figure("fig04_sampling_distribution.png", 14, "Population of prices and the distribution of 1,000 sample means (n = 30)")

h1("10. Probability and hypothesis testing")
h2("Probability analysis")
para(f"Events: **high price** = price above Rs {PR['threshold_price']:.0f} lakhs (Rs 1 crore); **large house** = area above {PR['threshold_area']:,} sq ft; **Urban** = location type Urban.")
table([["Quantity", "Value", "Meaning"],
       ["P(high)", f3(PR["p_high"]), f"{PR['n_high']} of {PR['n']:,} houses exceed Rs 100 lakhs"],
       ["P(large)", f3(PR["p_large"]), "Share of houses above 1,500 sq ft"],
       ["P(high | large)", f3(PR["p_high_given_large"]), "Conditional probability of a high price given a large house"],
       ["P(high | not large)", f3(PR["p_high_given_not_large"]), "High-price probability for smaller houses"],
       ["P(Urban)", f3(PR["p_urban"]), "Prior: share of Urban houses"],
       ["P(high | Urban)", f3(PR["p_high_given_urban"]), "Likelihood in Bayes' theorem"],
       ["P(Urban | high), Bayes", f3(PR["p_urban_given_high_bayes"]), "= P(high | Urban) × P(Urban) / P(high)"],
       ["P(Urban | high), direct", f3(PR["p_urban_given_high_direct"]), "Counted directly (verification)"]],
      [4.2, 2, 10.2], "Probability results", size=9.5)
para(f"A large house is much more likely to be high-priced: P(high | large) = {f3(PR['p_high_given_large'])} against P(high) = {f3(PR['p_high'])}. The two events are **not independent**, because "
     f"P(high and large) = {f3(PR['p_high_and_large'])} is far above P(high) × P(large) = {f3(PR['independence_product'])}. Bayes' theorem gives P(Urban | high) = "
     f"{f3(PR['p_high_given_urban'])} × {f3(PR['p_urban'])} / {f3(PR['p_high'])} = {f3(PR['p_urban_given_high_bayes'])}, identical to the directly counted value, so about {PR['p_urban_given_high_bayes']*100:.0f}% of "
     f"high-priced houses are Urban although only {PR['p_urban']*100:.0f}% of all houses are.")
e = PR["lln"]
para(f"**Law of large numbers.** Three random samples drawn with replacement were tracked as they grew. With n = 10 the sample proportions were off by {e[0]['err_n10']:.3f}, {e[1]['err_n10']:.3f} and {e[2]['err_n10']:.3f} "
     f"from the true P(high) = {f3(PR['p_high'])}; with n = 2,000 the errors were {e[0]['err_n2000']:.3f}, {e[1]['err_n2000']:.3f} and {e[2]['err_n2000']:.3f}. The sample proportion settles near the true value as the sample grows.")
figure("fig06_law_of_large_numbers.png", 12.5, "Law of large numbers: running share of high-priced houses in random samples")
h2("Hypothesis test")
para(f"**H0:** mean price of Urban houses = mean price of Suburban houses. **H1:** the means differ. **Test:** Welch two-sample t-test (unequal variances), two-sided, significance level α = {H['alpha']}.")
table([["Statistic", "Value"], [f"Mean (Urban, n = {H['n_a']})", f"Rs {f2(H['mean_a'])} lakhs"], [f"Mean (Suburban, n = {H['n_b']})", f"Rs {f2(H['mean_b'])} lakhs"],
       ["Mean difference", f"Rs {f2(H['diff'])} lakhs, 95% CI [{f2(H['ci'][0])}, {f2(H['ci'][1])}]"], ["t statistic (df)", f"{f2(H['t'])} ({H['df']:.0f})"],
       ["p-value", f"{H['p']:.2e}"], ["Cohen's d (effect size)", f2(H["cohens_d"])], ["Mann-Whitney p-value (check)", f"{H['mannwhitney_p']:.2e}"],
       ["One-way ANOVA, all 3 locations", f"F = {f1(H['anova_F'])}, p = {H['anova_p']:.1e}"], ["Decision", H["decision"]]],
      [7, 9.4], "Hypothesis test results", size=9.5)
para(f"Because the p-value is far below 0.05, we **reject H0**: Urban houses are on average Rs {f1(H['diff'])} lakhs more expensive than Suburban houses, a medium-sized effect (d = {f2(H['cohens_d'])}). "
     f"Levene's test (p = {H['levene_p']:.2f}) supports equal variances, so the Welch test is conservative. The Shapiro-Wilk test shows the Urban prices are slightly non-normal (p = {H['shapiro_p_a']:.3f}), "
     f"so the distribution-free Mann-Whitney test was added as a check; it agrees. The ANOVA across all three location types is also significant.")
figure("fig05_hypothesis_test.png", 11, "Price distributions for Urban and Suburban houses")

h1("11. Correlation and regression")
h2("Correlation analysis")
figure("fig07_correlation_matrices.png", 16, "Pearson and Spearman correlation matrices")
ct = RG["corr_with_price"]
table([["Feature", "Pearson r", "p-value", "Spearman ρ", "p-value"]] + [[c_["variable"], f3(c_["pearson_r"]), pv(c_["pearson_p"]), f3(c_["spearman_rho"]), pv(c_["spearman_p"])] for c_ in ct],
      [5, 2.7, 2.7, 2.7, 2.7], "Correlation of each feature with price", size=9.5, right_from=1)
tp = RG["top_predictor_pairs"][0]
para(f"The strongest factors associated with price are **Area_sqft** (r = {f2(ct[0]['pearson_r'])}), **Bedrooms** ({f2(ct[1]['pearson_r'])}) and **Bathrooms** ({f2(ct[2]['pearson_r'])}); "
     f"Neighborhood_Rating (+) and Distance_to_City_km (−) follow, and Age_years has a weak negative relationship. Parking_Spaces shows almost no linear relationship with price "
     f"(r = {f2(ct[-1]['pearson_r'])}, p = {pv(ct[-1]['pearson_p'])}) even though it has an effect once the other features are held fixed (see the multiple regression). Spearman values are close to Pearson values, so the relationships are "
     f"mostly linear and monotonic. The largest correlation among the features themselves is {tp['a']} vs {tp['b']} (r = {f2(tp['r'])}), which warns of multicollinearity. **Correlation does not imply causation.**")
figure("fig08_top_scatter.png", 15.5, "Price against the three most correlated features")
h2("Simple linear regression")
para(f"Model: Price = {f2(sm['intercept'])} + {sm['slope']:.4f} × Area_sqft (fitted on the training set). Each extra square foot is associated with Rs {sm['slope']*100000:,.0f} more in price. "
     f"Training R² = {f3(sm['train_r2'])}; on the test set MAE = {f2(sm['test']['MAE'])}, RMSE = {f2(sm['test']['RMSE'])} lakhs and R² = {f3(sm['test']['R2'])}. "
     f"Area alone leaves more than half of the variation unexplained, because location, rooms and age also matter.")
h2("Multiple linear regression")
para(f"Using Area, Bedrooms, Bathrooms, Age, Distance, Rating, Parking and the location and furnishing dummies, the model reaches test MAE = {f2(mm['test']['MAE'])}, RMSE = {f2(mm['test']['RMSE'])} lakhs and "
     f"R² = {f3(mm['test']['R2'])} (training adjusted R² = {f3(mm['adj_r2'])}; overall F-test p {pv(mm['f_p'])}). Coefficients below are in Rs lakhs per unit and were estimated with NumPy.")
table([["Variable", "Coefficient", "Std. error", "t", "p-value", "95% CI"]] + [[t_["variable"], f"{t_['coef']:.3f}", f"{t_['std_err']:.3f}", f"{t_['t']:.1f}", pv(t_["p"]), f"[{t_['ci_low']:.2f}, {t_['ci_high']:.2f}]"] for t_ in mm["table"]],
      [4.4, 2.4, 2.2, 1.8, 2.0, 3.6], "Multiple regression coefficients (training set, baselines: Rural, Unfurnished)", size=9, right_from=1)
top_std = list(mm["std_coef"].items())[:3]
para("Reading the table: holding everything else fixed, an Urban house costs about Rs " + f1(next(t_['coef'] for t_ in mm['table'] if t_['variable'] == 'Loc_Urban')) +
     " lakhs more than a Rural one; each additional year of age lowers the price by about Rs " + f2(-next(t_['coef'] for t_ in mm['table'] if t_['variable'] == 'Age_years')) +
     " lakhs, and each extra kilometre from the city by about Rs " + f2(-next(t_['coef'] for t_ in mm['table'] if t_['variable'] == 'Distance_to_City_km')) +
     " lakhs. " + ("Every coefficient except the intercept is significant at 5%." if all(t_["p"] < 0.05 for t_ in mm["table"][1:]) else "Not every coefficient is significant at 5%.") +
     " Variance inflation factors for the numerical features are at most " + f"{max(mm['vif'].values()):.1f}" + " (" + max(mm["vif"], key=mm["vif"].get) +
     "), so multicollinearity is moderate and acceptable. Standardised coefficients, which make the features comparable, rank " +
     ", ".join(f"{k} ({v:+.1f})" for k, v in top_std) + " highest.")
figure("fig09_regression.png", 15, "Simple regression line and multiple regression predictions on the test set")

h1("12. Mathematical implementation")
la = MT["linear_algebra"]
para("Linear regression was implemented using only NumPy to show the mathematics behind the library models. Features were standardised and a column of ones was added for the intercept, so the prediction is the matrix product ŷ = Xw.")
for b in [f"**Vector:** the first 7 prices form a vector of shape {tuple(la['vector_shape'])}: {la['vector']}.",
          f"**Matrix:** the first 7 houses × 7 numerical features form a matrix of shape {tuple(la['matrix_shape'])}.",
          f"**Matrix addition:** adding two blocks of 5 houses element by element and halving gives the average feature values; for the first row: {[round(v, 1) for v in la['matrix_add_mean_first_row']]} (Area, Bedrooms, Bathrooms, Age).",
          f"**Dot product:** the mean-centred dot product of area and price over the training set is {la['dot_area_price_centered']:,.0f} (positive: they move together); the cosine similarity is {la['cosine_area_price']:.3f}.",
          f"**Matrix multiplication:** XᵀX has shape {tuple(la['xtx_shape'])} for the 7-feature demonstration, and the standardised training design matrix has condition number {la['xtx_condition_number']:.1f} (well conditioned).",
          "**Normal equation:** w = (XᵀX)⁻¹Xᵀy gives the exact least-squares weights in one step.",
          "**Cost function:** J(w) = (1/2m) Σ (Xw − y)², half the mean squared error.",
          "**Gradient:** ∇J = (1/m) Xᵀ(Xw − y), obtained with calculus; it points uphill, so each step moves the opposite way: w ← w − α∇J. A unit test checks this formula against a numerical derivative."]: bullet(b)
cl = GD["cost_after_200_by_alpha"]
table([["Quantity", "Value"], ["Learning rate α", GD["alpha"]], ["Iterations", GD["iterations"]], ["Initial cost J(0)", f"{GD['initial_cost']:,.2f}"],
       ["Cost after 10 iterations", f"{GD['cost_10']:,.2f}"], ["Cost after 100 iterations", f"{GD['cost_100']:,.2f}"], ["Final cost", f"{GD['final_cost']:.4f}"],
       ["Cost at normal-equation solution", f"{GD['normal_eq_cost']:.4f}"], ["Largest weight difference (GD vs normal equation)", f"{GD['max_weight_diff']:.1e}"],
       ["Test RMSE of the NumPy model (Rs lakhs)", f2(GD["test"]["RMSE"])], ["Test R² of the NumPy model", f3(GD["test"]["R2"])]], [9, 7.4], "Gradient descent results", size=9.5)
para(f"The cost fell from {GD['initial_cost']:,.0f} to {GD['final_cost']:.2f}, matching the closed-form minimum, so gradient descent converged to the same weights. The learning rate matters: after 200 iterations the cost was "
     f"{cl['0.001']:,.0f} for α = 0.001 (too slow), {cl['0.01']:,.1f} for α = 0.01, and {cl['0.1']:.2f} and {cl['0.5']:.2f} for α = 0.1 and 0.5. The parameter paths show Area, Neighborhood_Rating and the Urban dummy settling at the largest positive values and Distance and Age at negative values.")
figure("fig10_gradient_descent.png", 16, "Cost and parameter values during gradient descent, and the effect of the learning rate")

h1("13. Machine learning models")
para("Five models were developed. The **mean baseline** always predicts the average training price. **Simple linear regression** uses area only. **Multiple linear regression** uses all features. "
     "**Random forest** averages many decision trees trained on random subsets of data and features. **Gradient boosting** builds trees one after another, each correcting the previous errors.")
para("**Avoiding leakage.** (1) The split is made before any model is fitted. (2) Hyper-parameters of the two ensemble models were tuned by 5-fold cross-validation on the training set only. "
     "(3) The models were compared on the validation set and the best was selected by validation RMSE. (4) The test set was used once, for the final report.")
tu = MD["tuning"]
table([["Model", "Best hyper-parameters", "CV RMSE", "Combinations"]] + [[k, ", ".join(f"{a}={b}" for a, b in v["params"].items()), f2(v["cv_rmse"]), v["combinations"]] for k, v in tu.items()],
      [3.5, 8.1, 2.2, 2.6], "Hyper-parameter tuning (5-fold cross-validation on the training set)", size=9.5)

h1("14. Model evaluation")
names = list(tm)
hi = 1 + names.index(sel)
table([["Model", "MAE", "MSE", "RMSE", "R²", "MAPE %"]] + [[n + (" ★" if n == sel else ""), f2(vm[n]["MAE"]), f1(vm[n]["MSE"]), f2(vm[n]["RMSE"]), f3(vm[n]["R2"]), f1(vm[n]["MAPE"])] for n in names],
      [5.6, 2, 2.2, 2, 2, 2.4], "Validation metrics, Rs lakhs (used for model selection; ★ = selected)", size=9.5, highlight=hi, right_from=1)
table([["Model", "MAE", "MSE", "RMSE", "R²", "MAPE %"]] + [[n + (" ★" if n == sel else ""), f2(tm[n]["MAE"]), f1(tm[n]["MSE"]), f2(tm[n]["RMSE"]), f3(tm[n]["R2"]), f1(tm[n]["MAPE"])] for n in names],
      [5.6, 2, 2.2, 2, 2, 2.4], "Test metrics, Rs lakhs (final, untouched data)", size=9.5, highlight=hi, right_from=1)
figure("fig11_model_comparison.png", 16, "Model performance on the test set")
figure("fig13_actual_vs_predicted.png", 15, "Actual versus predicted price, " + sel)
h2("Residual analysis")
para("Residual = actual price − predicted price, so a positive residual means the model **underestimates** the price and a negative residual means it **overestimates** it.")
figure("fig12_residuals.png", 16, "Residuals versus predicted price, residual distribution and Q-Q plot")
table([["Model", "Mean residual", "Std", "Within Rs 5 lakhs", "Within Rs 10 lakhs", "Tendency"]] + [[r_["model"], f"{r_['mean_residual']:+.2f}", f2(r_["std"]), f"{r_['within_5']:.1f}%", f"{r_['within_10']:.1f}%", r_["tendency"]] for r_ in MD["residual_summary"]],
      [4.6, 2.3, 1.6, 2.6, 2.8, 2.5], "Residual summary on the test set (lakhs)", size=9, right_from=1)
band = {b["band"]: b for b in MD["residual_by_price_band"]}; loc = {b["Location_Type"]: b for b in MD["residual_by_location"]}
para(f"For {sel} the mean residual is {rs['mean']:+.2f} lakhs, so it **underestimates** prices slightly on average (about {rs['mean'] / S['price']['mean'] * 100:.1f}% of the mean price). The pattern depends on price level: low-priced houses are "
     f"overestimated (mean residual {band['Low-priced']['mean_residual']:+.1f}), mid-priced ones are close to unbiased ({band['Mid-priced']['mean_residual']:+.1f}) and high-priced ones are underestimated ({band['High-priced']['mean_residual']:+.1f}), the usual pull of predictions towards the average. "
     f"By location the mean residual is {loc['Urban']['mean_residual']:+.1f} (Urban), {loc['Suburban']['mean_residual']:+.1f} (Suburban) and {loc['Rural']['mean_residual']:+.1f} (Rural), with similar percentage errors ({loc['Urban']['mape']:.1f}%, {loc['Suburban']['mape']:.1f}%, {loc['Rural']['mape']:.1f}%). "
     f"{rs['within_5']:.0f}% of predictions fall within Rs 5 lakhs and {rs['within_10']:.0f}% within Rs 10 lakhs. The largest over-prediction was Rs {f1(rs['max_over'])} lakhs and the largest under-prediction Rs {f1(rs['max_under'])} lakhs. "
     f"The residuals are centred near zero, show no strong curve against the predicted price, and are consistent with a normal distribution (Shapiro-Wilk p = {rs['shapiro_p']:.2f}); their spread grows a little for expensive houses.")

h1("15. Results and discussion")
para(f"**{MD['n_beat_baseline']} of {MD['n_learned']} learned models beat the mean baseline**, and the selected {sel} is best on both validation and test data (test RMSE Rs {f2(tm[sel]['RMSE'])} lakhs against Rs {f2(tm['Mean baseline']['RMSE'])} lakhs for the baseline). "
     f"Simple regression on area alone ({f3(tm['Simple Linear Regression']['R2'])}) is much weaker than the multiple model ({f3(tm[sel]['R2'])}), so location, rooms, age, distance and neighbourhood add a lot of information. "
     f"Random forest (R² {f3(tm['Random Forest']['R2'])}) and gradient boosting ({f3(tm['Gradient Boosting']['R2'])}) did not outperform the linear model.")
para("This result is expected for this dataset: the prices were generated from a linear pricing rule with multiplicative noise, so the linear model matches the true process and tree ensembles can only approximate it "
     "with the 700 training houses available. On real housing data, where relationships are curved and features interact, ensembles often do better, so this ranking should not be assumed to transfer. "
     "The statistical findings (location effect, size effect, correlations) recover the structure that was built into the data, which confirms that the methods work as intended.")
para("Selection by validation RMSE is deliberate: using the test set to choose the model would make the reported test score optimistic. With a single random split of 150 test houses, small differences between models should not be over-interpreted.")

h1("16. Limitations")
for b in ["The dataset is synthetic; the results demonstrate the methods and do not describe a real housing market.",
          "Missing values were filled with medians computed on the whole dataset before splitting, a small leakage that would be avoided in production by fitting the imputer on training data only.",
          "A single random split was used; k-fold cross-validation of all models would give more reliable comparisons.",
          "The linear model assumes additive effects; real prices may involve interactions (for example, area matters more in Urban areas) and curvature.",
          "Prices were modelled in rupees, not log-rupees; the residual spread grows slightly for expensive houses.",
          "Predictors such as neighbourhood rating are subjective and may themselves reflect price."]: bullet(b)
h1("17. Future enhancements")
for b in ["Repeat the analysis on real listings (for example the Ames, Iowa or a city-specific dataset) and compare with these results.",
          "Model the logarithm of price, and add interaction terms such as area × location.", "Use k-fold cross-validation, ridge and lasso regression, and feature selection.",
          "Add geographic features (latitude and longitude, distance to schools and transport).", "Provide prediction intervals and deploy a small web application for price estimates."]: bullet(b)

h1("18. Conclusion")
para(f"The project delivered a complete, reproducible analysis of {P['clean_rows']:,} house records. The statistics quantified how price varies with location, size and condition; the hypothesis test showed that Urban houses cost significantly more than Suburban houses; "
     f"correlation analysis identified area, bedrooms and bathrooms as the strongest factors; and the NumPy implementation showed that gradient descent reproduces the least-squares solution. "
     f"On unseen test data the selected {sel} achieved MAE = Rs {f2(tm[sel]['MAE'])} lakhs, RMSE = Rs {f2(tm[sel]['RMSE'])} lakhs and R² = {f3(tm[sel]['R2'])}. "
     f"Because the data are synthetic, the main lesson is methodological: a careful split, an honest baseline and residual analysis matter as much as the choice of algorithm.")

h1("19. References")
refs = ["Breiman, L. (2001). Random forests. *Machine Learning*, 45(1), 5-32.",
        "De Cock, D. (2011). Ames, Iowa: Alternative to the Boston Housing Data as an End of Semester Regression Project. *Journal of Statistics Education*, 19(3).",
        "Friedman, J. H. (2001). Greedy function approximation: A gradient boosting machine. *Annals of Statistics*, 29(5), 1189-1232.",
        "Harris, C. R., et al. (2020). Array programming with NumPy. *Nature*, 585, 357-362.",
        "Harrison, D., & Rubinfeld, D. L. (1978). Hedonic housing prices and the demand for clean air. *Journal of Environmental Economics and Management*, 5(1), 81-102.",
        "Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. *Computing in Science & Engineering*, 9(3), 90-95.",
        "McKinney, W. (2010). Data structures for statistical computing in Python. *Proceedings of the 9th Python in Science Conference*, 56-61.",
        "Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research*, 12, 2825-2830.",
        "Rosen, S. (1974). Hedonic prices and implicit markets: Product differentiation in pure competition. *Journal of Political Economy*, 82(1), 34-55.",
        "Virtanen, P., et al. (2020). SciPy 1.0: fundamental algorithms for scientific computing in Python. *Nature Methods*, 17, 261-272.",
        "Welch, B. L. (1947). The generalization of 'Student's' problem when several different population variances are involved. *Biometrika*, 34(1-2), 28-35."]
for i, rf in enumerate(refs, 1):
    p = doc.add_paragraph(); p.paragraph_format.left_indent = Cm(0.9); p.paragraph_format.first_line_indent = Cm(-0.9); p.paragraph_format.space_after = Pt(4)
    p.add_run(f"[{i}] ")
    for k, part in enumerate(rf.split("*")):
        if part: rr = p.add_run(part); rr.italic = k % 2 == 1

out = ROOT / "reports/House_Price_Prediction_Report.docx"
doc.save(out); print("saved", out)
subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(out.parent), str(out)], capture_output=True)
print("pdf:", (out.parent / "House_Price_Prediction_Report.pdf").exists())
