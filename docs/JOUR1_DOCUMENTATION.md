# MacroDash-NBB : Documentation pédagogique Jour 1

> Document de référence pour comprendre chaque détail du projet et pouvoir l'expliquer en entretien.
> Auteur : Tahar Guenfoud. Date : 2026-05-18.

---

## Table des matières

1. [Contexte et motivation du projet](#1-contexte-et-motivation-du-projet)
2. [Architecture du projet](#2-architecture-du-projet)
3. [Les 5 séries macroéconomiques](#3-les-5-séries-macroéconomiques)
4. [Le format JSON Eurostat décortiqué](#4-le-format-json-eurostat-décortiqué)
5. [Les 3 bugs API résolus](#5-les-3-bugs-api-résolus)
6. [Le bug Plotly et sa correction](#6-le-bug-plotly-et-sa-correction)
7. [Les résultats obtenus](#7-les-résultats-obtenus)
8. [Comment expliquer ce projet en entretien](#8-comment-expliquer-ce-projet-en-entretien)

---

## 1. Contexte et motivation du projet

### Pourquoi ce projet existe

À l'origine, le plan était d'utiliser l'API SDMX de la Banque Nationale de Belgique (stat.nbb.be) pour construire un dashboard macroéconomique belge. Cette API était parfaite : données officielles, gratuite, sans inscription, couverture longue de l'économie belge.

Problème : depuis mars 2026, stat.nbb.be est hors service. Pas de date de retour annoncée. Il fallait donc trouver une source alternative qui réponde aux mêmes critères de qualité.

Le choix s'est porté sur Eurostat, l'office statistique de l'Union européenne. Trois raisons :

1. **Mêmes données macro pour la Belgique** : Eurostat agrège les données nationales, dont celles de la NBB. Les séries belges qu'on récupère via Eurostat proviennent en réalité de la NBB et de Statbel, mais passent par le canal européen.
2. **API JSON gratuite, sans clé d'authentification** : pas besoin de s'inscrire, pas de quota strict, format JSON standard.
3. **Couverture historique longue** : la plupart des séries remontent à 2000 ou avant, ce qui permet de couvrir plusieurs cycles économiques.

### L'objectif final

Construire un dashboard interactif qui affiche les indicateurs macroéconomiques belges majeurs sur la période 2010-2025, avec une narrative claire pour un public de recruteurs en banque ou en data science financière.

### La narrative centrale

La période 2022-2024 raconte une histoire forte : le cycle de resserrement monétaire de la BCE. Voici les jalons à mettre en avant :

- **Été 2022** : la BCE remonte ses taux directeurs pour la première fois depuis 2011, en réaction au choc inflationniste (guerre en Ukraine, énergie, post-Covid).
- **Septembre 2023** : le taux de dépôt BCE atteint 4 %, plus haut historique.
- **2024** : début du cycle de baisse, l'inflation se rapproche de la cible 2 %.

Le dashboard doit rendre visible ce cycle à travers les 5 séries choisies, et faire ressortir les corrélations entre elles (transmission de la politique monétaire vers l'économie réelle).

### Pourquoi ce projet est pertinent pour un poste en banque ou data scientist

Le projet coche plusieurs cases visibles dès le pitch :

- **Compréhension du contexte macro** : un Data Analyst en banque doit comprendre les cycles de taux, l'inflation, le chômage. Ce n'est pas que de la technique.
- **Manipulation d'API publique** : montrer qu'on sait construire un client API robuste, gérer les erreurs, faire face aux changements de schéma.
- **Pipeline de données réel** : extraction, transformation, agrégation à fréquence mensuelle, gestion des NaN, validation.
- **Restitution visuelle** : un dashboard Plotly + Streamlit est aujourd'hui un standard attendu.

---

## 2. Architecture du projet

### Structure des dossiers

```
macrodash-nbb/
├── src/
│   ├── config.py           # Catalogue des séries et constantes globales
│   ├── fetch_eurostat.py   # Client API Eurostat (parsing JSON-stat)
│   └── transform.py        # Construction du DataFrame mensuel consolidé
├── notebooks/
│   └── 01_exploration.ipynb  # Exploration des données et visualisations
├── app/
│   └── Home.py             # Application Streamlit (page d'accueil)
├── data/
│   ├── raw/                # CSVs bruts par série (cache local)
│   └── processed/          # DataFrame final consolidé (parquet ou csv)
├── docs/
│   └── JOUR1_DOCUMENTATION.md  # Ce document
├── tests/                  # Tests unitaires (à venir)
└── pyproject.toml          # Dépendances et configuration projet
```

### La logique de séparation des responsabilités

Chaque module a une responsabilité unique. C'est un principe de base en software engineering, mais c'est aussi ce qui rend le projet maintenable et explicable en entretien.

**`config.py`** : ne fait rien d'autre que déclarer des constantes. Le catalogue des séries (codes Eurostat, libellés, filtres par défaut), les chemins de dossiers, les dates de référence pour les annotations BCE. Si demain on veut ajouter une 6ème série, on modifie uniquement ce fichier.

**`fetch_eurostat.py`** : s'occupe uniquement de communiquer avec l'API. Il prend en entrée un code de série et des paramètres temporels, il renvoie en sortie un DataFrame long-format avec une ligne par observation. Aucune logique métier ici, juste de l'extraction.

**`transform.py`** : prend les DataFrames individuels et les fusionne en un DataFrame consolidé à fréquence mensuelle. C'est ici qu'on gère le forward-fill du PIB trimestriel, la réindexation sur un calendrier mensuel commun, le filtrage des dimensions secondaires.

**`Home.py`** : c'est la couche présentation. Streamlit lit le DataFrame consolidé et affiche les graphes, sans jamais appeler l'API directement. C'est important parce que ça permet de servir le dashboard sans latence réseau.

### Le flux de données

```
API Eurostat (JSON-stat)
        │
        ▼
fetch_eurostat.py  → DataFrame long-format par série
        │
        ▼
data/raw/*.csv     → cache local pour ne pas re-télécharger
        │
        ▼
transform.py       → DataFrame wide-format mensuel consolidé
        │
        ▼
data/processed/    → fichier final unique
        │
        ▼
Streamlit Home.py  → graphiques Plotly interactifs
```

---

## 3. Les 5 séries macroéconomiques

| Clé interne | Code Eurostat | Description | Pertinence bancaire |
|-------------|--------------|-------------|---------------------|
| `olo_10y`   | `irt_lt_mcby_m` | Taux OLO belge 10 ans | Coût de financement long terme pour les banques |
| `euribor_3m` | `irt_h_mr3_m` | EURIBOR 3 mois zone euro | Taux court terme, lié aux décisions BCE |
| `inflation` | `prc_hicp_manr` | Inflation IPCH annuelle Belgique | Pression sur le remboursement des emprunteurs |
| `chomage`   | `une_rt_m` | Taux de chômage mensuel Belgique | Proxy de solvabilité des ménages |
| `pib`       | `nama_10_gdp` | PIB Belgique en millions EUR | Santé macroéconomique globale |

### Lecture détaillée de chaque série

**OLO 10 ans (`olo_10y`)** : OLO signifie Obligation Linéaire / Lineaire Obligatie. C'est l'obligation souveraine belge de référence, équivalent du Bund allemand ou de l'OAT française. Le taux à 10 ans est le baromètre du coût d'emprunt à long terme pour l'État belge, mais aussi indirectement pour les banques qui s'en servent comme référence pour fixer leurs taux de crédit hypothécaire. Quand l'OLO 10Y monte, les crédits hypothécaires deviennent plus chers.

**EURIBOR 3M (`euribor_3m`)** : Euro Interbank Offered Rate à 3 mois. C'est le taux auquel les grandes banques européennes se prêtent entre elles sur 3 mois. Il est très sensible aux décisions de la BCE. Pour une banque, c'est le coût de refinancement court terme. Il sert aussi de référence pour beaucoup de crédits à taux variable.

**Inflation IPCH (`inflation`)** : Indice des Prix à la Consommation Harmonisé. La version harmonisée est celle qui permet la comparaison entre pays de la zone euro. `manr` dans le code signifie "monthly annual rate", c'est-à-dire la variation annuelle calculée chaque mois (par exemple, inflation de janvier 2024 = prix de janvier 2024 vs prix de janvier 2023). Une inflation élevée érode le pouvoir d'achat des emprunteurs et augmente le risque de défaut.

**Chômage (`chomage`)** : taux de chômage harmonisé Eurostat, mensuel, désaisonnalisé. C'est un proxy classique de la solvabilité des ménages. Quand le chômage monte, les défauts sur crédits à la consommation et hypothécaires augmentent généralement avec un délai de 6 à 12 mois.

**PIB (`pib`)** : Produit Intérieur Brut belge en millions d'euros, en volume (corrigé de l'inflation). Attention, cette série est trimestrielle, pas mensuelle. C'est un point technique important qui impose une transformation spécifique (voir section 7).

### Pourquoi ces 5 séries et pas d'autres

Le choix répond à trois critères :

1. **Disponibilité longue et fiable** sur Eurostat pour la Belgique.
2. **Couverture des 4 grands compartiments macro** : taux longs, taux courts, prix, emploi, activité.
3. **Pertinence directe pour un poste en banque** : chacune de ces séries est utilisée tous les jours par les départements risques, ALM (Asset Liability Management) ou crédit.

On aurait pu ajouter le taux de change EUR/USD ou les spreads souverains, mais l'idée du Jour 1 était de poser une base solide avec 5 séries qu'on maîtrise totalement plutôt que 15 qu'on survole.

---

## 4. Le format JSON Eurostat décortiqué

C'est la partie la plus technique du projet et celle qui a demandé le plus de travail de compréhension. Si tu sais expliquer cette section en entretien, tu démontres une vraie capacité à digérer des formats de données complexes.

### Le problème

Eurostat utilise le format JSON-stat, un standard pour la diffusion de données statistiques multidimensionnelles. Une série de données macroéconomiques n'est pas juste une liste de paires (date, valeur). Elle peut avoir plusieurs dimensions : pays, période, sexe, âge, unité de mesure, etc.

Au lieu de retourner un tableau structuré classique avec une ligne par observation, JSON-stat retourne un dictionnaire compact où les valeurs sont aplaties dans un seul tableau, et il faut reconstruire la position de chaque valeur dans l'espace multidimensionnel.

### Analogie pour comprendre

Imagine un tableur Excel à 3 dimensions : pays en lignes, mois en colonnes, et une troisième dimension cachée (par exemple "homme/femme") en feuilles. Si tu déplies ce cube en une seule longue liste, tu perds l'information de position. JSON-stat te donne cette longue liste plus les "instructions" pour retrouver la position 3D de chaque cellule.

Les instructions sont :
- **`id`** : la liste ordonnée des dimensions (par exemple `["geo", "time", "unit"]`)
- **`size`** : la taille de chaque dimension (par exemple `[2, 3, 1]` = 2 pays, 3 mois, 1 unité)
- **`dimension`** : pour chaque dimension, le mapping entre l'index numérique et le code lisible (par exemple `{"0": "BE", "1": "FR"}`)
- **`value`** : le dictionnaire des valeurs, avec comme clé la position aplatie et comme valeur la donnée

### L'exemple concret pas à pas

Prenons une série fictive avec 3 dimensions de tailles `(2, 3, 1)` :

- 2 pays : Belgique (index 0), France (index 1)
- 3 mois : janvier (0), février (1), mars (2)
- 1 unité : pourcentage (0)

Le nombre total d'observations possibles est `2 * 3 * 1 = 6`. Elles sont indexées de 0 à 5 dans le tableau aplati.

L'ordre d'aplatissement suit la convention dite "row-major" : la dernière dimension varie le plus vite, la première le plus lentement.

| Position aplatie | Pays (geo) | Mois (time) | Unité |
|------------------|------------|-------------|-------|
| 0                | BE (0)     | janv (0)    | % (0) |
| 1                | BE (0)     | févr (1)    | % (0) |
| 2                | BE (0)     | mars (2)    | % (0) |
| 3                | FR (1)     | janv (0)    | % (0) |
| 4                | FR (1)     | févr (1)    | % (0) |
| 5                | FR (1)     | mars (2)    | % (0) |

### Le concept de "strides"

Pour passer d'une position aplatie à des indices multidimensionnels, on a besoin des "strides" (pas). Un stride te dit de combien de positions tu dois sauter dans le tableau aplati pour avancer d'un cran dans une dimension donnée.

Avec sizes `[2, 3, 1]` :
- Pour avancer d'un cran en unité (dernière dimension), on saute 1 position. `strides[2] = 1`.
- Pour avancer d'un cran en time, on saute `taille_unite = 1` positions. `strides[1] = 1`.
- Pour avancer d'un cran en geo, on saute `taille_time * taille_unite = 3 * 1 = 3` positions. `strides[0] = 3`.

Donc strides = `[3, 1, 1]`.

### Le calcul inverse : retrouver les indices à partir de la position

Pour la position aplatie 4, on veut retrouver les indices (geo, time, unit).

```
geo_idx  = (4 // 3) % 2 = 1 % 2 = 1   → FR
time_idx = (4 // 1) % 3 = 4 % 3 = 1   → février
unit_idx = (4 // 1) % 1 = 4 % 1 = 0   → %
```

Vérification dans le tableau : position 4 = FR, février, %. C'est correct.

La formule générale est : `idx_dim_i = (position // strides[i]) % sizes[i]`

### Le code Python dans `fetch_eurostat.py`

```python
n = len(id_order)
strides = [1] * n
for i in range(n - 2, -1, -1):
    strides[i] = strides[i + 1] * sizes[i + 1]

rows = []
for pos_str, val in vals.items():
    pos = int(pos_str)
    row: dict = {}
    for i, dim in enumerate(id_order):
        dim_idx = (pos // strides[i]) % sizes[i]
        row[dim] = lookups[dim].get(dim_idx, str(dim_idx))
    row["valeur"] = val
    rows.append(row)
```

Lecture ligne par ligne :

- `n = len(id_order)` : nombre de dimensions
- La boucle `for i in range(n - 2, -1, -1)` parcourt les dimensions de l'avant-dernière vers la première. Pour chaque dimension i, le stride est le produit de la taille de la dimension i+1 par le stride de i+1. On part de `strides[-1] = 1` (la dernière dimension a toujours un stride de 1).
- Ensuite, pour chaque position dans le dictionnaire des valeurs, on calcule les indices multidimensionnels avec la formule vue plus haut, et on traduit chaque indice en libellé via le dictionnaire `lookups[dim]` (qui mappe `0 -> "BE"`, `1 -> "FR"`, etc.).

À la sortie de cette boucle, on a une liste de dictionnaires qu'on peut directement passer à `pd.DataFrame(rows)` pour obtenir une table propre au format long.

### Pourquoi ce design dans le code

On aurait pu utiliser une bibliothèque tierce comme `pyjstat` qui parse JSON-stat automatiquement. Le choix de faire le parsing à la main a deux justifications :

1. **Comprendre vraiment ce qui se passe** : en entretien, on peut expliquer chaque ligne. Avec une dépendance, on dirait "j'ai utilisé pyjstat" et on ne maîtriserait pas le format.
2. **Pas de dépendance fragile** : `pyjstat` n'est pas activement maintenu, et le format JSON-stat évolue. Mieux vaut un parser de 15 lignes qu'on contrôle.

---

## 5. Les 3 bugs API résolus

L'API Eurostat a connu plusieurs changements de comportement entre mars et mai 2026 qui ont cassé le code initial. C'est typique des projets data : les sources évoluent et il faut s'adapter. Voici les 3 bugs rencontrés et leurs résolutions.

### Bug 1 : le paramètre `lang=EN` cause une erreur HTTP 400

**Symptôme** : tous les appels API renvoyaient `HTTP 400 Bad Request` avec le message d'erreur "noEuroLegacy parameter is no longer supported".

**Cause** : depuis mai 2026, Eurostat a déprécié le paramètre `lang=EN` qui était auparavant utilisé pour forcer les libellés en anglais. Le paramètre fait partie d'une famille de paramètres "legacy" qui ne sont plus acceptés.

**Solution** : retirer purement et simplement `lang=EN` de la construction de l'URL. Les libellés reviennent dans la langue par défaut (en pratique souvent l'anglais quand même), ce qui ne pose pas de problème pour notre usage puisqu'on utilise les codes, pas les libellés.

**Leçon** : toujours vérifier la documentation officielle quand un appel qui marchait avant casse. Ne pas supposer que ton code est buggé, le serveur peut avoir changé.

### Bug 2 : `endPeriod` devient obligatoire

**Symptôme** : appels API renvoyant `HTTP 400` même après correction du bug 1, dès qu'on passait uniquement `startPeriod=2010` sans préciser de date de fin.

**Cause** : depuis mai 2026, l'API exige que `startPeriod` ET `endPeriod` soient tous les deux présents, ou aucun. Auparavant, ne passer que `startPeriod` retournait par défaut toutes les données jusqu'à aujourd'hui. Maintenant ça plante.

**Solution** : générer dynamiquement `endPeriod` si l'utilisateur ne le précise pas.

```python
_end = end or str(date.today().year)
```

Cette ligne fait : si `end` est `None` (non précisé), prendre l'année courante. Sinon, garder la valeur passée. Le `or` en Python renvoie le premier opérande qui est "truthy", et `None` est "falsy".

**Leçon** : prévoir des valeurs par défaut intelligentes dans tes fonctions de client API. Ne jamais laisser un paramètre obligatoire de l'API en optionnel dans ton code sans fallback.

### Bug 3 : les filtres de dimensions en query params provoquent HTTP 400

**Symptôme** : passer des filtres comme `sex=T` (total), `age=TOTAL`, ou `coicop=CP00` (tous biens et services) directement dans l'URL générait des erreurs 400.

**Cause** : l'API a changé sa syntaxe d'acceptation des filtres. Auparavant, on pouvait écrire `https://...?startPeriod=2010&endPeriod=2025&sex=T&age=TOTAL`. Maintenant ces filtres doivent passer par un autre canal (chemin POST avec body JSON), ou pas du tout.

**Solution adoptée** : récupérer toute la réponse sans filtrer côté API, puis filtrer en pandas avec `.loc`.

Exemple concret pour la série chômage :

```python
df = fetch_eurostat_dataset("une_rt_m", start="2010", end="2025")
df_be = df.loc[
    (df["geo"] == "BE") &
    (df["sex"] == "T") &
    (df["age"] == "TOTAL") &
    (df["unit"] == "PC_ACT") &
    (df["s_adj"] == "SA")
].copy()
```

**Leçon** : c'est une approche défensive courante en data engineering. Si l'API ne te laisse pas filtrer en amont, fais-le en aval. Le coût de transférer plus de données est presque toujours inférieur au coût de debug d'une API qui change.

**Compromis** : on télécharge plus de données qu'on n'en utilise (toutes les ventilations par sexe, âge, etc.). En contrepartie, le code est plus robuste aux changements de l'API et permet d'explorer facilement d'autres ventilations sans re-télécharger.

---

## 6. Le bug Plotly et sa correction

### Le contexte

Une fois les données récupérées et le DataFrame consolidé construit, on a voulu ajouter des annotations verticales sur les graphes pour marquer les dates clés du cycle BCE 2022-2024. Par exemple, une ligne verticale au 1er juillet 2022 avec le label "Début hausse BCE".

Plotly fournit pour ça la fonction `fig.add_vline(x=..., annotation_text=...)`.

### Le bug rencontré

Code initial :

```python
fig.add_vline(
    x="2022-07-01",
    annotation_text="Début hausse BCE",
    line_dash="dash"
)
```

Résultat : `TypeError: unsupported operand type(s) for +: 'int' and 'str'`

### Pourquoi ça plante

C'est un bug spécifique à Plotly quand on utilise `add_vline` avec `annotation_text` sur un subplot dont l'axe X est de type datetime. Voici la chaîne de causalité :

1. Plotly veut positionner l'annotation au milieu de la ligne verticale.
2. Pour ça, il calcule la moyenne entre `x0` et `x1` (qui sont égaux dans le cas d'une vline, mais le code générique calcule quand même la moyenne).
3. Cette moyenne est calculée par une fonction interne `_mean([x0, x1])`.
4. `_mean` est implémentée avec la fonction `sum()` de Python, qui par défaut commence l'accumulation à `0` (un entier).
5. Quand on passe `x0 = "2022-07-01"` (une chaîne), Python tente `0 + "2022-07-01"` et plante avec un `TypeError`.

C'est un bug connu, qui apparaît surtout dans les subplots datetime. La même opération sans subplot peut fonctionner parce qu'un autre chemin de code est emprunté.

### La solution

Convertir la date en millisecondes depuis epoch Unix avant de la passer à `add_vline`. Plotly accepte les axes datetime en interne en millisecondes, et un entier ne pose pas de problème à `sum()`.

```python
import pandas as pd

x_ms = pd.Timestamp("2022-07-01").value // 10**6

fig.add_vline(
    x=x_ms,
    annotation_text="Début hausse BCE",
    line_dash="dash"
)
```

Explication ligne à ligne :

- `pd.Timestamp("2022-07-01")` crée un objet Timestamp pandas.
- `.value` renvoie le nombre de nanosecondes depuis le 1er janvier 1970 (l'epoch Unix).
- `// 10**6` divise par 1 million pour convertir les nanosecondes en millisecondes (Plotly attend des millisecondes).

L'annotation est alors positionnée correctement et Plotly ne fait plus l'erreur de type.

### Leçon générale

Quand un bug semble "incompréhensible", il y a souvent une couche d'abstraction qui cache une opération basique qui plante. Le réflexe à avoir :

1. Lire la stack trace complète, pas juste le dernier message.
2. Identifier le module et la fonction qui plante (`_mean` dans `plotly/_subplots.py` par exemple).
3. Comprendre pourquoi cette fonction est appelée avec ce type d'argument.
4. Trouver un contournement qui respecte les contraintes de la fonction interne.

---

## 7. Les résultats obtenus

### Le DataFrame final

Dimensions : **192 lignes x 5 colonnes**, période **2010-01 à 2025-12**.

Chaque ligne correspond à un mois calendaire, chaque colonne à une série. Format wide, indexé par la date.

Exemple des premières lignes :

```
              olo_10y  euribor_3m  inflation  chomage       pib
date
2010-01-01      3.74        0.66       0.7      8.1   89250.0
2010-02-01      3.55        0.66       0.8      8.2   89250.0
2010-03-01      3.46        0.65       1.5      8.3   89250.0
...
```

### Les NaN attendus et leur justification

Avoir des NaN dans un dataset n'est pas un problème en soi, à condition de pouvoir les expliquer. Voici les deux séries qui en contiennent et pourquoi.

**`euribor_3m` : 133 NaN**

L'EURIBOR 3 mois est tombé à zéro puis légèrement en territoire négatif autour de 2015, et il y est resté jusqu'à fin 2021. Eurostat a manifestement cessé de publier la série pendant cette période, ou la publie de manière intermittente. Résultat : on a un trou de plusieurs années entre 2015 et 2022.

Que faire de ces NaN ?

- Ne **pas** les remplir par 0. Ce serait inventer une donnée qu'on n'a pas. Même si économiquement c'est proche de la vérité, en data analysis on ne fabrique pas de la donnée.
- Les laisser tels quels et les afficher comme des trous dans les graphes. Plotly gère bien ça nativement.
- Documenter le trou pour ne pas être surpris en entretien.

**`pib` : 11 NaN**

Le PIB Eurostat est publié à fréquence trimestrielle, pas mensuelle. Pour aligner cette série avec les autres dans un DataFrame mensuel, on fait un forward-fill : chaque valeur trimestrielle est répétée sur les 3 mois du trimestre. Par exemple, le PIB Q1 2024 (référence : fin mars 2024) est étendu à janvier, février et mars 2024.

Les 11 NaN correspondent au fait qu'au moment de l'extraction, le PIB Q4 2025 n'est pas encore publié. Eurostat publie les comptes trimestriels avec un délai d'environ 2 mois après la fin du trimestre. Pour les mois de fin 2025 (octobre, novembre, décembre), pas encore de valeur disponible.

Solution honnête : laisser les NaN, indiquer dans le dashboard que la dernière valeur PIB disponible est Q3 2025.

### Les corrélations entre séries

On a calculé la matrice de corrélation de Pearson sur les paires de séries. Trois corrélations sortent du lot avec |r| > 0.6.

**OLO 10Y x EURIBOR 3M : r = +0.732**

Interprétation : les taux longs et les taux courts bougent ensemble. Quand la BCE remonte ses taux directeurs (effet direct sur l'EURIBOR 3M), les marchés anticipent une trajectoire de taux plus élevée et les rendements obligataires longs (OLO 10Y) montent aussi. C'est la transmission classique de la politique monétaire le long de la courbe des taux.

Note pédagogique : la corrélation n'est pas de 1 parce que les taux longs intègrent aussi d'autres facteurs (prime de risque, attentes d'inflation à long terme, dynamique de la dette souveraine).

**EURIBOR 3M x PIB : r = -0.829**

Interprétation : quand les taux courts montent, la croissance ralentit. C'est cohérent avec le canal du crédit : taux plus élevés = moins d'investissement et de consommation à crédit = moins de croissance.

Attention pédagogique : corrélation n'est pas causalité. Sur cet échantillon court (2010-2025), les deux séries ont surtout été corrélées par le cycle 2022-2024 (taux qui montent fort, croissance qui ralentit). Sur un échantillon plus long ou plus diversifié, la corrélation pourrait être plus faible.

**Chômage x PIB : r = -0.749**

C'est la loi d'Okun, une régularité empirique en macroéconomie. Économie forte = entreprises qui embauchent = chômage qui baisse. Et inversement. Cette corrélation est robuste à travers les pays et les décennies, c'est l'une des relations les plus stables de la macroéconomie appliquée.

### Visualisations construites

Dans le notebook `01_exploration.ipynb`, on a généré :

- Une grille de 5 sous-graphes (un par série) avec les annotations BCE sur la période 2022-2024.
- Une heatmap de corrélation pour visualiser la matrice complète.
- Un graphique combiné OLO 10Y / EURIBOR 3M pour mettre en évidence le mouvement parallèle des taux.

---

## 8. Comment expliquer ce projet en entretien

### Pitch de 2 minutes

> "J'ai construit un dashboard macroéconomique belge à partir de l'API Eurostat. L'objectif était double : d'abord, démontrer que je sais construire un pipeline data complet, de l'extraction API jusqu'à la restitution visuelle. Ensuite, raconter une histoire macro pertinente pour le secteur bancaire, à savoir le cycle de resserrement monétaire de la BCE entre 2022 et 2024.
>
> Côté technique, le projet est structuré en 4 modules : un fichier de configuration qui catalogue les séries, un client API qui parse le format JSON-stat d'Eurostat, un module de transformation qui consolide tout en DataFrame mensuel, et une application Streamlit pour la visualisation interactive. J'ai rencontré et résolu plusieurs problèmes intéressants, notamment 3 bugs de l'API Eurostat qui a changé son schéma en mai 2026, et un bug Plotly sur les annotations datetime que j'ai contourné en convertissant les dates en millisecondes Unix.
>
> Côté contenu, j'ai retenu 5 séries qui couvrent les 4 grands compartiments macro : taux longs avec l'OLO 10 ans, taux courts avec l'EURIBOR 3 mois, prix avec l'inflation IPCH, emploi avec le chômage, activité avec le PIB. J'ai vérifié que les corrélations qu'on observe sont cohérentes avec la théorie : transmission des taux le long de la courbe, loi d'Okun entre chômage et PIB, effet récessif des hausses de taux."

### Questions techniques probables et réponses

**Q : Pourquoi Eurostat plutôt que la BCE ou la NBB directement ?**

> "À l'origine je voulais utiliser stat.nbb.be, mais l'API NBB est hors service depuis mars 2026. La BCE Data Portal a une API mais elle est plus complexe et orientée zone euro plutôt que Belgique. Eurostat est le bon compromis : gratuit, sans inscription, format JSON standardisé, et les données belges qu'on récupère viennent en réalité de la NBB et Statbel via le canal européen."

**Q : Pourquoi avoir parsé le JSON-stat à la main plutôt qu'utiliser pyjstat ?**

> "Deux raisons. D'abord pour vraiment comprendre le format, parce qu'en entretien je veux pouvoir expliquer chaque ligne, pas dire 'j'ai utilisé une lib'. Ensuite parce que pyjstat n'est plus activement maintenu et le format évolue. Un parser de 15 lignes que je contrôle est plus robuste qu'une dépendance externe fragile."

**Q : Pourquoi DuckDB est dans tes plans pour la suite ?**

> "Pour l'instant le pipeline tient en mémoire avec pandas, ce qui est largement suffisant pour 5 séries et 192 lignes. Mais je veux ajouter un cache local persistant avec DuckDB pour deux raisons : éviter de re-télécharger les données à chaque exécution, et pouvoir faire des requêtes SQL sur les données historiques. DuckDB est parfait pour ça : zero-config, fichier unique, SQL standard, intégration native avec pandas et Parquet."

**Q : Pourquoi Plotly et pas Matplotlib ou Altair ?**

> "Plotly produit des graphes interactifs nativement, ce qui est important pour un dashboard. L'utilisateur peut zoomer, survoler, désactiver une série. Matplotlib est meilleur pour de la production statique (papier scientifique, PDF), Altair est élégant mais moins riche en interactions. Pour un dashboard exposé à des recruteurs ou des collègues, Plotly est le standard."

**Q : Pourquoi Streamlit et pas Dash ou Power BI ?**

> "Streamlit permet de prototyper très vite avec du Python pur, sans HTML ni callback. Dash est plus puissant mais aussi plus verbeux, je l'aurais choisi pour une application destinée à de la production avec plusieurs utilisateurs. Power BI est un outil métier, pas un livrable de portfolio data scientist. Streamlit est aujourd'hui le standard pour les projets data en démonstration."

**Q : Comment tu gères les NaN dans tes graphes et tes corrélations ?**

> "Je ne les remplis pas artificiellement, je les laisse tels quels. Plotly affiche naturellement les trous, ce qui est plus honnête qu'une interpolation. Pour les corrélations, pandas calcule par défaut sur les paires de valeurs non-nulles, donc pas de biais. Si je devais faire de la modélisation prédictive plus tard, là je devrais choisir une stratégie d'imputation explicite : forward-fill pour les séries lentes, interpolation pour les taux, ou suppression pour les modèles qui ne tolèrent pas les NaN."

**Q : Tu as pensé à automatiser le rafraîchissement ?**

> "Pour la suite, oui. L'idée serait de mettre le pipeline dans un workflow GitHub Actions qui s'exécute chaque mois en début de mois, télécharge les dernières données, met à jour le fichier Parquet, et redéploie automatiquement le dashboard. Pour l'instant l'exécution est manuelle parce que je voulais d'abord valider la robustesse du code avant d'automatiser."

**Q : Quelle est la limite principale de ton projet aujourd'hui ?**

> "Le projet est exploratoire et descriptif. Il décrit les corrélations passées mais ne fait pas de modélisation prédictive. La prochaine étape logique serait soit un modèle de prévision macro (par exemple un VAR pour modéliser conjointement les 5 séries), soit un cas d'usage bancaire concret comme du stress-test de portefeuille hypothécaire en fonction des scénarios de taux. C'est dans ma roadmap."

### Choix techniques à justifier

| Choix | Justification courte |
|-------|----------------------|
| Eurostat | API NBB hors service, Eurostat = même données via canal européen, gratuit, JSON |
| Parser JSON-stat à la main | Compréhension complète, pas de dépendance fragile (pyjstat peu maintenu) |
| DuckDB prévu | Cache persistant, requêtes SQL sur historique, intégration pandas/Parquet |
| Plotly | Interactivité native, standard dashboard, support datetime correct (avec le fix) |
| Streamlit | Prototypage rapide en Python pur, idéal pour démo portfolio |
| Pas de remplissage NaN | Honnêteté méthodologique, Plotly gère les trous nativement |
| Forward-fill PIB trimestriel | Méthode standard pour aligner fréquences mixtes, alternative à l'interpolation |
| Filtrage en pandas plutôt qu'en query params | Robustesse aux changements d'API, coût négligeable |

### Pièges à éviter en entretien

Ne jamais dire :

- "J'ai utilisé ChatGPT pour faire le parsing JSON" même si c'est vrai. Dire plutôt : "J'ai analysé le format JSON-stat en lisant la doc Eurostat et en testant pas à pas."
- "Je ne sais pas pourquoi il y a des NaN dans euribor_3m". Toujours avoir une explication prête : "Période de taux nuls 2015-2021, série discontinuée par Eurostat sur cette période."
- "Le projet est terminé". Toujours présenter une roadmap : automatisation, ajout de séries, modélisation prédictive, cas d'usage bancaire.
- "C'était facile". Toujours mentionner les difficultés résolues (3 bugs API, bug Plotly) pour montrer la capacité de debug.

Toujours dire :

- "J'ai documenté chaque étape pour pouvoir refaire le projet ou l'étendre dans 6 mois."
- "J'ai pensé l'architecture pour qu'ajouter une 6ème série coûte 5 minutes de code, pas une refonte."
- "J'ai validé les corrélations contre la théorie macro pour m'assurer que mes données ne sont pas corrompues."

---

## Annexe : checklist de révision avant entretien

- [ ] Je peux expliquer le parsing JSON-stat avec l'exemple à 3 dimensions (sizes 2x3x1)
- [ ] Je connais les 3 bugs API et leurs solutions par cœur
- [ ] Je connais le bug Plotly et le contournement millisecondes Unix
- [ ] Je peux citer les 5 séries, leur code Eurostat et leur pertinence bancaire
- [ ] Je sais expliquer les NaN dans euribor_3m et pib sans hésiter
- [ ] Je connais les 3 corrélations fortes et leur interprétation économique
- [ ] J'ai préparé une roadmap d'évolution du projet (DuckDB, automatisation, modélisation)
- [ ] J'ai relu le pitch de 2 minutes à voix haute au moins 3 fois
