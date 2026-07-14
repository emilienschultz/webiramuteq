# -*- coding: utf-8 -*-
#License: GNU/GPL
"""Explorateur Streamlit des résultats IRaMuTeQ.

    streamlit run iraexplorer/app.py

L'app ne fait que lire les répertoires de résultats (via model.py) et
préparer des fichiers .cfg pour iracmd.py (via configs.py). Un panneau
d'audit sur chaque page restitue la provenance exacte des fichiers.
"""

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
import configs as cfgmod
import runner
from model import Corpus, discover_corpora

REPO = Path(__file__).resolve().parent.parent

# palette de référence (skill dataviz) : une teinte pour les grandeurs,
# une paire divergente pour les polarités, un ordre catégoriel fixe
BLUE = '#2a78d6'
RED = '#e34948'
CATEG = ['#2a78d6', '#1baf7a', '#eda100', '#008300',
         '#4a3aa7', '#e34948', '#e87ba4', '#eb6834']

st.set_page_config(page_title='IRaMuTeQ explorer', page_icon='📚', layout='wide')


# ---------------------------------------------------------------------------
# aides
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner='chargement du corpus...')
def load_corpus(path, mtime) :
    # mtime invalide le cache quand le répertoire change
    return Corpus(path)


def hbar(df, label, value, color=BLUE, height=None, value_title=None) :
    """Barres horizontales, une teinte, tri décroissant, tooltip."""
    chart = (alt.Chart(df)
             .mark_bar(color=color, cornerRadiusEnd=2, height={'band' : 0.7})
             .encode(x=alt.X(value, type='quantitative',
                             title=value_title or value),
                     y=alt.Y(label, type='nominal', sort='-x', title=None),
                     tooltip=list(df.columns)))
    return chart.properties(height=height or max(120, 22 * len(df)))


def searchable_table(df, key, columns=None) :
    """Filtre plein-texte + tableau."""
    query = st.text_input('Filtrer', key='filter_' + key,
                          placeholder='texte à chercher...')
    view = df
    if query :
        mask = pd.Series(False, index=df.index)
        for col in (columns or df.columns) :
            mask |= df[col].astype(str).str.contains(query, case=False, na=False)
        view = df[mask]
    st.caption('%i lignes / %i' % (len(view), len(df)))
    st.dataframe(view, use_container_width=True, hide_index=True)


def audit_panel(analysis) :
    """Provenance des fichiers de l'analyse + export JSON."""
    with st.expander('🔍 Audit — fichiers et provenance') :
        checksum = st.checkbox('calculer les empreintes SHA-256', key='sha_' + analysis.name)
        st.dataframe(analysis.manifest(checksum=checksum), use_container_width=True, hide_index=True)
        st.download_button('Exporter l\'analyse en JSON (tables incluses)',
                           analysis.to_json(include_tables=True, checksum=checksum),
                           file_name='%s.json' % analysis.name, mime='application/json',
                           key='json_' + analysis.name)


def parametres_panel(parametres, name) :
    with st.expander('⚙️ Paramètres enregistrés (%s)' % name) :
        st.dataframe(pd.DataFrame(sorted(parametres.items()),
                                  columns=['paramètre', 'valeur']),
                     use_container_width=True, hide_index=True)


def show_images(analysis, keys=None) :
    imgs = [im for im in analysis.images() if keys is None or im[0] in keys]
    if not imgs :
        return
    cols = st.columns(min(2, len(imgs)))
    for i, (key, path, desc) in enumerate(imgs) :
        with cols[i % len(cols)] :
            st.image(str(path), caption=desc, use_column_width=True)


# ---------------------------------------------------------------------------
# pages
# ---------------------------------------------------------------------------

def page_corpus(corpus) :
    st.header('Corpus — %s' % corpus.name)
    p = corpus.parametres
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Textes', p.get('ucinb', '?'))
    c2.metric('Segments', p.get('ucenb', '?'))
    c3.metric('Occurrences', p.get('occurrences', '?'))
    c4.metric('Langue', p.get('lang', '?'))

    st.subheader('Variables étoilées')
    variables = corpus.variables()
    if variables.empty :
        st.info('aucune variable étoilée détectée')
    else :
        var = st.selectbox('Variable', sorted(variables['variable'].unique()))
        sub = variables[variables['variable'] == var].sort_values('textes', ascending=False)
        st.altair_chart(hbar(sub, 'modalite', 'textes', value_title='textes'),
                        use_container_width=True)

    st.subheader('Formes du corpus')
    searchable_table(corpus.forms(), 'forms_' + corpus.name)

    st.subheader('Extraits de segments')
    st.dataframe(corpus.segments(limit=10), use_container_width=True, hide_index=True)

    with st.expander('🔍 Audit — fichiers du corpus') :
        checksum = st.checkbox('calculer les empreintes SHA-256', key='sha_corpus')
        st.dataframe(corpus.manifest(checksum=checksum), use_container_width=True, hide_index=True)
    parametres_panel(p, 'Corpus.cira')


def page_stat(corpus, analysis) :
    st.header('Statistiques — %s' % analysis.name)
    summary = analysis.text('summary') or ''
    metrics = [l.split(' : ') for l in summary.splitlines() if ' : ' in l]
    if metrics :
        cols = st.columns(len(metrics))
        for col, (label, value) in zip(cols, metrics) :
            col.metric(label.replace('Nombre de', 'Nb').replace('Nombre d\'', 'Nb '),
                       value.split(' (')[0])
        st.caption(summary.splitlines()[-1] if 'hapax' not in summary.splitlines()[-1] else '')

    actives = analysis.table('actives')
    if actives is not None :
        st.subheader('Formes actives les plus fréquentes')
        n = st.slider('Nombre de formes affichées', 10, 100, 25, key='nstat')
        st.altair_chart(hbar(actives.head(n), 'forme', 'freq', value_title='effectif'),
                        use_container_width=True)

    st.subheader('Tables')
    tabs = st.tabs(['Toutes les formes', 'Actives', 'Supplémentaires', 'Hapax'])
    for tab, key in zip(tabs, ['total', 'actives', 'supplementaires', 'hapax']) :
        with tab :
            df = analysis.table(key)
            if df is not None :
                searchable_table(df, key + analysis.name)

    st.subheader('Diagrammes calculés par R')
    show_images(analysis)
    audit_panel(analysis)
    parametres_panel(analysis.parametres, 'Analyse.ira')


def page_spec(corpus, analysis) :
    st.header('Spécificités — %s' % analysis.name)
    spec = analysis.table('spec_formes')
    if spec is None :
        st.error('tablespecf.csv absent ou illisible (voir l\'audit)')
    else :
        st.subheader('Spécificités d\'une modalité')
        modalite = st.selectbox('Modalité', list(spec.columns))
        n = st.slider('Nombre de formes', 5, 50, 15, key='nspec')
        serie = spec[modalite].astype(float)
        top = pd.concat([serie.nlargest(n), serie.nsmallest(n)])
        df = top.reset_index()
        df.columns = ['forme', 'score']
        df['sens'] = df['score'].map(lambda v : 'sur-représentée' if v > 0 else 'sous-représentée')
        # polarité : paire divergente bleu/rouge, jamais un dégradé arc-en-ciel
        chart = (alt.Chart(df)
                 .mark_bar(cornerRadiusEnd=2, height={'band' : 0.7})
                 .encode(x=alt.X('score', type='quantitative', title='score de spécificité'),
                         y=alt.Y('forme', type='nominal',
                                 sort=alt.EncodingSortField('score', order='descending'),
                                 title=None),
                         color=alt.Color('sens', type='nominal',
                                         scale=alt.Scale(domain=['sur-représentée', 'sous-représentée'],
                                                         range=[BLUE, RED]),
                                         legend=alt.Legend(title=None, orient='top')),
                         tooltip=['forme', 'score', 'sens']))
        st.altair_chart(chart.properties(height=max(200, 20 * len(df))),
                        use_container_width=True)

        st.subheader('Tables complètes')
        tabs = st.tabs(['Spécificités des formes', 'Spécificités des types',
                        'Effectifs', 'Banalités', 'Bilan par modalité'])
        for tab, key in zip(tabs, ['spec_formes', 'spec_types', 'freq_formes',
                                   'banalites', 'stat_modalites']) :
            with tab :
                df = analysis.table(key)
                if df is not None :
                    st.dataframe(df, use_container_width=True)

    st.subheader('Analyses factorielles (images R)')
    show_images(analysis)
    audit_panel(analysis)
    parametres_panel(analysis.parametres, 'Analyse.ira')


def infotxt_metrics(info) :
    """Extrait les compteurs de info.txt -> ([(label, valeur)], lignes restantes)."""
    metrics, rest = [], []
    for line in info.splitlines() :
        line = line.strip()
        if not line or set(line) <= set('+-|iRaMuTeQ# ') :
            continue
        if ':' in line and line.split(':')[1].strip() \
           and not line.startswith(('temps', '|')) :
            label, value = line.split(':', 1)
            metrics.append((label.strip(), value.strip()))
        else :
            rest.append(line)
    return metrics, rest


def page_alceste(corpus, analysis) :
    st.header('Classification Reinert — %s' % analysis.name)

    # info.txt : le bilan de l'analyse, mis en avant
    info = analysis.text('info')
    if info :
        metrics, rest = infotxt_metrics(info)
        main = [(l, v) for l, v in metrics
                if l in ('Nombre de textes', 'Nombre de segments de texte',
                         'Nombre de formes', "Nombre d'occurrences",
                         'Nombre de classes')]
        if main :
            cols = st.columns(len(main))
            for col, (label, value) in zip(cols, main) :
                col.metric(label.replace('Nombre de segments de texte', 'Segments')
                                .replace('Nombre de textes', 'Textes')
                                .replace('Nombre de formes', 'Formes')
                                .replace("Nombre d'occurrences", 'Occurrences')
                                .replace('Nombre de classes', 'Classes'), value)
        for line in rest :
            if 'class' in line :        # ex : 7111 segments classés sur 7280 (97.68%)
                st.markdown('**%s**' % line)
        with st.expander('Bilan complet de l\'analyse (info.txt)') :
            st.code(info)

    prof = analysis.table('profiles')
    classes = prof.attrs.get('classes', []) if prof is not None else []
    if classes :
        dfc = pd.DataFrame(classes)
        dfc['classe'] = dfc['classe'].astype(str)
        st.subheader('Poids des classes')
        chart = (alt.Chart(dfc)
                 .mark_bar(cornerRadiusEnd=2, height={'band' : 0.7})
                 .encode(x=alt.X('segments', type='quantitative', title='segments classés'),
                         y=alt.Y('classe', type='nominal', title='classe'),
                         color=alt.Color('classe', type='nominal',
                                         scale=alt.Scale(range=CATEG), legend=None),
                         tooltip=['classe', 'segments', 'pourcentage']))
        st.altair_chart(chart.properties(height=32 * len(dfc) + 40),
                        use_container_width=True)

    st.subheader('Dendrogrammes')
    dendros = [('dendrogramme', 'simple'), ('dendro_texte', 'avec profils'),
               ('dendro_cloud', 'avec nuages de mots'), ('arbre', 'arbre CHD')]
    present = [(k, t) for k, t in dendros if analysis.image_path(k) is not None]
    if present :
        tabs = st.tabs([t for _, t in present])
        for tab, (key, _) in zip(tabs, present) :
            with tab :
                st.image(str(analysis.image_path(key)),
                         caption=analysis.files[key].spec.description,
                         use_column_width=True)
    else :
        st.info('aucun dendrogramme — relancer l\'analyse avec iracmd.py '
                'pour les générer')

    afc_imgs = [('afc_actives', 'formes actives'), ('afc_sup', 'formes supplémentaires'),
                ('afc_etoiles', 'variables étoilées'), ('afc_classes', 'classes')]
    present = [(k, t) for k, t in afc_imgs if analysis.image_path(k) is not None]
    st.subheader('Analyse factorielle des correspondances')
    if present :
        tabs = st.tabs([t for _, t in present] + ['facteurs'])
        for tab, (key, _) in zip(tabs, present) :
            with tab :
                st.image(str(analysis.image_path(key)),
                         caption=analysis.files[key].spec.description,
                         use_column_width=True)
        with tabs[-1] :
            facteurs = analysis.table('afc_facteur')
            if facteurs is not None :
                st.dataframe(facteurs, use_container_width=True)
    else :
        st.info('pas d\'AFC : elle n\'est calculée que lorsque la '
                'classification retient plus de 2 classes')

    if prof is not None and not prof.empty :
        st.subheader('Profils des classes')
        nums = sorted(prof['classe'].unique())
        tabs = st.tabs(['Classe %i' % i for i in nums])
        for tab, num in zip(tabs, nums) :
            with tab :
                sub = prof[prof['classe'] == num]
                color = CATEG[(num - 1) % len(CATEG)]
                top = sub[sub['categorie'] == 'active'].nlargest(20, 'chi2')
                st.altair_chart(hbar(top[['forme', 'chi2', 'eff_seg_classe', 'pourcentage']],
                                     'forme', 'chi2', color=color, value_title='chi2'),
                                use_container_width=True)
                etoiles = sub[sub['categorie'] == 'étoile']
                if not etoiles.empty :
                    st.caption('Modalités associées : ' + ', '.join(
                        '%s (chi2 %.1f)' % (r.forme, r.chi2)
                        for r in etoiles.nlargest(5, 'chi2').itertuples()))
                searchable_table(sub, 'prof%i_%s' % (num, analysis.name))
                # segments représentatifs : uce.csv (ligne N = segment N-1)
                uce = analysis.table('uce_classes')
                if uce is not None and st.checkbox('Voir des segments de cette classe',
                                                   key='seg%i_%s' % (num, analysis.name)) :
                    ids = [i - 1 for i in uce[uce.iloc[:, 0] == num].index[:10]]
                    segs = corpus.segments(ids=ids)
                    for r in segs.itertuples() :
                        st.markdown('- %s' % r.texte)

        antiprof = analysis.table('antiprofiles')
        if antiprof is not None and not antiprof.empty :
            with st.expander('Antiprofils (formes sous-représentées)') :
                searchable_table(antiprof, 'antiprof_' + analysis.name)

    audit_panel(analysis)
    parametres_panel(analysis.parametres, 'Analyse.ira')


def page_simitxt(corpus, analysis) :
    st.header('Similitudes — %s' % analysis.name)
    imgs = analysis.images()
    if imgs :
        st.image(str(imgs[0][1]), caption=imgs[0][2], use_column_width=True)
    actives = analysis.table('actives')
    selected = analysis.table('selected')
    if actives is not None :
        st.subheader('Formes retenues')
        if selected is not None :
            st.caption('%i formes sélectionnées sur %i formes actives'
                       % (len(selected), len(actives)))
        searchable_table(actives, 'actsimi_' + analysis.name)
    audit_panel(analysis)
    parametres_panel(analysis.parametres, 'Analyse.ira')


def page_generic(corpus, analysis) :
    st.header('%s — %s' % (analysis.type, analysis.name))
    st.info('pas de vue dédiée pour ce type d\'analyse : affichage générique')
    for key, lf in analysis.files.items() :
        data = lf.load()
        if isinstance(data, pd.DataFrame) :
            st.subheader('%s — %s' % (key, lf.spec.description))
            st.dataframe(data.head(500), use_container_width=True)
        elif isinstance(data, str) :
            st.subheader(key)
            st.code(data)
    show_images(analysis)
    audit_panel(analysis)
    parametres_panel(analysis.parametres, 'Analyse.ira')


# ---------------------------------------------------------------------------
# page « lancer un calcul » : corpus + paramètres + exécution
# ---------------------------------------------------------------------------

TREATMENTS = ['alceste', 'stat', 'spec', 'simitxt']
LANGS = ['french', 'english', 'german', 'italian', 'spanish', 'portuguese',
         'greek', 'swedish', 'galician', 'other']


def _widget_for(key, value, help_txt, choices, wkey) :
    if choices is not None :
        # normaliser la valeur courante vers une option existante
        cur = cfgmod.parse_value(value)
        idx = choices.index(cur) if cur in choices else 0
        return st.selectbox(key, choices, index=idx, help=help_txt, key=wkey)
    if isinstance(value, bool) :
        return st.checkbox(key, value=value, help=help_txt, key=wkey)
    if isinstance(value, int) :
        return st.number_input(key, value=value, step=1, help=help_txt, key=wkey)
    if isinstance(value, float) :
        return st.number_input(key, value=value, help=help_txt, key=wkey)
    if isinstance(value, (list, tuple)) :
        raw = st.text_input(key, value=repr(list(value)), help=help_txt, key=wkey)
        return cfgmod.parse_value(raw)
    return st.text_input(key, value=str(value), help=help_txt, key=wkey)


def _params_editor(target, corpus=None, extra_defaults=None) :
    """Widgets d'édition des paramètres d'un traitement -> dict."""
    defaults, source = cfgmod.load_defaults(target)
    if extra_defaults :
        defaults = {**extra_defaults, **defaults}
    st.caption('valeurs par défaut : %s' % source)
    params = {}
    # pour spec sur un corpus déjà construit : proposer ses modalités
    if target == 'spec' and corpus is not None :
        variables = corpus.variables()
        options = sorted(variables['modalite'].unique()) if not variables.empty else []
        params['etoiles'] = st.multiselect(
            'etoiles', options, default=[], key='p_%s_etoiles' % target,
            help=cfgmod.PARAM_HELP['etoiles'][0] + ' (vide = première variable)')
        defaults.pop('etoiles', None)
    cols = st.columns(2)
    for i, (key, value) in enumerate(sorted(defaults.items())) :
        help_txt, choices = cfgmod.PARAM_HELP.get(key, (None, None))
        with cols[i % 2] :
            params[key] = _widget_for(key, value, help_txt, choices,
                                      'p_%s_%s' % (target, key))
    return params


def page_run(corpus, root) :
    st.header('🚀 Lancer un calcul')
    st.markdown(
        'Choisissez un corpus, les traitements et leurs paramètres : les '
        'paramètres sont écrits dans des fichiers `.cfg` **propres à ce '
        'calcul** (répertoire `configs/`), puis `iracmd.py` est lancé. '
        'Les configurations par défaut d\'IRaMuTeQ ne sont pas modifiées.')

    # ---- 1. le corpus -----------------------------------------------------
    st.subheader('1. Corpus')
    mode = st.radio('Source', ['nouveau corpus (fichier texte au format Alceste)',
                               'corpus déjà construit'], horizontal=True)
    corpus_file = corpus_cira = None
    corpus_params = None
    lang = encoding = None
    newmode = mode.startswith('nouveau')
    if newmode :
        uploaded = st.file_uploader('Déposer un fichier corpus (.txt) — il sera '
                                    'copié dans le répertoire exploré', type=['txt'])
        if uploaded is not None :
            dest = Path(root) / uploaded.name
            if not dest.exists() :
                dest.write_bytes(uploaded.getvalue())
                st.success('fichier copié : %s' % dest)
        candidates = sorted(str(p) for p in Path(root).glob('*.txt'))
        if candidates :
            corpus_file = st.selectbox('Fichier corpus', candidates)
        else :
            st.warning('aucun fichier .txt dans %s — déposez-en un ci-dessus '
                       'ou indiquez un chemin' % root)
        other = st.text_input('...ou chemin complet d\'un autre fichier', value='')
        if other.strip() :
            corpus_file = other.strip()
        c1, c2 = st.columns(2)
        lang = c1.selectbox('Langue', LANGS, index=0)
        encoding = c2.text_input('Encodage', value='utf-8')
        with st.expander('Paramètres d\'import du corpus (segmentation, '
                         'lemmatisation, nettoyage...)') :
            corpus_params = _params_editor('corpus')
    else :
        if corpus is None :
            st.warning('aucun corpus construit — utilisez le mode « nouveau corpus »')
            return
        corpus_cira = str(corpus.cira)
        st.info('corpus sélectionné dans la barre latérale : **%s** (`%s`)'
                % (corpus.name, corpus_cira))
        lang = corpus.parametres.get('lang')

    # ---- 2. les traitements et leurs paramètres ---------------------------
    st.subheader('2. Traitements')
    selected = st.multiselect('Traitements à lancer', TREATMENTS,
                              default=['stat', 'alceste'])
    all_params = {}
    for target in selected :
        with st.expander('Paramètres — %s' % target, expanded=False) :
            all_params[target] = _params_editor(
                target, corpus=None if newmode else corpus,
                extra_defaults={'max_actives_simi' : 200} if target == 'simitxt' else None)

    # ---- 3. écriture des .cfg et exécution --------------------------------
    st.subheader('3. Exécution')
    stem = Path(corpus_file).stem if corpus_file else (corpus.name if corpus else 'run')
    run_name = st.text_input('Nom du calcul (répertoire des .cfg et du journal)',
                             value=stem)
    cfg_dir = REPO / 'configs' / run_name
    python = st.text_input('Interpréteur Python pour iracmd.py (wxPython requis)',
                           value=st.session_state.get('iracmd_python', sys.executable))
    st.session_state['iracmd_python'] = python

    col1, col2 = st.columns(2)
    write_only = col1.button('Écrire les .cfg seulement')
    launch = col2.button('Écrire les .cfg et lancer le calcul', type='primary',
                         disabled=not selected or (newmode and not corpus_file))

    if write_only or launch :
        written = {}
        if newmode and corpus_params is not None :
            path = cfg_dir / 'corpus.cfg'
            cfgmod.write_config(corpus_params, 'corpus', path)
            written['corpus'] = path
        for target in selected :
            path = cfg_dir / ('%s.cfg' % target)
            cfgmod.write_config(all_params.get(target, {}), target, path)
            written[target] = path
        st.session_state['run_written'] = {k : str(v) for k, v in written.items()}
        with st.expander('Fichiers .cfg écrits', expanded=not launch) :
            for target, path in written.items() :
                st.markdown('**`%s`**' % path)
                st.code(Path(path).read_text(encoding='utf8'), language='ini')
        # commandes équivalentes (rejouables à la main)
        cmds = []
        if newmode :
            cmds.append(cfgmod.build_command('corpus', cfg_path=written.get('corpus'),
                                             corpus_file=corpus_file, lang=lang,
                                             python=python)
                        + (' -e %s' % encoding if encoding else ''))
            cira_display = '<répertoire_créé>/Corpus.cira'
        else :
            cira_display = corpus_cira
        for target in selected :
            cmds.append(cfgmod.build_command(target, cfg_path=written.get(target),
                                             corpus_cira=cira_display, lang=lang,
                                             python=python))
        st.markdown('Commandes équivalentes :')
        st.code('\n'.join(cmds), language='bash')

    if launch :
        log_path = cfg_dir / 'run.log'
        written = st.session_state.get('run_written', {})
        analyses = [(t, written.get(t)) for t in selected]
        status = st.status('Calcul en cours...', expanded=True)

        def on_step(step) :
            icon = '✅' if step.ok else '❌'
            status.write('%s %s — code retour %s' % (icon, step.label, step.returncode))
            if not step.ok :
                status.code((step.stdout or '') + '\n' + (step.stderr or ''))

        steps, cira = runner.run_pipeline(
            python=python, analyses=analyses,
            corpus_file=None if not newmode else corpus_file,
            corpus_cira=corpus_cira, corpus_cfg=written.get('corpus'),
            lang=lang, encoding=encoding if newmode else None,
            cwd=REPO, log_path=log_path, on_step=on_step)
        ok = all(s.ok for s in steps)
        status.update(label='calcul terminé' if ok else 'calcul terminé avec des erreurs',
                      state='complete' if ok else 'error', expanded=True)
        st.caption('journal complet : %s' % log_path)
        if cira :
            st.success('résultats dans : %s' % Path(cira).parent)
        if st.button('Actualiser l\'explorateur') :
            load_corpus.clear()
            st.rerun()


# ---------------------------------------------------------------------------
# navigation
# ---------------------------------------------------------------------------

RENDERERS = {
    'stat' : page_stat,
    'spec' : page_spec,
    'alceste' : page_alceste,
    'reinert' : page_alceste,
    'simitxt' : page_simitxt,
}

ICONS = {'alceste' : '🌳', 'reinert' : '🌳', 'stat' : '📊',
         'spec' : '🎯', 'simitxt' : '🕸️'}


def corpus_signature(path) :
    """Clé de cache : change quand une analyse est ajoutée ou modifiée."""
    path = Path(path)
    sig = [('Corpus.cira', path.joinpath('Corpus.cira').stat().st_mtime)]
    for ira in sorted(path.glob('*/Analyse.ira')) :
        sig.append((ira.parent.name, ira.stat().st_mtime))
    return tuple(sig)


def main() :
    st.sidebar.title('IRaMuTeQ explorer')
    root = st.sidebar.text_input('Répertoire à explorer', value=str(REPO / 'data'))
    corpora = discover_corpora(root)
    corpus = None
    if not corpora :
        st.sidebar.warning('aucun répertoire de corpus (Corpus.cira) trouvé')
    else :
        by_name = {Path(p).name : str(p) for p in corpora}
        name = st.sidebar.selectbox('Corpus', sorted(by_name))
        choice = by_name[name]
        corpus = load_corpus(choice, corpus_signature(choice))

    entries = ['🚀 Lancer un calcul', '📄 Corpus']
    if corpus is not None :
        entries += ['%s %s' % (ICONS.get(a.type, '📁'), a.name) for a in corpus.analyses]
    page = st.sidebar.radio('Navigation', entries)
    if st.sidebar.button('🔄 Actualiser') :
        load_corpus.clear()
        st.rerun()

    if page == '🚀 Lancer un calcul' :
        page_run(corpus, root)
    elif corpus is None :
        st.info('Indiquez un répertoire contenant des résultats IRaMuTeQ '
                '(un dossier avec un fichier Corpus.cira), ou lancez un '
                'calcul sur un nouveau corpus via la page dédiée.')
    elif page == '📄 Corpus' :
        page_corpus(corpus)
    else :
        analysis = corpus.analyses[entries.index(page) - 2]
        RENDERERS.get(analysis.type, page_generic)(corpus, analysis)


main()
