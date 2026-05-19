from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"

DATA_RAW.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

# Catalogue des séries Eurostat utilisées dans le dashboard.
# Chaque clé est le nom interne utilisé dans le code et les CSVs.
DATASETS: dict[str, dict] = {
    "olo_10y": {
        "code": "irt_lt_mcby_m",
        "geo": "BE",
        "filters": {"int_rate": "ILM"},
        "label": "OLO 10 ans (%)",
        "unit": "%",
        "color": "#1a5276",
    },
    "euribor_3m": {
        "code": "irt_h_mr3_m",
        "geo": None,
        "filters": {},
        "label": "EURIBOR 3M (%)",
        "unit": "%",
        "color": "#c0392b",
    },
    "inflation": {
        "code": "prc_hicp_manr",
        "geo": "BE",
        "filters": {"coicop": "CP00", "unit": "RCH_A"},
        "label": "Inflation IPCH (%)",
        "unit": "%",
        "color": "#d35400",
    },
    "chomage": {
        "code": "une_rt_m",
        "geo": "BE",
        "filters": {"sex": "T", "age": "TOTAL", "unit": "PC_ACT"},
        "label": "Chomage (% actifs)",
        "unit": "% actifs",
        "color": "#6c3483",
    },
    "pib": {
        "code": "nama_10_gdp",
        "geo": "BE",
        "filters": {"na_item": "B1GQ", "unit": "CP_MEUR"},
        "label": "PIB Belgique (MEUR)",
        "unit": "MEUR",
        "color": "#1e8449",
    },
    "prix_immo": {
        "code": "ei_hppi_q",
        "geo": "BE",
        "filters": {"indic": "TOTAL", "unit": "RT4"},
        "label": "Prix immobilier (%YoY)",
        "unit": "% YoY",
        "color": "#148f77",
    },
}

# Dates clés du cycle BCE, utilisées pour annoter les graphiques.
BCE_EVENTS: list[tuple[str, str, str]] = [
    ("2020-03-01", "COVID", "#717d7e"),
    ("2022-07-01", "BCE +0.5%", "#c0392b"),
    ("2023-09-01", "Pic BCE 4.5%", "#c0392b"),
    ("2024-06-01", "BCE -0.25%", "#1e8449"),
]

EUROSTAT_BASE = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"
)
