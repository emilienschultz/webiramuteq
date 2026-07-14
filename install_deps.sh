#!/usr/bin/env bash
# Installation des dépendances d'IRaMuTeQ 0.8 alpha 7 :
#   - paquets Python (requirements.txt), via pip
#   - paquets R nécessaires aux analyses, via Rscript
#
# Usage :
#   ./install_deps.sh                    # tout installer
#   ./install_deps.sh --python .venv/bin/python
#   ./install_deps.sh --skip-python      # seulement les paquets R
#   ./install_deps.sh --skip-r           # seulement les paquets Python
#   ./install_deps.sh --rscript /chemin/vers/Rscript
#
# Le script est idempotent : les paquets R déjà installés sont ignorés.


# On UBUNTU ADD
# pip install -U -f https://extras.wxpython.org/wxPython4/extras/linux/gtk3/ubuntu-24.04 wxPython
# sudo apt-get update
# sudo apt-get install -y libgtk-3-0t64 libgdk-pixbuf-2.0-0 libnotify4 libsdl2-2.0-0 libwebkit2gtk-4.1-0

set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"
RSCRIPT=""
SKIP_PYTHON=0
SKIP_R=0
CRAN_MIRROR="${CRAN_MIRROR:-https://cran.rstudio.com/}"

# paquets R requis (liste de checkinstall.py, + wordcloud utilisé par les
# dendrogrammes à nuages de mots) ; les paquets optionnels ne font pas
# échouer le script (rgl : graphes 3D uniquement, exige XQuartz sous macOS)
R_PACKAGES=(ca gee ape igraph proxy wordcloud irlba textometry sna network intergraph rgl)
R_OPTIONAL=" rgl "

while [ $# -gt 0 ]; do
    case "$1" in
        --python)  PYTHON="$2"; shift 2 ;;
        --rscript) RSCRIPT="$2"; shift 2 ;;
        --skip-python) SKIP_PYTHON=1; shift ;;
        --skip-r)  SKIP_R=1; shift ;;
        -h|--help) awk 'NR > 1 && /^#/ { sub(/^# ?/, ""); print; next } NR > 1 { exit }' "$0"; exit 0 ;;
        *) echo "option inconnue : $1 (voir --help)"; exit 2 ;;
    esac
done

FAILED=""

# ---------------------------------------------------------------- Python ---
if [ "$SKIP_PYTHON" -eq 0 ]; then
    echo "== Dépendances Python (interpréteur : $PYTHON) =="
    if ! command -v "$PYTHON" >/dev/null 2>&1 && [ ! -x "$PYTHON" ]; then
        echo "ERREUR : interpréteur Python introuvable : $PYTHON" >&2
        echo "  (indiquer un interpréteur avec --python /chemin/vers/python)" >&2
        exit 1
    fi
    "$PYTHON" -m pip --version >/dev/null 2>&1 || {
        echo "ERREUR : pip n'est pas disponible pour $PYTHON" >&2; exit 1; }
    if "$PYTHON" -m pip install -r "$HERE/requirements.txt"; then
        echo "-> paquets Python OK"
    else
        echo "ERREUR : échec de l'installation des paquets Python" >&2
        FAILED="$FAILED python"
    fi
    echo
fi

# --------------------------------------------------------------------- R ---
if [ "$SKIP_R" -eq 0 ]; then
    if [ -z "$RSCRIPT" ]; then
        for cand in Rscript \
                    /Library/Frameworks/R.framework/Resources/bin/Rscript \
                    /opt/homebrew/bin/Rscript \
                    /usr/local/bin/Rscript \
                    /usr/bin/Rscript; do
            if command -v "$cand" >/dev/null 2>&1; then RSCRIPT="$cand"; break; fi
        done
    fi
    if [ -z "$RSCRIPT" ]; then
        echo "ERREUR : Rscript introuvable — installer R (https://www.r-project.org)" >&2
        echo "  ou indiquer son chemin avec --rscript" >&2
        exit 1
    fi
    echo "== Paquets R (Rscript : $RSCRIPT, miroir : $CRAN_MIRROR) =="
    for pkg in "${R_PACKAGES[@]}"; do
        if "$RSCRIPT" -e "quit(status = as.integer(!requireNamespace('$pkg', quietly = TRUE)))" >/dev/null 2>&1; then
            echo "   $pkg : déjà installé"
        else
            echo "   $pkg : installation..."
            if "$RSCRIPT" -e "install.packages('$pkg', repos = '$CRAN_MIRROR')" >/dev/null 2>&1 \
               && "$RSCRIPT" -e "quit(status = as.integer(!requireNamespace('$pkg', quietly = TRUE)))" >/dev/null 2>&1; then
                echo "   $pkg : OK"
            elif [ "${R_OPTIONAL#* $pkg }" != "$R_OPTIONAL" ]; then
                echo "   $pkg : échec, paquet optionnel ignoré (graphes 3D)" >&2
            else
                echo "   $pkg : ECHEC" >&2
                FAILED="$FAILED $pkg"
            fi
        fi
    done
    echo
fi

# ------------------------------------------------------------------ bilan ---
if [ -n "$FAILED" ]; then
    echo "Terminé avec des échecs :$FAILED" >&2
    exit 1
fi
echo "Toutes les dépendances sont installées."
