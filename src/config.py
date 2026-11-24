"""Shared settings for the House Price Prediction project."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"
FIGS = RESULTS / "figures"
TABLES = RESULTS / "tables"

SEED = 42
N_HOUSES = 1000
HIGH_PRICE = 100.0     # "high-priced house" = price above Rs 100 lakhs (Rs 1 crore)
BIG_AREA = 1500        # "large house" = area above 1500 sq ft
ALPHA = 0.05

NUMERIC = ["Area_sqft", "Bedrooms", "Bathrooms", "Age_years",
           "Distance_to_City_km", "Neighborhood_Rating", "Parking_Spaces"]
CATEGORICAL = ["Location_Type", "Furnishing"]
TARGET = "Price_Lakhs"

# colours (same family as the reference weather report)
NAVY, BLUE, ORANGE, GREEN, GREY, RED = "#16365C", "#22608F", "#E07B1F", "#2E8B57", "#6B7280", "#C0392B"
LOC_COLORS = {"Urban": BLUE, "Suburban": ORANGE, "Rural": GREEN}

for p in (DATA, FIGS, TABLES):
    p.mkdir(parents=True, exist_ok=True)
