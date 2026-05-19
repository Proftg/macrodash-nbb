"""
Persistance du DataFrame macro dans DuckDB.

Pourquoi DuckDB plutôt qu'un simple CSV ?
- Requêtes SQL directes sur l'historique (filtres, agrégations)
- Lecture partielle sans charger tout en mémoire
- Format binaire plus rapide que CSV sur de grands volumes
- Base de données locale, zéro configuration, fichier unique

Le fichier est stocké dans data/processed/macro.duckdb.
La table principale s'appelle macro_monthly.
"""
import duckdb
import pandas as pd

from src.config import DATA_PROCESSED

DB_PATH = DATA_PROCESSED / "macro.duckdb"


def save(macro: pd.DataFrame) -> None:
    """
    Sauvegarde le DataFrame macro dans DuckDB.

    Remplace la table si elle existe déjà (CREATE OR REPLACE).
    Le DatetimeIndex 'date' devient une colonne DATE dans la table.
    """
    if macro.empty:
        print("DataFrame vide : rien à sauvegarder.")
        return

    df = macro.reset_index()  # date passe de l'index à une colonne
    df["date"] = df["date"].dt.date  # Timestamp -> date Python (type DATE en DuckDB)

    with duckdb.connect(str(DB_PATH)) as con:
        con.execute("CREATE OR REPLACE TABLE macro_monthly AS SELECT * FROM df")

    print(f"DuckDB : {len(df)} lignes sauvegardées dans {DB_PATH.name}")


def load() -> pd.DataFrame:
    """
    Charge la table macro_monthly depuis DuckDB.

    Retourne un DataFrame avec le même format que build_macro_df :
    DatetimeIndex mensuel nommé 'date', une colonne par série.
    Retourne un DataFrame vide si la base n'existe pas encore.
    """
    if not DB_PATH.exists():
        return pd.DataFrame()

    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        df = con.execute("SELECT * FROM macro_monthly ORDER BY date").df()

    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")
    df.index.name = "date"
    return df


def query(sql: str) -> pd.DataFrame:
    """
    Exécute une requête SQL arbitraire sur la base et retourne un DataFrame.

    Exemples utiles :
        query("SELECT * FROM macro_monthly WHERE date >= '2022-01-01'")
        query("SELECT date, olo_10y, inflation FROM macro_monthly ORDER BY date DESC LIMIT 12")
        query("SELECT AVG(inflation) FROM macro_monthly WHERE date >= '2020-01-01'")
    """
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Base DuckDB introuvable : {DB_PATH}")

    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        return con.execute(sql).df()


def info() -> None:
    """Affiche un résumé de la table stockée : colonnes, plage temporelle, NaN."""
    if not DB_PATH.exists():
        print("Aucune base DuckDB trouvée.")
        return

    with duckdb.connect(str(DB_PATH), read_only=True) as con:
        df = con.execute("SELECT * FROM macro_monthly ORDER BY date").df()

    print(f"Table    : macro_monthly")
    print(f"Lignes   : {len(df)}")
    print(f"Période  : {df['date'].min()} -> {df['date'].max()}")
    print(f"Colonnes : {list(df.columns)}")
    print(f"NaN par colonne :")
    print(df.isna().sum().to_string())
