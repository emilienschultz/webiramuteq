# -*- coding: utf-8 -*-
#License: GNU/GPL
"""Explorateur Streamlit des résultats IRaMuTeQ, organisé en projets.

    streamlit run iraexplorer/app.py

Tous les projets vivent dans un même dossier (par défaut `projects/` à la
racine du dépôt) : un projet = un sous-répertoire contenant le fichier
corpus source, les fichiers .cfg du calcul, le journal run.log et les
répertoires de résultats. La page d'accueil liste les projets et permet
d'en créer, d'en ouvrir ou d'en supprimer.
"""

import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
import configs as cfgmod
import runner
from model import (Corpus, delete_analysis, delete_project, discover_corpora,
                   discover_projects)

REPO = Path(__file__).resolve().parent.parent
DEFAULT_PROJECTS = REPO / 'projects'

# palette de référence (skill dataviz) : une teinte pour les grandeurs,
# une paire divergente pour les polarités, un ordre catégoriel fixe
BLUE = '#2a78d6'
RED = '#e34948'
CATEG = ['#2a78d6', '#1baf7a', '#eda100', '#008300',
         '#4a3aa7', '#e34948', '#e87ba4', '#eb6834']

TREATMENTS = ['alceste', 'stat', 'spec', 'simitxt']
LANGS = ['french', 'english', 'german', 'italian', 'spanish', 'portuguese',
         'greek', 'swedish', 'galician', 'other']

# compatibilité : streamlit >= 1.49 remplace use_container_width/use_column_width
# par width='stretch'
_ST_NEW = tuple(int(v) for v in st.__version__.split('.')[:2]) >= (1, 49)
FULL = {'width' : 'stretch'} if _ST_NEW else {'use_container_width' : True}
IMGFULL = {'width' : 'stretch'} if _ST_NEW else {'use_column_width' : True}

st.set_page_config(page_title='IRaMuTeQ explorer', page_icon='📚', layout='wide')


# ---------------------------------------------------------------------------
# aides
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner='chargement du corpus...')
def load_corpus(path, signature) :
    # signature invalide le cache quand une analyse est ajoutée/supprimée
    return Corpus(path)


def corpus_signature(path) :
    path = Path(path)
    sig = [('Corpus.cira', path.joinpath('Corpus.cira').stat().st_mtime)]
    for ira in sorted(path.glob('*/Analyse.ira')) :
        sig.append((ira.parent.name, ira.stat().st_mtime))
    return tuple(sig)


def goto(view, **state) :
    st.session_state['view'] = view
    for key, val in state.items() :
        st.session_state[key] = val
    st.rerun()


def projects_root() :
    return Path(st.session_state.get('projects_root', str(DEFAULT_PROJECTS)))


def hbar(df, label, value, color=BLUE, height=None, value_title=None) :
    """Barres horizontales, une teinte, tri décroissant, tooltip."""
    chart = (alt.Chart(df)
             .mark_bar(color=color, cornerRadiusEnd=2, height={'band' : 0.7})
             .encode(x=alt.X(value, type='quantitative',
                             title=value_title or value),
                     y=alt.Y(label, type='nominal', sort='-x', title=None),
                     tooltip=list(df.columns)))
    return chart.properties(height=height or max(120, 22 * len(df)))


def altair_full(chart) :
    if _ST_NEW :
        st.altair_chart(chart, width='stretch')
    else :
        st.altair_chart(chart, use_container_width=True)


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
    st.dataframe(view, hide_index=True, **FULL)


def audit_panel(analysis) :
    """Provenance des fichiers de l'analyse + export JSON."""
    with st.expander('🔍 Audit — fichiers et provenance') :
        checksum = st.checkbox('calculer les empreintes SHA-256', key='sha_' + analysis.name)
        st.dataframe(analysis.manifest(checksum=checksum), hide_index=True, **FULL)
        st.download_button('Exporter l\'analyse en JSON (tables incluses)',
                           analysis.to_json(include_tables=True, checksum=checksum),
                           file_name='%s.json' % analysis.name, mime='application/json',
                           key='json_' + analysis.name)


def parametres_panel(parametres, name) :
    with st.expander('⚙️ Paramètres enregistrés (%s)' % name) :
        st.dataframe(pd.DataFrame(sorted(parametres.items()),
                                  columns=['paramètre', 'valeur']),
                     hide_index=True, **FULL)


def show_images(analysis, keys=None) :
    imgs = [im for im in analysis.images() if keys is None or im[0] in keys]
    if not imgs :
        return
    cols = st.columns(min(2, len(imgs)))
    for i, (key, path, desc) in enumerate(imgs) :
        with cols[i % len(cols)] :
            st.image(str(path), caption=desc, **IMGFULL)


# ---------------------------------------------------------------------------
# pages de résultats (dans un projet)
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
        altair_full(hbar(sub, 'modalite', 'textes', value_title='textes'))

    st.subheader('Formes du corpus')
    searchable_table(corpus.forms(), 'forms_' + corpus.name)

    st.subheader('Extraits de segments')
    st.dataframe(corpus.segments(limit=10), hide_index=True, **FULL)

    with st.expander('🔍 Audit — fichiers du corpus') :
        checksum = st.checkbox('calculer les empreintes SHA-256', key='sha_corpus')
        st.dataframe(corpus.manifest(checksum=checksum), hide_index=True, **FULL)
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

    actives = analysis.table('actives')
    if actives is not None :
        st.subheader('Formes actives les plus fréquentes')
        n = st.slider('Nombre de formes affichées', 10, 100, 25, key='nstat')
        altair_full(hbar(actives.head(n), 'forme', 'freq', value_title='effectif'))

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
        altair_full(chart.properties(height=max(200, 20 * len(df))))

        st.subheader('Tables complètes')
        tabs = st.tabs(['Spécificités des formes', 'Spécificités des types',
                        'Effectifs', 'Banalités', 'Bilan par modalité'])
        for tab, key in zip(tabs, ['spec_formes', 'spec_types', 'freq_formes',
                                   'banalites', 'stat_modalites']) :
            with tab :
                df = analysis.table(key)
                if df is not None :
                    st.dataframe(df, **FULL)

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
        altair_full(chart.properties(height=32 * len(dfc) + 40))

    st.subheader('Dendrogrammes')
    dendros = [('dendrogramme', 'simple'), ('dendro_texte', 'avec profils'),
               ('dendro_cloud', 'avec nuages de mots'), ('arbre', 'arbre CHD')]
    present = [(k, t) for k, t in dendros if analysis.image_path(k) is not None]
    if present :
        tabs = st.tabs([t for _, t in present])
        for tab, (key, _) in zip(tabs, present) :
            with tab :
                st.image(str(analysis.image_path(key)),
                         caption=analysis.files[key].spec.description, **IMGFULL)
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
                         caption=analysis.files[key].spec.description, **IMGFULL)
        with tabs[-1] :
            facteurs = analysis.table('afc_facteur')
            if facteurs is not None :
                st.dataframe(facteurs, **FULL)
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
                altair_full(hbar(top[['forme', 'chi2', 'eff_seg_classe', 'pourcentage']],
                                 'forme', 'chi2', color=color, value_title='chi2'))
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
        st.image(str(imgs[0][1]), caption=imgs[0][2], **IMGFULL)
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
            st.dataframe(data.head(500), **FULL)
        elif isinstance(data, str) :
            st.subheader(key)
            st.code(data)
    show_images(analysis)
    audit_panel(analysis)
    parametres_panel(analysis.parametres, 'Analyse.ira')


RENDERERS = {
    'stat' : page_stat,
    'spec' : page_spec,
    'alceste' : page_alceste,
    'reinert' : page_alceste,
    'simitxt' : page_simitxt,
}

ICONS = {'alceste' : '🌳', 'reinert' : '🌳', 'stat' : '📊',
         'spec' : '🎯', 'simitxt' : '🕸️'}


# ---------------------------------------------------------------------------
# édition des paramètres et lancement d'un calcul
# ---------------------------------------------------------------------------

def _widget_for(key, value, help_txt, choices, wkey) :
    if choices is not None :
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


def treatments_editor(corpus=None) :
    """Choix des traitements + édition de leurs paramètres -> (liste, dict)."""
    selected = st.multiselect('Traitements à lancer', TREATMENTS,
                              default=['stat', 'alceste'])
    all_params = {}
    for target in selected :
        with st.expander('Paramètres — %s' % target, expanded=False) :
            all_params[target] = _params_editor(
                target, corpus=corpus,
                extra_defaults={'max_actives_simi' : 200} if target == 'simitxt' else None)
    return selected, all_params


def python_field() :
    python = st.text_input('Interpréteur Python pour iracmd.py (wxPython requis)',
                           value=st.session_state.get('iracmd_python', sys.executable))
    st.session_state['iracmd_python'] = python
    return python


def write_cfgs(project_dir, selected, all_params, corpus_params=None) :
    """Écrit les .cfg du calcul dans le dossier du projet -> {cible : chemin}."""
    written = {}
    if corpus_params is not None :
        path = Path(project_dir) / 'corpus.cfg'
        cfgmod.write_config(corpus_params, 'corpus', path)
        written['corpus'] = path
    for target in selected :
        path = Path(project_dir) / ('%s.cfg' % target)
        cfgmod.write_config(all_params.get(target, {}), target, path)
        written[target] = path
    return written


def launch_pipeline(python, project_dir, selected, written, corpus_file=None,
                    corpus_cira=None, lang=None, encoding=None) :
    """Exécute le pipeline avec affichage progressif ; retourne (ok, cira)."""
    status = st.status('Calcul en cours...', expanded=True)

    def on_step(step) :
        icon = '✅' if step.ok else '❌'
        status.write('%s %s — code retour %s' % (icon, step.label, step.returncode))
        if not step.ok :
            status.code((step.stdout or '') + '\n' + (step.stderr or ''))

    steps, cira = runner.run_pipeline(
        python=python, analyses=[(t, written.get(t)) for t in selected],
        corpus_file=corpus_file, corpus_cira=corpus_cira,
        corpus_cfg=written.get('corpus'), lang=lang, encoding=encoding,
        cwd=REPO, log_path=Path(project_dir) / 'run.log', on_step=on_step)
    ok = bool(steps) and all(s.ok for s in steps)
    status.update(label='calcul terminé' if ok else 'calcul terminé avec des erreurs',
                  state='complete' if ok else 'error', expanded=not ok)
    st.caption('journal : %s — fichiers .cfg : %s' % (Path(project_dir) / 'run.log',
                                                      project_dir))
    return ok, cira


# ---------------------------------------------------------------------------
# page d'accueil : liste des projets, création, ouverture, suppression
# ---------------------------------------------------------------------------

def page_home() :
    st.title('📚 IRaMuTeQ explorer')
    root = st.text_input('Dossier des projets',
                         value=st.session_state.get('projects_root', str(DEFAULT_PROJECTS)))
    st.session_state['projects_root'] = root

    if st.button('➕ Créer une nouvelle analyse', type='primary') :
        goto('create')

    st.subheader('Projets existants')
    projects = discover_projects(root)
    if not projects :
        st.info('aucun projet dans %s — créez une nouvelle analyse' % root)
        return
    for proj in projects :
        with st.container(border=True) :
            c1, c2, c3, c4 = st.columns([3, 4, 1, 1])
            c1.markdown('**%s**' % proj['name'])
            desc = '%i corpus, %i analyse(s)' % (proj['n_corpora'], proj['n_analyses'])
            if proj['analyses_types'] :
                desc += ' — ' + ', '.join(proj['analyses_types'])
            c2.markdown(desc)
            c2.caption('modifié le %s' % proj['modified'])
            if proj['n_corpora'] and c3.button('Ouvrir', key='open_' + proj['name']) :
                goto('project', project=proj['path'])
            if c4.button('🗑️', key='del_' + proj['name'],
                         help='supprimer ce projet') :
                st.session_state['confirm_delete'] = proj['path']
            if st.session_state.get('confirm_delete') == proj['path'] :
                st.warning('Supprimer définitivement le projet **%s** et tous '
                           'ses résultats ? (%s)' % (proj['name'], proj['path']))
                cc1, cc2 = st.columns(2)
                if cc1.button('Oui, supprimer', key='delyes_' + proj['name'],
                              type='primary') :
                    delete_project(proj['path'], root)
                    load_corpus.clear()
                    st.session_state.pop('confirm_delete', None)
                    st.rerun()
                if cc2.button('Annuler', key='delno_' + proj['name']) :
                    st.session_state.pop('confirm_delete', None)
                    st.rerun()


# ---------------------------------------------------------------------------
# page de création d'un projet
# ---------------------------------------------------------------------------

def page_create() :
    if st.button('← Retour aux projets') :
        goto('home')
    st.header('➕ Nouvelle analyse')
    st.markdown(
        'Un **projet** est créé dans le dossier des projets : il contient le '
        'fichier corpus, les `.cfg` propres au calcul, le journal `run.log` '
        'et les résultats.')

    uploaded = st.file_uploader('Fichier corpus (.txt, format Alceste)', type=['txt'])
    other = st.text_input('...ou chemin d\'un fichier corpus existant', value='')
    src_name = uploaded.name if uploaded is not None else Path(other).name
    default_name = Path(src_name).stem if src_name else ''
    name = st.text_input('Nom du projet', value=default_name)
    name = ''.join(c for c in name if c.isalnum() or c in '_-')

    c1, c2 = st.columns(2)
    lang = c1.selectbox('Langue', LANGS, index=0)
    encoding = c2.text_input('Encodage', value='utf-8')
    with st.expander('Paramètres d\'import du corpus (segmentation, '
                     'lemmatisation, nettoyage...)') :
        corpus_params = _params_editor('corpus')

    st.subheader('Traitements')
    selected, all_params = treatments_editor(corpus=None)
    python = python_field()

    ready = bool(name) and (uploaded is not None or other.strip())
    if not ready :
        st.caption('indiquer un fichier corpus et un nom de projet pour continuer')
    if st.button('Créer le projet et lancer le calcul', type='primary',
                 disabled=not ready or not selected) :
        project_dir = projects_root() / name
        if project_dir.exists() :
            st.error('le projet %s existe déjà — choisir un autre nom' % name)
            return
        project_dir.mkdir(parents=True)
        # copie du corpus dans le projet (le projet est autoportant)
        if uploaded is not None :
            corpus_file = project_dir / uploaded.name
            corpus_file.write_bytes(uploaded.getvalue())
        else :
            src = Path(other.strip()).expanduser()
            if not src.exists() :
                st.error('fichier introuvable : %s' % src)
                return
            corpus_file = project_dir / src.name
            corpus_file.write_bytes(src.read_bytes())
        written = write_cfgs(project_dir, selected, all_params, corpus_params)
        ok, cira = launch_pipeline(python, project_dir, selected, written,
                                   corpus_file=corpus_file, lang=lang,
                                   encoding=encoding)
        if ok and cira :
            st.success('projet créé : %s' % project_dir)
            load_corpus.clear()
            goto('project', project=str(project_dir))
        elif cira :
            st.warning('projet créé avec des erreurs (voir le journal '
                       'ci-dessus) : %s' % project_dir)
        else :
            st.error('la construction du corpus a échoué — le projet %s '
                     'contient le journal run.log' % project_dir)


# ---------------------------------------------------------------------------
# page projet : exploration + nouveau traitement + suppression d'analyses
# ---------------------------------------------------------------------------

def page_project_run(project_dir, corpus) :
    st.header('🚀 Nouveau traitement')
    st.markdown('Les `.cfg` et le journal sont écrits dans le dossier du '
                'projet : `%s`' % project_dir)
    mode = st.radio('Corpus', ['corpus du projet (déjà construit)',
                               'nouveau fichier corpus dans ce projet'],
                    horizontal=True)
    newmode = mode.startswith('nouveau')
    corpus_file = corpus_cira = None
    lang = encoding = None
    corpus_params = None
    if newmode :
        uploaded = st.file_uploader('Fichier corpus (.txt)', type=['txt'])
        candidates = sorted(str(p) for p in Path(project_dir).glob('*.txt'))
        source = st.selectbox('...ou un fichier déjà dans le projet',
                              ['(aucun)'] + candidates)
        c1, c2 = st.columns(2)
        lang = c1.selectbox('Langue', LANGS, index=0)
        encoding = c2.text_input('Encodage', value='utf-8')
        with st.expander('Paramètres d\'import du corpus') :
            corpus_params = _params_editor('corpus')
        if uploaded is not None :
            corpus_file = Path(project_dir) / uploaded.name
            if not corpus_file.exists() :
                corpus_file.write_bytes(uploaded.getvalue())
        elif source != '(aucun)' :
            corpus_file = source
    else :
        if corpus is None :
            st.warning('pas encore de corpus construit dans ce projet')
            return
        corpus_cira = str(corpus.cira)
        lang = corpus.parametres.get('lang')
        st.info('corpus : **%s** (`%s`)' % (corpus.name, corpus_cira))

    st.subheader('Traitements')
    selected, all_params = treatments_editor(corpus=None if newmode else corpus)
    python = python_field()

    ready = bool(selected) and (corpus_cira is not None or corpus_file is not None)
    if st.button('Lancer le calcul', type='primary', disabled=not ready) :
        written = write_cfgs(project_dir, selected, all_params,
                             corpus_params if newmode else None)
        ok, cira = launch_pipeline(python, project_dir, selected, written,
                                   corpus_file=corpus_file, corpus_cira=corpus_cira,
                                   lang=lang, encoding=encoding if newmode else None)
        load_corpus.clear()
        if ok :
            st.success('terminé — les nouveaux résultats sont dans la barre latérale')


def analysis_delete_panel(analysis) :
    with st.expander('🗑️ Supprimer cette analyse') :
        st.warning('Suppression définitive du répertoire %s' % analysis.path)
        if st.checkbox('je confirme', key='confdel_' + analysis.name) :
            if st.button('Supprimer', key='dodel_' + analysis.name, type='primary') :
                delete_analysis(analysis.path)
                load_corpus.clear()
                st.rerun()


def page_project() :
    project_dir = st.session_state.get('project')
    if not project_dir or not Path(project_dir).exists() :
        goto('home')
    st.sidebar.title(Path(project_dir).name)
    if st.sidebar.button('← Projets') :
        goto('home')
    corpora = discover_corpora(project_dir)
    corpus = None
    if corpora :
        by_name = {Path(p).name : str(p) for p in corpora}
        name = st.sidebar.selectbox('Corpus', sorted(by_name))
        choice = by_name[name]
        corpus = load_corpus(choice, corpus_signature(choice))

    entries = ['📄 Corpus'] if corpus is not None else []
    if corpus is not None :
        entries += ['%s %s' % (ICONS.get(a.type, '📁'), a.name) for a in corpus.analyses]
    entries.append('🚀 Nouveau traitement')
    page = st.sidebar.radio('Navigation', entries)
    if st.sidebar.button('🔄 Actualiser') :
        load_corpus.clear()
        st.rerun()

    if page == '🚀 Nouveau traitement' :
        page_project_run(project_dir, corpus)
    elif page == '📄 Corpus' :
        page_corpus(corpus)
    else :
        analysis = corpus.analyses[entries.index(page) - 1]
        RENDERERS.get(analysis.type, page_generic)(corpus, analysis)
        analysis_delete_panel(analysis)


# ---------------------------------------------------------------------------
# navigation
# ---------------------------------------------------------------------------

def main() :
    view = st.session_state.get('view', 'home')
    if view == 'create' :
        page_create()
    elif view == 'project' :
        page_project()
    else :
        page_home()


main()
