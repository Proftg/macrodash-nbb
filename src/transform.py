"""
Nettoyage et alignement temporel des séries Eurostat.

Les séries ont des fréquences différentes selon le dataset :
  - mensuel (YYYY-MM) : taux, inflation, chômage
  - trimestriel (YYYY-Qn) : PIB
  - annuel (YYYY) : cas rare

On normalise tout sur un index mensuel (MS) pour pouvoir assembler
les séries dans un seul DataFrame. Le trimestriel et l'annuel sont
convertis par forward-fill (chaque valeur trimestrielle est répétée
sur les 3 mois correspondants).
"""
import pandas as pd


def _detect_freq(df: pd.DataFrame) -> str:
    """Identifie la fréquence temporelle à partir de la colonne periode."""
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
    Convertit un DataFrame [periode, valeur] en Series avec index DatetimeIndex mensuel.
    Le paramètre name devient le nom de la Series retournée.
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
    Assemble un dict de DataFrames en un seul DataFrame multi-colonnes
    avec un index DatetimeIndex mensuel.
    Sauvegarde le résultat dans data/processed/macro_monthly.csv.
    """
    from src.config import DATA_PROCESSED

    monthly = {k: to_monthly(df, k) for k, df in series.items() if not df.empty}
    if not monthly:
        return pd.DataFrame()

    macro = pd.concat(monthly.values(), axis=1).sort_index()
    macro.index.name = "date"

    try:
        out = DATA_PROCESSED / "macro_monthly.csv"
        macro.to_csv(out)
    except OSError:
        pass  # filesystem read-only (ex. Streamlit Cloud) : on continue sans sauvegarder
    return macro
