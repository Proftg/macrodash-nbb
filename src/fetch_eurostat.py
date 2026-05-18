"""
Client pour l'API Eurostat.

stat.nbb.be/sdmx-json est hors service depuis mars 2026.
On utilise Eurostat qui publie les mêmes séries macro belges
via une API JSON gratuite et sans inscription.

Doc officielle : https://ec.europa.eu/eurostat/web/main/data/web-services

Le format JSON Eurostat est un tableau N-dimensionnel aplati.
Chaque observation est identifiée par un indice calculé avec des strides :
  stride[i] = prod(size[i+1:])
  dim_idx[i] = (flat_index // stride[i]) % size[i]
"""
import time
from pathlib import Path

import pandas as pd
import requests

from src.config import DATASETS, DATA_RAW, EUROSTAT_BASE


class EurostatClient:
    """Accès à l'API Eurostat SDMX-JSON."""

    def __init__(self, timeout: int = 30):
        self.session = requests.Session()
        self.session.headers.update(
            {"Accept": "application/json", "User-Agent": "MacroDash-NBB/1.0"}
        )
        self.timeout = timeout

    def get_raw(
        self,
        code: str,
        geo: str | None = "BE",
        start: str | None = "2010",
        end: str | None = None,
        **extra,
    ) -> dict:
        """Requête brute vers l'API Eurostat, retourne le dict JSON."""
        params: dict = {"format": "JSON"}
        if geo:
            params["geo"] = geo
        if start:
            params["startPeriod"] = start
        if end:
            params["endPeriod"] = end
        params.update(extra)

        r = self.session.get(
            f"{EUROSTAT_BASE}/{code}", params=params, timeout=self.timeout
        )
        r.raise_for_status()
        return r.json()

    def parse(self, data: dict) -> pd.DataFrame:
        """
        Convertit une réponse JSON Eurostat en DataFrame pandas.

        Eurostat encode les données sous forme d'un tableau aplati.
        On reconstruit les indices de chaque dimension via les strides,
        puis on mappe chaque position sur son code de catégorie.
        """
        id_order = data.get("id", [])
        sizes = data.get("size", [])
        dims = data.get("dimension", {})
        vals = data.get("value", {})

        if not id_order or not vals:
            return pd.DataFrame()

        n = len(id_order)
        strides = [1] * n
        for i in range(n - 2, -1, -1):
            strides[i] = strides[i + 1] * sizes[i + 1]

        lookups: dict[str, dict[int, str]] = {}
        for dim in id_order:
            idx_map = dims.get(dim, {}).get("category", {}).get("index", {})
            lookups[dim] = {v: k for k, v in idx_map.items()}

        rows = []
        for pos_str, val in vals.items():
            pos = int(pos_str)
            row: dict = {}
            for i, dim in enumerate(id_order):
                dim_idx = (pos // strides[i]) % sizes[i]
                row[dim] = lookups[dim].get(dim_idx, str(dim_idx))
            row["valeur"] = val
            rows.append(row)

        df = pd.DataFrame(rows)
        if "time" in df.columns:
            df = df.rename(columns={"time": "periode"})
        if "periode" in df.columns:
            df = df.sort_values("periode").reset_index(drop=True)
        df["valeur"] = pd.to_numeric(df["valeur"], errors="coerce")
        return df

    def fetch_series(
        self,
        key: str,
        start: str = "2010",
        end: str | None = None,
    ) -> pd.DataFrame:
        """
        Récupère et filtre une série définie dans config.DATASETS.
        Retourne un DataFrame à deux colonnes : periode et valeur.

        Les filtres de dimensions (sex, age, unit...) ne sont pas passés
        en query params car l'API Eurostat retourne 400 sur certains d'entre eux.
        On les applique en pandas après avoir parsé la réponse complète.
        """
        cfg = DATASETS[key]
        raw = self.get_raw(cfg["code"], geo=cfg["geo"], start=start, end=end)
        df = self.parse(raw)
        if df.empty:
            return df

        # Appliquer les filtres de dimensions sur le DataFrame
        for col, val in cfg["filters"].items():
            if col in df.columns:
                df = df[df[col] == val]

        if df.empty:
            return df

        # S'il reste plusieurs valeurs par période, on prend la moyenne
        dim_cols = [c for c in df.columns if c not in ("periode", "valeur")]
        if dim_cols:
            df = df.groupby("periode")["valeur"].mean().reset_index()

        return df[["periode", "valeur"]].dropna()

    def fetch_all(
        self,
        start: str = "2010",
        end: str | None = None,
        cache: bool = True,
    ) -> dict[str, pd.DataFrame]:
        """
        Récupère toutes les séries du catalogue.
        Avec cache=True, chaque série est sauvegardée en CSV dans data/raw/.
        """
        results: dict[str, pd.DataFrame] = {}
        for key in DATASETS:
            try:
                df = self.fetch_series(key, start=start, end=end)
                if not df.empty:
                    results[key] = df
                    if cache:
                        path = DATA_RAW / f"{key}.csv"
                        df.to_csv(path, index=False)
                        print(f"  {key:<15} {len(df):>4} obs  -> {path.name}")
                    else:
                        print(f"  {key:<15} {len(df):>4} obs")
                else:
                    print(f"  {key:<15} vide")
                time.sleep(0.5)
            except requests.HTTPError as e:
                print(f"  {key:<15} HTTP {e.response.status_code}")
            except Exception as e:
                print(f"  {key:<15} Erreur : {e}")
        return results

    @staticmethod
    def load_cached() -> dict[str, pd.DataFrame]:
        """Charge les CSVs depuis data/raw/ pour éviter les appels API répétés."""
        results: dict[str, pd.DataFrame] = {}
        for key in DATASETS:
            path = DATA_RAW / f"{key}.csv"
            if path.exists():
                results[key] = pd.read_csv(path)
        return results
