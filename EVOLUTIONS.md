# Évolutions par rapport à la version préliminaire

Ce document trace les transformations apportées à la version de départ
d'IRaMuTeQ 0.8 alpha 7 (sources du portage Python 3 de mai 2020, commit
`ed38f79` « base version »). Les évolutions ont été réalisées en juillet
2026. Le cœur du logiciel (corpus, analyses, scripts R, interface
wxPython) n'a été modifié qu'à la marge : l'essentiel est constitué
d'ajouts autour de l'existant.

## 1. Ligne de commande : portage de `iracmd.py` en Python 3

*Commit `681d04c` — fichiers : `iracmd.py` (nouveau, à la racine),
`autres/iracmd.py` (supprimé), `README.md` (nouveau).*

Le harnais historique `autres/iracmd.py` (Python 2, chemins codés en dur,
API d'un état antérieur du code) a été réécrit pour le code Python 3 :

- mêmes options qu'à l'origine (`-f`, `-t`, `-c`, `-d`, `-e`, `-l`, `-r`,
  `-b`) via argparse ; analyses disponibles : `alceste`/`reinert`, `stat`,
  `spec`, `simitxt` (les types `pam` et `afcuci`, dont les modules ont
  disparu du code, ont été retirés) ;
- amorçage de `~/.iramuteq-<version>/` identique à la GUI (copie des
  fichiers de configuration et des dictionnaires, `history.db`,
  détection du binaire R écrite dans `path.cfg`, avec ajout des chemins
  macOS `/Library/Frameworks/R.framework` et `/opt/homebrew/bin/R`) ;
- exécution réellement sans fenêtre : les classes d'analyse créent des
  `wx.ProgressDialog` et un dialogue de rapport d'erreur sans condition ;
  `iracmd` les remplace à l'import par des objets neutres et journalise
  les erreurs R sur la console ;
- adaptations là où la GUI passe par un dialogue :
  - `spec` : les modalités comparées viennent du paramètre `etoiles`,
    par défaut la première variable étoilée du corpus (chaque texte ne
    doit porter qu'une modalité du jeu comparé) ;
  - `simitxt` : sélection par défaut des 200 formes actives les plus
    fréquentes (`max_actives_simi`), faute du dialogue de sélection ;
  - `stat` : paramètres pris dans `stat.cfg` (la GUI les demandait via
    un dialogue).

## 2. Ligne de commande : graphiques supplémentaires de la méthode Reinert

*Commit `92ae9b0` (partie CLI) — fichier : `iracmd.py`.*

- Après chaque classification, `iracmd` génère deux graphiques que la
  GUI ne produit qu'à la demande (boutons du panneau CHD) :
  `dendrogramme_texte_1.png` (profils des classes sur les feuilles du
  dendrogramme) et `dendrogramme_cloud_1.png` (nuages de mots par
  classe, paquet R `wordcloud` requis). Les mêmes appels R que la GUI
  sont utilisés (`plot.dendro.prof`, `plot.dendro.cloud`), avec un
  correctif pour le cas à 2 classes où `debsup`/`debet` ne sont pas
  présents dans `RData.RData`. `liste_graph_chd.txt` est mis à jour pour
  que ces images apparaissent aussi dans la GUI.
- L'AFC (`AFC2D*.png`, `afc_facteur/col/row.csv`) était déjà produite par
  le script R de profils dès que la classification retient plus de
  2 classes ; c'est documenté, et le paramètre `nbcl_p1` permet
  d'obtenir davantage de classes (validé sur le corpus de test : 2
  classes par défaut, 7 classes avec `nbcl_p1 = 20`).
- Changement de sémantique de `-c` : le fichier de configuration
  **surcharge** désormais les valeurs par défaut au lieu de les
  remplacer ; un `.cfg` minimal ne contenant que les paramètres modifiés
  est donc valide.

## 3. Explorateur web : couche de données et exécution (`iraexplorer/`)

*Commits `0913584` et suivants — fichiers : `iraexplorer/model.py`,
`iraexplorer/configs.py`, `iraexplorer/runner.py`,
`iraexplorer/__init__.py`.*

Un paquet indépendant, pensé pour être réutilisable derrière une API
(FastAPI...) : il ne dépend ni de wxPython, ni de Streamlit, ni du code
d'IRaMuTeQ (bibliothèque standard + pandas).

- `model.py` — chargement des résultats écrits sur disque : `Corpus`
  (Corpus.cira, bases SQLite ouvertes en lecture seule, variables
  étoilées, formes, segments) et `Analysis` (Analyse.ira + fichiers
  produits par R, dont un parseur du format en blocs de
  `profiles.csv`/`antiprofiles.csv`). Choix structurants :
  - **manifeste déclaratif** : chaque fichier attendu par type d'analyse
    est décrit (nom, rôle, format) dans `ANALYSIS_FILES` ;
  - **auditabilité** : chaque fichier garde chemin, taille, date, statut
    de lecture (`ok`/`missing`/`error` + message), empreinte SHA-256 à la
    demande ; les fichiers présents mais non répertoriés sont inventoriés ;
  - **tolérance** : un fichier manquant ou illisible ne fait jamais
    échouer le chargement ;
  - **sérialisation** : `to_dict()`/`to_json()` sur tous les objets.
- `configs.py` — lecture des paramètres par défaut
  (`~/.iramuteq-<version>/` sinon `configuration/`), aide contextuelle
  par paramètre, écriture de `.cfg` spécifiques compatibles
  `iracmd.py -c/-d`, construction des lignes de commande équivalentes.
- `runner.py` — enchaînement d'un calcul complet en sous-processus
  (construction du corpus `-b`, localisation du répertoire créé, puis
  chaque analyse en `-r`) ; chaque étape est consignée (commande exacte,
  horodatage, code retour, sorties) dans des objets `RunStep` et un
  fichier `run.log`, de quoi rejouer ou auditer un calcul a posteriori.

## 4. Explorateur web : interface Streamlit (`iraexplorer/app.py`)

*Commits `0913584` puis `92ae9b0` (refonte en projets).*

`streamlit run iraexplorer/app.py`. L'interface a d'abord été un
explorateur de répertoires de résultats avec un panneau « préparer une
analyse », puis a été réorganisée autour de la notion de **projet** :

- tous les projets vivent dans un dossier unique `projects/`
  (configurable) ; un projet est un dossier autoportant : fichier corpus
  copié dedans, **fichiers `.cfg` du calcul stockés dans le dossier du
  projet**, journal `run.log`, répertoires de résultats ;
- **page d'accueil** : liste des projets existants (corpus, analyses,
  date), bouton « créer une nouvelle analyse », ouverture d'un projet,
  suppression d'un projet avec confirmation ;
- **page de création** : dépôt ou chemin d'un corpus au format Alceste,
  langue/encodage, édition de tous les paramètres (import du corpus et
  chaque traitement choisi parmi alceste/stat/spec/simitxt), lancement du
  pipeline avec suivi étape par étape ;
- **vue projet** : une page par analyse —
  - Reinert : bilan `info.txt` mis en avant (métriques et taux de
    segments classés), poids des classes, dendrogrammes en onglets
    (simple, profils, nuages de mots, arbre CHD), AFC en onglets
    (4 plans + facteurs), profils par classe avec segments
    représentatifs, antiprofils ;
  - spécificités : scores par modalité (graphique divergent
    sur/sous-représentation), tables complètes, images d'AFC ;
  - similitudes : graphe, formes retenues ;
  - statistiques : résumé, fréquences, Zipf ;
  - page « nouveau traitement » pour relancer des calculs sur le corpus
    du projet, et suppression d'une analyse individuelle ;
- **audit sur chaque page** : inventaire des fichiers sources de la vue
  (chemin, taille, date, statut, SHA-256 optionnel) et export JSON de
  l'analyse ; les suppressions passent par des fonctions avec garde-fous
  (refus hors du dossier des projets ou sans `Analyse.ira`) ;
- compatibilité assurée entre les API Streamlit ≤ 1.48
  (`use_container_width`) et ≥ 1.49 (`width='stretch'`) ; graphiques
  Altair avec une palette fixe validée (une teinte pour les grandeurs,
  paire divergente pour les polarités, ordre catégoriel constant pour
  les classes).

## 5. Installation des dépendances

*Commit `718f910` — fichiers : `requirements.txt`, `install_deps.sh`.*

- `requirements.txt` : dépendances Python (wxPython et xlrd pour la
  GUI/CLI ; streamlit, pandas, altair pour l'explorateur web) ;
- `install_deps.sh` : installe les paquets Python (pip) et les paquets R
  requis par les analyses (liste de `checkinstall.py`), de façon
  idempotente ; options `--python`, `--rscript`, `--skip-python`,
  `--skip-r`, miroir CRAN configurable ; `rgl` est traité comme optionnel
  (graphes 3D uniquement, exige XQuartz sous macOS) ; notes
  d'installation wxPython pour Ubuntu en tête de script.

## Validation

Les évolutions ont été validées sur le corpus `data/theses-socio-1000.txt`
(1 000 résumés de thèses de sociologie, variable `*annee`) :

- CLI : construction du corpus (7 280 segments, 260 843 occurrences),
  puis `stat`, `spec` (avec et sans sélection de modalités), `simitxt`
  et `alceste` (2 classes par défaut, 7 classes avec `nbcl_p1 = 20`,
  AFC et dendrogrammes enrichis inclus), fichiers de sortie contrôlés ;
- explorateur : chargement de l'ensemble des résultats sans erreur et
  parcours de toutes les pages via `streamlit.testing.AppTest`, y compris
  les flux complets création de projet → exécution réelle → exploration,
  relance d'un traitement, suppression d'analyse et de projet ;
- boucle interface → CLI : les `.cfg` générés par l'interface ont été
  consommés par `iracmd.py` et les résultats réapparaissent dans
  l'interface.

## Dettes techniques

Les graphiques Reinert en ligne de commande (section 2) ont été réalisés
sans modifier le cœur du logiciel, au prix de deux dettes assumées :

1. **Duplication du générateur de script R des dendrogrammes.** Le script
   généré par `make_reinert_graphs` dans `iracmd.py` est une quasi-copie
   de celui que construit la GUI dans `layout.py` (méthode `make_dendro`
   de `GraphPanelDendro`, enfouie dans une classe de panneau wx et donc
   inutilisable hors interface). Toute évolution du tracé côté GUI devra
   être répercutée à la main côté CLI. Refactoring souhaitable : extraire
   ce générateur dans `PrintRScript.py` (lieu naturel des constructeurs de
   scripts R) et l'appeler des deux côtés.

2. **Correctif de robustesse présent uniquement côté CLI.** Quand la
   classification retient 2 classes ou moins, `RData.RData` ne contient
   pas les variables `debsup`/`debet` (créées seulement dans le bloc AFC,
   conditionné à `clnb > 2`) ; le script généré par la CLI les recalcule
   si elles sont absentes, alors que le script équivalent de la GUI
   échouerait dans ce cas. Le correctif serait à reporter dans
   `layout.py` (ou dans le générateur commun issu du point 1).

## Limites connues

- `iracmd.py` importe toujours wxPython (chaîne d'imports des modules
  d'analyse), même s'il n'ouvre aucune fenêtre ;
- l'AFC de la méthode Reinert n'existe que si la classification retient
  plus de 2 classes (comportement d'origine du script R) ;
- l'explorateur lit les résultats sur disque ; les analyses de matrices
  (`tab*.py`) ne sont pas couvertes par la CLI ni par l'explorateur ;
- `autres/` reste un ensemble de scripts historiques majoritairement
  Python 2, non portés.
