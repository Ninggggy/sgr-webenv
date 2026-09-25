"""Offline adapter. Author collectors and task material are not part of this image."""
import datetime as dt
import json
import os
import re
import sqlite3
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit, urlencode, parse_qs

os.environ.setdefault('URL_PREFIX', '/search/')
os.environ.setdefault('ELASTICSEARCH_SERVICE_HOST', 'search')
os.environ.setdefault('ELASTICSEARCH_INDEX', 'arxiv')
os.environ.setdefault('ELASTICSEARCH_MAPPING', '/opt/search/mappings/DocumentMapping.json')
os.environ.setdefault('AWS_EC2_METADATA_DISABLED', 'true')

from flask import Flask, abort, redirect, render_template, request, Response, send_from_directory, url_for
from markupsafe import Markup
from types import SimpleNamespace
from official_cite import arxiv_bibtex
from scope_policy import unsupported, HISTORY, DAILY, IDENTIFIERS, EXCLUDED
from source_scope import primary_category,equivalent_categories,groups,announcement_month,classification
from jinja2 import ChoiceLoader, FileSystemLoader
from lxml import html
from arxiv.base import Base
from arxiv.base.urls import urlizer
from search.routes import ui, classic_api
from search.services.index import SearchSession
from search.converters import ArchiveConverter
from search.filters import filters
from arxiv.taxonomy import get_category_display
from arxiv.taxonomy.definitions import GROUPS,ARCHIVES_ACTIVE,CATEGORIES_ACTIVE
from arxiv.util.authors import parse_author_affil_utf

# Same UI controllers, forms, query builder and index client as the official
# factory, without its cloud static-file extension or production middleware.
app = Flask('search')
app.config.from_pyfile('config.py')
app.url_map.converters['archive'] = ArchiveConverter
SearchSession.init_app(app)
Base(app)
app.add_template_filter(urlizer(['arxiv_id','doi','url']),'arxiv_urlize')
app.register_blueprint(ui.blueprint)
for error_type,handler in classic_api.exceptions.get_handlers():
    classic_api.blueprint.register_error_handler(error_type,handler)
app.register_blueprint(classic_api.blueprint)
for name, function in filters:
    app.add_template_filter(function, name)
app.config.update(ANALYTICS_ENABLED=False, FLASKS3_ACTIVE=False, SERVER_NAME=None,
                  MAX_CONTENT_LENGTH=1024*1024)
app.jinja_loader = ChoiceLoader([FileSystemLoader('/app/templates'), app.jinja_loader])
# Cookie defaults in upstream couple independent tabs. Query state is entirely
# explicit in URLs in this offline adapter; no server session is used.
app.before_request_funcs['ui'] = [f for f in app.before_request_funcs.get('ui', [])
                                  if f.__name__ != 'get_parameters_from_cookie']
app.after_request_funcs['ui'] = [f for f in app.after_request_funcs.get('ui', [])
                                 if f.__name__ != 'set_parameters_in_cookie']
ID = re.compile(r'(?:\d{4}\.\d{4,5}|[a-z][a-z.-]*/\d{7})(?:v[1-9]\d*)?\Z')
DB = '/data/metadata.sqlite'


class Category(str):
    @property
    def id(self): return str(self)
    def display(self):
        return get_category_display(str(self)) if self else 'Primary category not yet acquired'


@app.url_defaults
def version_urls(endpoint,values):
    if endpoint in ('abs','pdf') and values.get('version'):
        values['paper_id']+='v'+str(values.pop('version'))


def database():
    db = sqlite3.connect('file:'+DB+'?mode=ro', uri=True)
    db.row_factory = sqlite3.Row
    return db


@lru_cache(maxsize=1)
def scope():
    with database() as db:
        return {'records':db.execute('SELECT count(*) FROM records').fetchone()[0],
                'sets':[dict(x) for x in db.execute('SELECT source_set,complete,response_date FROM harvest_state')],
                'asof': db.execute('SELECT max(response_date) FROM harvest_state').fetchone()[0]}


from search.controllers import advanced
from search.controllers.advanced import forms as advanced_forms


class SnapshotDate(dt.date):
    @classmethod
    def today(cls):
        value=scope()['asof']
        if not value: raise RuntimeError('Dataset has no source date')
        return cls.fromisoformat(value[:10])


advanced.date=SnapshotDate
advanced_forms.date=SnapshotDate


@app.template_filter('search_display_date')
def search_display_date(value):
    # 112 archived search observations spanning winter/summer use Eastern dates.
    # Keep canonical UTC instants and official query bounds unchanged.
    from pytz import timezone
    return value.astimezone(timezone('US/Eastern')).strftime('%-d %B, %Y')


@app.context_processor
def offline_context():
    return {'offline_scope':scope()}


@app.before_request
def guard_query():
    if request.path=='/api/query':
        params=request.args if request.method=='GET' else request.form
        if request.method=='POST' and not request.headers.get('Content-Type'):
            params={k:v[0] for k,v in parse_qs(request.get_data(as_text=True)).items()}
        if params.get('include_older_versions'):
            return unsupported(HISTORY)
        raw=params.get('search_query','')
        # Do not allow undocumented prefixes to be silently reinterpreted as all-field text.
        tokens=re.findall(r'"[^"\n]*"|[^\s()]+', raw)
        if any(re.match(r'(?:orcid|author_id|au_id|msc|msc_class|acm|acm_class):', t, re.I) for t in tokens):
            return unsupported(IDENTIFIERS)
        if any(re.match(r'(?:full_text|fulltext):', t, re.I) for t in tokens):
            return unsupported(EXCLUDED)
        identifiers=[x.strip() for x in params.get('id_list','').split(',') if x.strip()]
        if raw:
            from search.domain.classic_api.classic_search_query import adapt_query
            from search.domain.classic_api.query_parser import parse_classic_query
            from search.domain.base import Term,Field
            def terms(node):
                if isinstance(node,Term):yield node
                elif isinstance(node,tuple):
                    for child in node[1:]:yield from terms(child)
            for term in terms(parse_classic_query(adapt_query(raw))):
                value=term.value.strip('"')
                if term.field==Field.Identifier:identifiers.append(value)
                if term.field==Field.SubjectCategory and not groups(value):
                    return classic_api.exceptions.respond('This category is outside complete cs/math/stat coverage.',link='/offline',status=503)
        with database() as db:
            for pid in identifiers:
                if not ID.fullmatch(pid):continue  # upstream validates malformed identifiers
                bare,ver=re.fullmatch(r'(.+?)(?:v([1-9]\d*))?',pid).groups()
                row=db.execute('SELECT max(number) FROM versions WHERE paper_id=?',(bare,)).fetchone()
                if not row or row[0] is None:
                    return classic_api.exceptions.respond('Record is outside the acquired offline coverage.',link='/offline',status=404)
                if ver and not db.execute('SELECT 1 FROM versions WHERE paper_id=? AND number=?',(bare,int(ver))).fetchone():
                    return classic_api.exceptions.respond('Unknown version number.',link='/offline',status=404)
                if ver and int(ver)!=row[0]:return unsupported(HISTORY,bare)
    if request.path.startswith('/search'):
        query = request.args.get('query', '').strip().removeprefix('arXiv:')
        if ID.fullmatch(query):
            return redirect('/abs/'+query)
        selected_classes=[k for k,v in request.args.items() if k.startswith('classification-') and v=='y']
        selected_fields=[v for k,v in request.args.items() if k.endswith('-field') or k=='searchtype']
        if any(v in ('full_text','help') for v in selected_fields):return unsupported(EXCLUDED)
        if any(v in ('author_id','orcid','acm_class','msc_class') for v in selected_fields):
            return unsupported(IDENTIFIERS)
        allowed_classes={'classification-computer_science','classification-mathematics','classification-statistics'}
        if set(selected_classes)-allowed_classes:
            return render_template('notice.html', message='This query requests archives outside complete cs/math/stat coverage.'),503
        archives=(request.view_args or {}).get('archives')
        if archives and any(not groups(a) for a in str(archives).split(',')):
            return render_template('notice.html', message='This archive is outside complete cs/math/stat coverage.'),503
        if request.args.get('include_older_versions'):
            return unsupported(HISTORY)


def taxonomy_view():
    homepage_groups={}
    for key,value in GROUPS.items():
        archives=[]
        for ident,a in ARCHIVES_ACTIVE.items():
            if a.get('in_group')!=key:continue
            cats=[SimpleNamespace(id=c,full_name=v['name']) for c,v in CATEGORIES_ACTIVE.items() if v.get('in_archive')==ident]
            archives.append(SimpleNamespace(id=ident,full_name=a['name'],get_categories=lambda cats=cats:cats))
        homepage_groups[key]=SimpleNamespace(id=key,full_name=value['name'],is_active=True,is_test=value.get('is_test',False),get_archives=lambda archives=archives:archives)
    return homepage_groups


@app.get('/')
def home():
    homepage_groups=taxonomy_view()
    return render_template('home.html',groups=homepage_groups,categories=CATEGORIES_ACTIVE,
        paper=SimpleNamespace(id=''),header_context='',browse_archive='cs',pagetitle='arXiv.org e-Print archive')


@app.get('/pdf/<path:paper_id>',endpoint='pdf')
def pdf_notice(paper_id):
    return unsupported(EXCLUDED)


@app.get('/offline')
def offline():
    return render_template('notice.html', message=f'This release contains {scope()["records"]:,} current metadata records covering cs, math and stat, including cross-listings, with complete version numbers and submission timestamps. Source collection extends through {scope()["asof"]}; this is not an instantaneous snapshot. Supported capabilities include current-metadata search, current abstract pages, citations, and year/month browsing. '+HISTORY+' '+DAILY+' '+IDENTIFIERS+' '+EXCLUDED)



@app.get('/offline/unavailable')
def unavailable():
    return unsupported(EXCLUDED)


@app.get('/institutional_banner')
def institutional_banner():
    # No IP-based institution lookup in the offline environment.
    return {'label':None}


@app.get('/health')
def health():
    return {'status':os.environ.get('ARXIV_RELEASE_STATUS','candidate'), 'version':'0.1.0', 'profile':'current-metadata', **scope()}


@app.get('/assets/<path:name>')
def assets(name):
    return send_from_directory('/app/assets', name)


@app.get('/search')
def search_redirect():
    return redirect('/search/'+('?' + request.query_string.decode() if request.query_string else ''))


@app.get('/abs/<path:paper_id>', endpoint='abs')
def abstract(paper_id):
    if not ID.fullmatch(paper_id): abort(404)
    match = re.fullmatch(r'(.+?)(?:v([1-9]\d*))?', paper_id)
    bare, selected = match.groups()
    with database() as db:
        record = db.execute('SELECT * FROM records WHERE id=?', (bare,)).fetchone()
        if not record:
            return render_template('notice.html', message='This record is not present in the local dataset. This is a coverage gap, not evidence that the paper does not exist.'), 404
        history = [dict(v) for v in db.execute('SELECT * FROM versions WHERE paper_id=? ORDER BY number', (bare,))]
    if not history or record['deleted']:
        return render_template('notice.html', message='The source marks this record deleted or supplies no version history.'), 410
    number = int(selected) if selected else history[-1]['number']
    version = next((v for v in history if v['number'] == number), None)
    if not version: abort(404)
    if number != history[-1]['number']:
        return unsupported(HISTORY,bare)
    data = dict(record)
    data['primary_category']=primary_category(data.get('categories'))
    # Display current canonical browse contexts, not every historical alias.
    contexts=set()
    for c in data.get('categories','').split():
        canonical=primary_category(c)
        contexts.add(canonical);contexts.add(classification(canonical)['archive']['id'])
    context=request.args.get('context') or data['primary_category']
    if context not in contexts:abort(400)
    for v in history:
        v['date'] = dt.datetime.fromisoformat(v['submitted_at'])
    authors_markup=Markup(', ').join(Markup('<a href="{}">{}</a>').format(
        url_for('ui.search',query=last+', '+first,searchtype='author',order='-submitted_date'),
        ' '.join(x for x in (first,last,suffix) if x))
        for last,first,suffix,*_ in parse_author_affil_utf(data.get('authors') or ''))
    return render_template('abstract.html', paper=data, number=number, history=history, pagetitle='['+paper_id+'] '+data['title'],
                           authors_markup=authors_markup,browse_context=context,
                           alternate_contexts=sorted(contexts-{context}),announcement_month=announcement_month(bare),
                           current=version, primary=data.get('primary_category'),
                           classification=classification(data.get('primary_category')),
                           current_date=dt.datetime.fromisoformat(version['submitted_at']),
                           browse_archive=(data.get('primary_category') or (data.get('categories') or 'cs').split()[0]).split('.')[0],
                           primary_obj=Category(data.get('primary_category') or ''),
                           secondary_objects=[Category(c) for c in (data.get('categories') or '').split() if c not in equivalent_categories(data.get('primary_category') or '')],
                           original_history=[{'version':v['number'],'submitted_date':v['date']} for v in history])


from browsing import bp as browsing_blueprint
app.register_blueprint(browsing_blueprint)



@app.get('/prevnext')
def prevnext():
    pid=request.args.get('id','');context=request.args.get('context','');direction=request.args.get('function','')
    if set(request.args)-{'id','context','function'} or not ID.fullmatch(pid) or direction not in ('prev','next'):abort(400)
    if not groups(context):return render_template('notice.html',message='Sequential navigation in this context is outside the complete offline scope.'),503
    bare=re.sub(r'v[1-9]\d*$','',pid);month=announcement_month(bare);year,m=map(int,month.split('-'))
    inc=1 if direction=='next' else -1
    y2,m2=divmod(year*12+m-1+inc,12);adjacent=f'{y2:04d}-{m2+1:02d}'
    comparator,order=('>','ASC') if direction=='next' else ('<','DESC')
    # Match the official Browse database's adjacent-month, identifier ordering.
    with database() as d:
        row=d.execute('SELECT paper_id FROM catalog WHERE context=? AND month IN (?,?) AND paper_id '+comparator+' ? ORDER BY paper_id '+order+' LIMIT 1',(context,month,adjacent,bare)).fetchone()
    if not row:abort(404)
    return redirect('/abs/'+row[0]+'?'+urlencode({'context':context}),301)

@app.get('/bibtex/<path:paper_id>')
def bibtex(paper_id):
    if not ID.fullmatch(paper_id): abort(404)
    bare,selected=re.fullmatch(r'(.+?)(?:v([1-9]\d*))?',paper_id).groups()
    with database() as db:
        row=db.execute('SELECT * FROM records WHERE id=?',(bare,)).fetchone()
        versions=[dict(v) for v in db.execute('SELECT * FROM versions WHERE paper_id=? ORDER BY number',(bare,))]
    if not row or not versions:abort(404)
    version=next((v for v in versions if v['number']==int(selected)),None) if selected else versions[-1]
    if not version:abort(404)
    if version['number']!=versions[-1]['number']:
        return unsupported(HISTORY,bare)
    data=dict(row)
    data['primary_category']=primary_category(data.get('categories'))
    primary=data.get('primary_category')
    meta=SimpleNamespace(title=data['title'],authors=SimpleNamespace(raw=data['authors']),
        primary_category=SimpleNamespace(id=primary) if primary else None,
        doi=data.get('doi'),arxiv_id=bare,arxiv_identifier=SimpleNamespace(id=paper_id),
        get_datetime_of_version=lambda n:dt.datetime.fromisoformat(next(v for v in versions if v['number']==(n or versions[-1]['number']))['submitted_at']))
    return Response(arxiv_bibtex(meta),mimetype='text/plain')



@app.get('/<path:path>')
def excluded(path):
    if path.split('/')[0] in ('pdf','html','src','format','e-print','login','user','help','about','show-email','auth','search-help','labs','tb','licenses','donate'):
        return unsupported(EXCLUDED)
    abort(404)


def local_url(value):
    parts=urlsplit(value)
    if '\\' in value or any(ord(c)<32 for c in value):
        return '/offline/unavailable'
    if parts.scheme not in ('http','https',''):
        return value if value == 'javascript:history.back()' else '/offline/unavailable'
    if not parts.netloc:
        return value
    if parts.scheme not in ('http','https','') or parts.username or parts.password:
        return '/offline/unavailable'
    if parts.hostname in ('arxiv.org','export.arxiv.org','info.arxiv.org') and parts.port in (None,80,443):
        return parts.path+('?' + parts.query if parts.query else '')+('#'+parts.fragment if parts.fragment else '')
    return '/offline/unavailable'


@app.after_request
def offline_response(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'self'; frame-src 'none'; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
    if response.headers.get('Location'):
        response.headers['Location']=local_url(response.headers['Location'])
    if response.mimetype == 'text/html' and not response.direct_passthrough:
        tree=html.document_fromstring(response.get_data())
        for node in tree.iter():
            for attr in ('href','src','action'):
                value=node.get(attr)
                if value:
                    try: node.set(attr, local_url(value))
                    except ValueError: node.set(attr,'/offline/unavailable')
        response.set_data(html.tostring(tree, encoding='utf-8', doctype='<!DOCTYPE html>'))
    return response
