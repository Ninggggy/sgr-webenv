"""Metadata-backed calendar browsing with official list templates.
Daily event lists are handled separately; a month is never treated as a day.
"""
import calendar
import datetime as dt
import re
import sqlite3
from types import SimpleNamespace
from urllib.parse import urlencode
from flask import Blueprint,request,abort,render_template,redirect
from arxiv.taxonomy import get_category_display
from arxiv.taxonomy.definitions import CATEGORIES,ARCHIVES
from arxiv.util.authors import parse_author_affil_utf
from scope_policy import unsupported, DAILY
from source_scope import primary_category,equivalent_categories,groups,is_primary_context

bp=Blueprint('browse',__name__)
DB='/data/metadata.sqlite'

class Category(str):
 def display(self):return get_category_display(str(self))


def connection():
 d=sqlite3.connect('file:'+DB+'?mode=ro',uri=True);d.row_factory=sqlite3.Row;d.create_function('is_primary_context',2,is_primary_context);return d


def permitted(context):
 return context in (set(ARCHIVES)|set(CATEGORIES)) and bool(groups(context))


def available(d):
 return d.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='catalog'").fetchone()


def period(value,asof):
 if value=='current':return asof[:7]
 if re.fullmatch(r'\d{2}',value):return str((1900 if int(value)>=90 else 2000)+int(value))
 if re.fullmatch(r'\d{6}',value):return value[:4]+'-'+value[4:]
 if re.fullmatch(r'\d{4}-\d',value):return value[:5]+'0'+value[-1]
 if not re.fullmatch(r'\d{4}(-\d{2})?',value):abort(400)
 if len(value)==7:
  try:dt.date.fromisoformat(value+'-01')
  except ValueError:abort(400)
 return value


def article(row):
 data=dict(row);cats=data['categories'].split();primary=primary_category(data['categories'])
 data['primary_category']=Category(primary)
 data['secondary_categories']=[Category(c) for c in cats if c not in equivalent_categories(primary)]
 data['display_secondaries']=lambda:[c.display() for c in data['secondary_categories']]
 data['arxiv_id']=data['id'];data['arxiv_id_v']=data['id']+'v'+str(data['version'])
 return SimpleNamespace(**data)


def authors_for(article):
 parts=[]
 for last,first,suffix,*_ in parse_author_affil_utf(article.authors or ''):
  if parts:parts.append(', ')
  parts.append((' '.join(x for x in (first,last,suffix) if x),last+', '+first))
 return (parts,None)


@bp.get('/list/<context>/<subcontext>')
def list_articles(context,subcontext):
 if context not in (set(ARCHIVES)|set(CATEGORIES)):abort(404)
 if subcontext in ('new','recent','pastweek','catchup'):return unsupported(DAILY)
 if not permitted(context):return render_template('notice.html',message='This archive is outside the complete cs/math/stat scope.'),503
 with connection() as d:
  if not available(d):return render_template('notice.html',message='Calendar coverage is unavailable in this dataset.'),503
  asof=d.execute('select max(response_date) from harvest_state').fetchone()[0]
  normalized=period(subcontext,asof)
  if normalized!=subcontext:return redirect('/list/'+context+'/'+normalized,301)
  if int(normalized[:4])<1990:abort(400)
  if normalized[:4]>asof[:4]:abort(404)
  if len(normalized)==7 and normalized>asof[:7]:
   return render_template('notice.html',message='This month is later than the published data reference date; its coverage is unavailable.'),503
  try:
   skip=int(request.args.get('skip','0'));shown=int(request.args.get('show','25'))
  except ValueError:abort(400)
  if skip<0 or shown<1 or shown>2000:abort(400)
  if set(request.args)-{'skip','show'}:abort(400)
  where='c.context=? AND c.month LIKE ?';params=(context,normalized+'%')
  count=d.execute('SELECT count(*) FROM catalog c WHERE '+where,params).fetchone()[0]
  rows=d.execute('SELECT r.*, (SELECT max(number) FROM versions WHERE paper_id=r.id) AS version FROM catalog c JOIN records r ON r.id=c.paper_id WHERE '+where+' ORDER BY c.month,is_primary_context(r.categories,?) DESC,r.id LIMIT ? OFFSET ?',(*params,context,shown,skip)).fetchall()
 articles=[article(r) for r in rows]
 items=[{'article':a,'list_index':skip+i+1,'listingType':'' if is_primary_context(rows[i]['categories'],context) else 'cross','primary':a.primary_category} for i,a in enumerate(articles)]
 def url(n,s=shown):return '/list/'+context+'/'+normalized+'?'+urlencode({'skip':n,'show':s})
 pages=[]
 # Same numbered ranges, with bounded links for very large lists.
 current=skip//shown;total=(count+shown-1)//shown
 positions=sorted({0,total-1,*range(max(0,current-2),min(total,current+3))}) if total else []
 prior=-1
 for p in positions:
  if p<0:continue
  if p>prior+1:pages.append({'nolink':'...'})
  text=f'{p*shown+1}-{min(count,(p+1)*shown)}'
  pages.append({'nolink':text} if p==current else {'url':url(p*shown),'txt':text});prior=p
 values=[25,50,100,250,500,1000,2000]
 name=ARCHIVES.get(context,{}).get('name') or CATEGORIES.get(context,{}).get('name',context)
 return render_template('list/month.html' if len(normalized)==7 else 'list/year.html',
  paper=SimpleNamespace(id=''),browse_archive=context,header_context=name,pagetitle=name+' '+normalized,
  list_ctx_name=name,list_month_name='',list_year=normalized[:4],pubmonth=dt.datetime.strptime(normalized[:7] if len(normalized)==7 else normalized+'-01','%Y-%m'),
  count=count,shown=shown,skipn=skip,context=context,subcontext=normalized,list_type='month',
  listings=items,paging=pages,viewing_all=count<=shown,mf_fewer=max([x for x in values if x<shown],default=None),
  mf_more=next((x for x in values if shown<x<count),None),mf_all=2000 if shown<min(count,2000) else None,
  author_links={a.arxiv_id_v:authors_for(a) for a in articles},downloads={a.arxiv_id_v:['pdf','other'] for a in articles},latexml={},
  url_for_author_search=lambda a,q:'/search/?'+urlencode({'query':q,'searchtype':'author'}))


@bp.get('/archive/<category>')
def archive(category):
 from wtforms import Form,HiddenField,SelectField,SubmitField
 if category not in (set(ARCHIVES)|set(CATEGORIES)):abort(404)
 if not permitted(category):return render_template('notice.html',message='This archive is outside the complete cs/math/stat scope.'),503
 # Original Browse resolves a category landing URL to its enclosing archive.
 ident=CATEGORIES.get(category,{}).get('in_archive',category)
 definition=ARCHIVES.get(ident)
 if not definition:abort(404)
 with connection() as d:
  asof=dt.date.fromisoformat(d.execute('select max(response_date) from harvest_state').fetchone()[0][:10])
 start=definition['start_date'];end=definition.get('end_date') or asof
 operating=list(range(end.year,start.year-1,-1))
 categories=[SimpleNamespace(id=k,full_name=v['name'],description=v.get('description','')) for k,v in sorted(CATEGORIES.items()) if v.get('in_archive')==ident and v.get('is_active')]
 archive=SimpleNamespace(id=ident,full_name=definition['name'],start_date=start,get_categories=lambda:categories)
 class ByMonthForm(Form):
  archive=HiddenField('archive');year=SelectField('year');month=SelectField('month');submit=SubmitField('Go')
 form=ByMonthForm();form.archive.data=ident
 form.year.choices=[(str(y),str(y)) for y in operating]
 form.month.choices=[('all','all months')]+[(f'{i:02d}',f'{i:02d} ({calendar.month_abbr[i]})') for i in range(1,13)]
 return render_template('archive.html',paper=SimpleNamespace(id=''),browse_archive=ident,header_context=definition['name'],pagetitle=definition['name'],
  archive=archive,archive_id=ident,list_form=form,category_list=categories,subsumed_id=None,
  stats_by_year=[('/year/'+ident+'/'+str(y),str(y)) for y in operating],years=[asof.year,asof.year-1],
  months=[(f'{i:02d}',f'{i:02d} ({calendar.month_abbr[i]})') for i in range(1,13)],days=[f'{i:02d}' for i in range(1,32)],current_month=f'{asof.month:02d}')


@bp.get('/year/<context>/<int:year>')
def year_statistics(context,year):
 if context not in ARCHIVES:abort(404)
 if not permitted(context):return render_template('notice.html',message='This archive is outside the complete cs/math/stat scope.'),503
 if year<100:return redirect('/year/'+context+'/'+str(1900+year if year>=91 else 2000+year),301)
 definition=ARCHIVES[context]
 with connection() as d:
  asof=dt.date.fromisoformat(d.execute('SELECT max(response_date) FROM harvest_state').fetchone()[0][:10])
  if year>asof.year:abort(404)
  if year<definition['start_date'].year:abort(400)
  rows=d.execute('SELECT c.month,sum(is_primary_context(r.categories,?)) AS primary_count,count(*) AS total FROM catalog c JOIN records r ON r.id=c.paper_id WHERE c.context=? AND c.month LIKE ? GROUP BY c.month ORDER BY c.month',(context,context,str(year)+'-%')).fetchall()
 months=[];new_count=0;cross_count=0
 for row in rows:
  month=int(row['month'][5:]);new=row['primary_count'];cross=row['total']-new;total=new+cross
  url='/list/'+context+'/'+row['month']
  art=[('|',url+'?skip='+str(i) if i%100==0 else None) for i in range(0,total,20)]
  if total%20>=10:art.append(('!',None))
  months.append(SimpleNamespace(month_count=SimpleNamespace(new=new,cross=cross),art=art,yymm=f'{month:02d}',my=dt.date(year,month,1).strftime('%b %Y'),url=url))
  new_count+=new;cross_count+=cross
 years=range(asof.year,definition['start_date'].year-1,-1)
 return render_template('year.html',paper=SimpleNamespace(id=''),browse_archive=context,header_context=definition['name'],pagetitle=definition['name']+' '+str(year),
  archive=SimpleNamespace(id=context,full_name=definition['name']),year=str(year),month_data=months,
  listing=SimpleNamespace(new_count=new_count,cross_count=cross_count),stats_by_year=[('' if y==year else '/year/'+context+'/'+str(y),str(y)) for y in years])


@bp.get('/catchup/<subject>/<date>')
def catchup(subject,date):
 if subject not in (set(ARCHIVES)|set(CATEGORIES)):abort(404)
 try:day=dt.date.fromisoformat(date);page=int(request.args.get('page','1'))
 except ValueError:abort(400)
 if page<1 or request.args.get('abs','False') not in ('True','False'):abort(400)
 if set(request.args)-{'abs','page'}:abort(400)
 return unsupported(DAILY)


@bp.get('/catchup')
def catchup_form():
 return unsupported(DAILY)


@bp.get('/multi')
def multi():
 group=request.args.get('group','grp_cs').removeprefix('grp_')
 if '/catchup' in request.args:return redirect('/catchup?'+urlencode({'group':'grp_'+group}),302)
 fields={'cs':'computer_science','math':'mathematics','stat':'statistics'}
 if group not in fields:return render_template('notice.html',message='This group is outside the complete offline scope.'),503
 return redirect('/search/advanced?'+urlencode({'advanced':'1','classification-'+fields[group]:'y'}),302)


@bp.get('/list/')
def list_form():
 context=request.args.get('archive','');year=request.args.get('year','');month=request.args.get('month','all')
 if not permitted(context) or not re.fullmatch(r'\d{4}',year):abort(400)
 if month in ('all','0',''):period=year
 else:
  try:value=int(month);dt.date(int(year),value,1)
  except ValueError:abort(400)
  period=year+f'-{value:02d}'
 return redirect('/list/'+context+'/'+period,302)
