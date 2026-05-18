"""
Nettoyage et alignement temporel des séries Eurostat.

Problématique fréquences mixtes :
  - Séries mensuelles (YYYY-MM)  : taux, inflation, chômage
  - Séries trimestrielles (YYYY-Qn) : PIB trimestriel
  - Séries annuelles (YYYY) : éventuellement

Stratégie : tout normaliser en DatetimeIndex mensuel (MS).
Le trimestriel et l'annuel sont convertis par forward-fill.
"""
import pandas as pd


def _detect_freq(df: pd.DataFrame) -> str:
    """Détecte la fréquence temporelle à partir de la colonne 'periode'."""
    if df.empty or "periode" not in df.columns:
        return "unknown"
    sample = df["periode"].dropna().head(5).tolist()
    if any("Q" in str(p) for p in sample):
        return "quarterly"
    if all(len(str(p)) == 4 for p in sample):
        return "annual"
    return "monthly"


def to_monthly(df: pd.DataFrame, name: str) -> pd.Series:
    """
    Convertit un DataFrame [periode, valeur] en Series DatetimeIndex mensuel.
    name → nom de la Series retournée (utilisé comme nom de colonne).
    """
    if df.empty:
        return pd.Series(dtype=float, name=name)

    freq = _detect_freq(df)
    s = df.set_index("periode")["valeur"].copy()

    if freq == "monthly":
        s.index = pd.to_datetime(s.index, format="%Y-%m", errors="coerce")
    elif freq == "quarterly":
        s.index = pd.PeriodIndex(s.index, freq="Q").to_timestamp()
        s = s.resample("MS").ffill()
    elif freq == "annual":
        s.index = pd.to_datetime(s.index, format="%Y", errors="coerce")
        s = s.resample("MS").ffill()
    else:
        s.index = pd.to_datetime(s.index, errors="coerce")

    s = s.dropna()
    s.name = name
    return s


def build_macro_df(series: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Assemble un dict {key: DataFrame[periode, valeur]} en un DataFrame
    multi-colonnes avec index DatetimeIndex mensuel.
    Sauvegarde dans data/processed/macro_monthly.csv.
    """
    from src.config import DATA_PROCESSED

    monthly = {k: to_monthly(df, k) for k, df in series.items() if not df.empty}
    if not monthly:
        return pd.DataFrame()

    macro = pd.concat(monthly.values(), axis=1).sort_index()
    macro.index.name = "date"

    out = DATA_PROCESSED / "macro_monthly.csv"
    macro.to_csv(out)
    return macro
