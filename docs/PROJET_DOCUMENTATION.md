# MacroDash-NBB : documentation pédagogique complète

Document de référence pour Tahar Guenfoud.
Objectif : comprendre chaque aspect du projet et savoir l'expliquer en entretien sans hésiter.

---

## Table des matières

1. [Pourquoi ce projet a été choisi](#partie-1--pourquoi-ce-projet-a-été-choisi)
2. [Description technique complète](#partie-2--description-technique-complète)
3. [Impact sur la recherche d'emploi](#partie-3--impact-sur-la-recherche-demploi)
4. [Guide d'explication en entretien](#partie-4--guide-dexplication-en-entretien)

---

## PARTIE 1 : pourquoi ce projet a été choisi

### Le contexte de départ

Tu postules pour des postes Data Analyst et Data Scientist en Belgique. Tes cibles principales sont les banques (KBC, BNP Paribas Fortis, Belfius, ING) et la Banque Nationale de Belgique. Tu as déjà un portfolio solide côté ferroviaire avec Infrabel (dashboard ponctualité, blackspots, vérification probabiliste PRISM). Mais tu n'avais aucun projet à orientation bancaire ou financière. Ton CV racontait une histoire incomplète pour un recruteur de banque.

Tu avais identifié l'API stat.nbb.be comme source idéale. Problème : elle est hors service depuis mars 2026. Sans alternative, le projet ne décollait pas. Tu as trouvé qu'Eurostat publie exactement les mêmes données macro belges, gratuitement, avec une API REST documentée. Le projet est devenu faisable.

### Pourquoi ce projet est stratégique pour ta recherche d'emploi

**1. Il prouve que tu comprends les mécanismes macro suivis quotidiennement par les banques.**

Une banque vit de l'écart entre les taux auxquels elle emprunte et ceux auxquels elle prête. Les équipes risque surveillent l'inflation, le chômage, le marché immobilier parce que ces variables déterminent la solvabilité des emprunteurs et la valeur des collatéraux. En montrant que tu sais nommer ces séries, les croiser et les interpréter, tu signales que tu n'es pas un candidat purement technique qui découvrira le métier sur place.

**2. Il démontre un pipeline data complet de bout en bout.**

Beaucoup de candidats juniors ont des notebooks Kaggle. Très peu ont un pipeline qui ingère une API externe complexe, transforme des fréquences hétérogènes, persiste dans une base et expose via une web app déployée. C'est exactement la chaîne que tu manipuleras dans un poste Data Analyst en banque.

**3. Il existe en ligne avec un lien cliquable.**

Le dashboard est accessible à https://macrodashnbb.streamlit.app/. Tu mets ce lien sur ton CV et ton LinkedIn. Un recruteur clique, voit le résultat en dix secondes, et tu passes devant 80 % des candidats qui n'ont que des captures d'écran.

**4. La narrative temporelle est forte.**

La période 2022-2024 (cycle BCE de hausse puis baisse des taux) est la plus analysée actuellement par les équipes risque et ALM des banques belges. C'est aussi celle qui a fait basculer le portefeuille immobilier de plusieurs banques en provisions. Annoter ces événements sur les graphiques montre que tu sais raconter une histoire à partir des chiffres, pas juste afficher des courbes.

**5. Tu te différencies des profils Kaggle.**

Le projet n'est pas un Titanic ou un House Prices. C'est une chaîne de production qui ressemble à un livrable professionnel. Pour un recruteur, c'est la différence entre un exercice d'école et un travail de junior opérationnel.

---

## PARTIE 2 : description technique complète

### Structure du projet

```
macrodash-nbb/
├── src/
│   ├── config.py           # Catalogue des 6 séries et constantes
│   ├── fetch_eurostat.py   # Client API Eurostat (parsing JSON-stat)
│   ├── transform.py        # Alignement fréquences mixtes vers mensuel
│   └── persist.py          # Stockage DuckDB
├── app/
│   └── Home.py             # Application Streamlit
├── notebooks/
│   └── 01_exploration.ipynb
├── data/
│   ├── raw/                # Cache CSV (gitignore)
│   └── processed/          # DataFrame final et base DuckDB (gitignore)
└── .streamlit/config.toml  # Thème clair
```

Chaque fichier a une responsabilité unique. C'est l'inverse d'un notebook fourre-tout. Si un recruteur regarde le repo, il voit immédiatement où chercher.

### Les 6 séries de données

| Clé | Code Eurostat | Description | Fréquence | Pertinence bancaire |
|-----|--------------|-------------|-----------|---------------------|
| olo_10y | irt_lt_mcby_m | OLO belge 10 ans | Mensuelle | Coût de financement long terme |
| euribor_3m | irt_h_mr3_m | EURIBOR 3M | Mensuelle (2010-2014 seulement) | Taux court terme BCE |
| inflation | prc_hicp_manr | Inflation IPCH annuelle | Mensuelle | Pression sur le remboursement |
| chomage | une_rt_m | Taux de chômage | Mensuelle | Solvabilité des emprunteurs |
| pib | nama_10_gdp | PIB Belgique MEUR | Trimestrielle | Santé macroéconomique |
| prix_immo | ei_hppi_q | Prix immobiliers (%YoY) | Trimestrielle | Valeur du collatéral hypothécaire |

Ce choix de six séries n'est pas neutre. Chacune correspond à un indicateur que tu retrouveras dans un rapport ALM ou un comité risque. Tu peux justifier chaque ligne du tableau face à un manager métier.

### Le format JSON-stat d'Eurostat (la partie la plus complexe)

Eurostat ne renvoie pas un CSV propre. Le format JSON-stat retourne un tableau N-dimensionnel aplati en une seule liste de valeurs, plus des métadonnées qui décrivent comment reconstruire la position de chaque cellule.

**L'analogie simple :** imagine un tableur Excel 3D (temps x pays x catégorie). Quelqu'un déplie ce cube en une longue ligne unique de valeurs et te donne séparément une notice qui dit "la cellule numéro 1247 correspond à : année 2023, pays Belgique, catégorie hommes". Ton travail, c'est d'écrire le code qui lit la notice et reconstruit la grille.

**La mécanique technique :** on utilise des strides, c'est-à-dire le pas à appliquer pour chaque dimension.

```
strides[i] = strides[i+1] * sizes[i+1]
dim_idx   = (position // strides[i]) % sizes[i]
```

Cette reconstruction est implémentée dans `fetch_eurostat.py`. C'est exactement le même principe que NumPy utilise en interne pour stocker des arrays multidimensionnels en mémoire contiguë. Tu peux donc dire en entretien que tu as manipulé concrètement le concept de strides, ce que peu de candidats juniors savent expliquer.

### Les 3 bugs API que tu as résolus

Ces bugs ne sont pas documentés clairement par Eurostat. Tu les as identifiés en lisant les réponses HTTP et en testant. C'est une compétence très valorisée.

**Bug 1 : `lang=EN` renvoie HTTP 400.**
Le paramètre `lang` a été déprécié dans la nouvelle version de l'API en mai 2026. Solution : supprimer le paramètre.

**Bug 2 : `endPeriod` est devenu obligatoire.**
Sans date de fin, l'API renvoie HTTP 400 depuis mai 2026. Solution : toujours passer `endPeriod` même quand on veut "toutes les données récentes".

**Bug 3 : les filtres de dimensions en query params font échouer la requête.**
Si on passe `sex=T` ou `age=TOTAL` dans l'URL, HTTP 400. Solution : récupérer toutes les dimensions, puis filtrer en pandas après le téléchargement. Moins élégant mais robuste.

En entretien, ces trois bugs sont parfaits pour répondre à la question "raconte-moi un problème technique que tu as résolu".

### Le bug Plotly (annotation_text sur subplot datetime)

Sur les subplots avec un axe temporel, `add_vline(x="2022-07-01", annotation_text="...")` plantait avec une `TypeError`. La cause profonde : Plotly calcule en interne `sum([x0, x1])` pour positionner l'annotation, et `sum()` commence son accumulateur à 0 (un int). L'opération `0 + "2022-07-01"` est invalide en Python.

**Solution :** convertir la date en millisecondes Unix avant de la passer à Plotly.
```python
ts_ms = pd.Timestamp(date_str).value // 10**6
```

Cas typique de bug "internal library" : tu n'as pas écrit le code fautif, mais tu as creusé jusqu'à la cause racine. C'est exactement ce qu'un senior fait au quotidien.

### Le module DuckDB (`persist.py`)

DuckDB est une base SQL en colonnes, embarquée comme SQLite, mais optimisée pour l'analytique. Le fichier `persist.py` expose quatre fonctions :

- `save(macro)` : écrit le DataFrame final dans la base
- `load()` : recharge tout en DataFrame
- `query(sql)` : exécute du SQL standard et renvoie un DataFrame
- `info()` : métadonnées (nb de lignes, plage de dates)

**Pourquoi DuckDB plutôt que CSV ou SQLite :**
- Fichier unique, zéro serveur, zéro configuration
- SQL standard complet (window functions, CTE, etc.)
- Intégration native pandas (`con.execute(sql).df()`)
- Beaucoup plus rapide que CSV sur des requêtes filtrées car stockage colonne
- Très utilisé en 2025-2026 dans les stacks data modernes (Motherduck, dbt)

**L'analogie :** DuckDB est à l'analytique ce que SQLite est aux applis mobiles. Une base pro complète, mais en un seul fichier portable.

### Résultats de l'analyse (corrélations Pearson 2010-2025)

| Couple | r | Lecture économique |
|--------|---|---------------------|
| OLO 10Y x EURIBOR 3M | +0,73 | Taux longs et courts bougent ensemble |
| EURIBOR 3M x PIB | -0,83 | Taux hauts freinent la croissance |
| Chômage x PIB | -0,75 | Loi d'Okun confirmée |
| OLO 10Y x Prix immobiliers | -0,30 | Taux hauts pèsent sur l'immobilier |

Tu peux commenter chaque corrélation avec une justification économique, pas juste lire la valeur. C'est le signal recherché par un recruteur banque : un Data Analyst qui parle métier.

### Événements BCE annotés

Trois moments charnières marqués sur les graphiques :

- Juillet 2022 : BCE +0,5 %, début du cycle de hausse après une décennie de taux nuls
- Septembre 2023 : pic à 4,5 %, fin du cycle de hausse
- Juin 2024 : BCE -0,25 %, premier signal de baisse

Ces trois dates sont celles que toute personne en banque connaît par cœur. Les annoter sur ton dashboard montre que tu lis l'actualité économique.

### Dashboard Streamlit déployé

URL live : https://macrodashnbb.streamlit.app/

Fonctionnalités :
- 4 KPIs en haut (dernière valeur de chaque série principale)
- Multiselect pour choisir les séries à afficher
- Slider de plage temporelle
- Toggle pour activer ou non les annotations BCE
- Matrice de corrélation repliable
- Thème clair défini dans `.streamlit/config.toml`

L'interface est volontairement sobre. Pas d'effet, pas de surcharge. C'est l'esprit "dashboard de salle de marché".

---

## PARTIE 3 : impact sur la recherche d'emploi

### Ce que ce projet prouve à un recruteur banque

**Sur le plan technique :**
- Tu sais consommer une API REST publique, gérer ses bugs et ses cas limites
- Tu sais transformer et aligner des données à fréquences hétérogènes (mensuel, trimestriel)
- Tu sais persister proprement avec une base moderne (DuckDB)
- Tu sais déployer une web app accessible publiquement
- Tu sais documenter ton code et structurer un repo

**Sur le plan métier :**
- Tu connais les indicateurs macro suivis par une banque (taux, inflation, chômage, immobilier)
- Tu sais relier ces indicateurs aux préoccupations bancaires (collatéral, solvabilité, ALM)
- Tu sais lire l'actualité BCE et l'inscrire dans une analyse
- Tu sais interpréter des corrélations sans les confondre avec de la causalité

### Postes pour lesquels ce projet est particulièrement pertinent

| Poste | Pourquoi ce projet colle |
|-------|--------------------------|
| Data Analyst junior banque | Pipeline complet + indicateurs macro = cœur du métier DA en banque |
| Data Scientist Risque | Variables macro = inputs des modèles de risque de crédit |
| ALM Analyst | Suivi des taux longs et courts = quotidien d'un analyste ALM |
| Model Validation | Démonstration que tu comprends les inputs des modèles |
| Data Analyst NBB | Données macro = mission première de la NBB |
| Data Analyst secteur public | Pipelines reproductibles + visualisation = livrable type |

### Comment positionner le projet selon l'interlocuteur

**Face à un recruteur technique (data engineer, lead DS) :**
Insister sur le pipeline. JSON-stat, strides, DuckDB, Streamlit, gestion des bugs API. Montrer le repo, expliquer l'architecture en couches (fetch / transform / persist / app). Parler des choix d'outils et pourquoi tu les as faits.

**Face à un recruteur RH :**
Rester sur le résultat visible. "J'ai construit un dashboard accessible en ligne qui suit six indicateurs macro belges. Voici le lien." Insister sur l'autonomie, l'initiative (l'API NBB hors service, tu as pivoté vers Eurostat tout seul), et le fait que le projet est en production.

**Face à un manager métier (chef d'équipe risque, ALM, économiste) :**
Parler indicateurs et interprétation. Pourquoi tu as choisi ces six séries, comment tu lis les corrélations, ce que les annotations BCE racontent. Ne pas survendre la technique. Le manager veut savoir si tu sauras dialoguer avec son équipe.

### Ce que ce projet apporte que les autres projets n'apportent pas

- Infrabel-dashboard : montre la maîtrise data viz, mais secteur ferroviaire
- Blackspots Infrabel : montre la maîtrise géospatiale, mais secteur ferroviaire
- railway-delay-ml : montre la maîtrise ML, mais secteur ferroviaire et tu ne le mentionnes pas en entretien Infrabel
- infrabel-delay-verification : montre la rigueur méthodologique (PRISM, PCTL), mais secteur ferroviaire

MacroDash-NBB est le seul projet qui couvre l'angle bancaire et financier. C'est la pièce manquante pour candidater en banque sans avoir l'air d'un transfuge ferroviaire.

### Les 5 choses à dire en entretien sur ce projet

1. "L'API stat.nbb.be est hors service depuis mars 2026, j'ai pivoté vers Eurostat qui publie les mêmes séries. Cette capacité à dérisquer une dépendance externe est un réflexe que je transposerai en poste."

2. "J'ai choisi six séries qui correspondent à ce qu'une banque suit au quotidien : taux longs, taux courts, inflation, chômage, PIB, immobilier. Chaque série est justifiée par un cas d'usage métier."

3. "Le pipeline est en quatre couches : ingestion, transformation, persistance DuckDB, visualisation Streamlit. C'est le découpage que je retrouverais dans une équipe data en production."

4. "Le dashboard est en ligne, accessible en cliquant sur le lien sur mon CV. Vous pouvez le tester maintenant si vous voulez."

5. "Les annotations BCE sur les graphiques racontent une histoire concrète : début de cycle juillet 2022, pic septembre 2023, retournement juin 2024. C'est la période que vos équipes risque ont le plus analysée."

### Les 3 choses à ne jamais dire

1. **"C'était un projet pour apprendre Streamlit."**
Faux registre. Le projet n'est pas un exercice, c'est un livrable. Présente-le comme tel.

2. **"J'ai utilisé l'IA pour debug les bugs API."**
Même si c'est vrai en partie, le recruteur retient "il sait pas debugger seul". Dis plutôt que tu as identifié les bugs en lisant les réponses HTTP et la doc Eurostat.

3. **"J'aurais aimé faire un modèle prédictif mais j'ai manqué de temps."**
Ne t'excuse jamais de ce que le projet n'est pas. Présente ce qui est là. Si on te demande "et après ?", parle d'une suite réfléchie (par exemple : ajouter un modèle de prédiction de défaut en combinant ces variables macro avec un dataset UCI Credit).

---

## PARTIE 4 : guide d'explication en entretien

### Pitch de 2 minutes

"J'ai construit un dashboard macroéconomique belge appelé MacroDash-NBB. L'idée de départ était d'utiliser l'API de la Banque Nationale, mais elle est hors service depuis mars 2026. J'ai donc pivoté vers l'API Eurostat, qui publie les mêmes séries pour la Belgique.

Le projet ingère six indicateurs : l'OLO 10 ans, l'EURIBOR 3 mois, l'inflation IPCH, le chômage, le PIB et l'indice des prix immobiliers. Ces six séries couvrent les variables qu'une banque suit au quotidien pour piloter son risque de crédit et son ALM.

Côté technique, c'est un pipeline en quatre couches. Une couche fetch qui parse le format JSON-stat d'Eurostat, une couche transform qui aligne des fréquences mensuelles et trimestrielles, une couche persist qui stocke en DuckDB, et une web app Streamlit déployée en ligne.

J'ai identifié et corrigé trois bugs dans l'API Eurostat (changements d'API non documentés en mai 2026) et un bug Plotly sur les annotations de subplots datetime.

Le résultat est en ligne, le lien est sur mon CV. Les corrélations entre les séries confirment des relations économiques classiques : taux hauts contre PIB à -0,83, loi d'Okun chômage contre PIB à -0,75. J'ai annoté les trois moments BCE clés du cycle 2022-2024."

### Questions probables et réponses

**Q : Pourquoi DuckDB plutôt que PostgreSQL ou CSV ?**
R : CSV ne supporte pas les requêtes SQL filtrées efficacement. PostgreSQL aurait demandé un serveur à déployer pour un usage analytique mono-utilisateur. DuckDB me donne du SQL standard, du stockage colonne rapide, et un fichier unique portable. C'est l'outil adapté à la taille du dataset et au cas d'usage.

**Q : Pourquoi Eurostat et pas une API plus directe ?**
R : La NBB héberge ses données sur stat.nbb.be, mais cette API est hors service depuis mars 2026. Eurostat agrège les mêmes statistiques nationales pour tous les pays européens, dont la Belgique. C'est une source officielle, gratuite, stable et documentée.

**Q : Le format JSON-stat, c'est quoi exactement ?**
R : C'est un format standard pour les données statistiques officielles. L'idée est de représenter un tableau multidimensionnel (temps, géographie, catégorie) sous forme aplatie, plus des métadonnées qui décrivent comment retrouver les indices de chaque dimension. Concrètement, j'ai implémenté la reconstruction par strides, le même principe que NumPy en interne.

**Q : Pourquoi six séries et pas plus ?**
R : Chaque série a un cas d'usage bancaire identifié. Au-delà, on ajoute du bruit sans valeur d'analyse. C'est mieux d'avoir six indicateurs justifiés que vingt mal compris.

**Q : Comment validerais-tu que les chiffres sont corrects ?**
R : Trois contrôles. Premièrement, recouper la dernière valeur avec le site public Eurostat. Deuxièmement, vérifier que les corrélations connues sont cohérentes (Okun, taux contre PIB). Troisièmement, regarder les ruptures de série autour d'événements connus (mars 2020 Covid, juillet 2022 hausse BCE) pour voir si les données réagissent comme attendu.

**Q : Comment tu ferais évoluer le projet ?**
R : Trois pistes concrètes. Ajouter un modèle prédictif de défaut en combinant ces variables macro avec un dataset crédit (UCI Default Credit Card). Étendre à d'autres pays européens pour faire de la comparaison. Mettre en place un refresh automatique mensuel via GitHub Actions.

**Q : Tu as travaillé seul ou en équipe ?**
R : Seul, sur mon temps personnel. C'est un projet portfolio. Mais le découpage en couches et la doc rendent le code lisible par un autre développeur, c'est l'esprit que j'aurais en équipe.

### Analogies simples pour les parties techniques

**JSON-stat :** un tableur Excel 3D déplié en une seule liste, avec une notice qui explique comment retrouver chaque cellule.

**Strides :** le pas à appliquer pour passer d'une dimension à l'autre dans la liste aplatie. Exactement comme un index de bibliothèque qui dit "rayon 3, étagère 5, livre 12".

**DuckDB :** SQLite pour l'analytique. Un fichier unique, zéro serveur, mais avec du SQL puissant et un stockage colonne rapide.

**Streamlit :** un moyen de transformer un script Python en application web sans écrire de HTML ni de JavaScript. Tu écris des `st.line_chart(...)` et l'app se construit.

**Markov chains (pour la comparaison future avec le projet PRISM) :** un système qui passe d'un état à un autre avec des probabilités fixes, où le futur ne dépend que de l'état présent. Comme un train qui transite entre stations selon des probabilités de retard, sans se souvenir des stations précédentes.

### Mémo final

Si tu ne devais retenir que trois phrases :

1. "Pipeline data complet de l'API à la web app déployée, sur des données macro belges pertinentes pour une banque."
2. "Six indicateurs choisis pour leur usage bancaire concret, pas pour faire joli."
3. "Le dashboard est en ligne, vous pouvez le tester en cliquant sur le lien de mon CV."

Ces trois phrases couvrent technique, métier, et preuve. C'est tout ce dont tu as besoin pour ouvrir une discussion sur ce projet en entretien.
