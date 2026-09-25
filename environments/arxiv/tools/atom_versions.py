"""Parse explicitly versioned official API entries with exact identity checks."""
import re
import xml.etree.ElementTree as ET

ATOM='http://www.w3.org/2005/Atom'
ARXIV='http://arxiv.org/schemas/atom'
ID=re.compile(r'(?:\d{4}\.\d{4,5}|[a-z][a-z.-]*/\d{7})v[1-9]\d*\Z')


def parse(body,requested):
    if not all(ID.fullmatch(x) for x in requested):raise ValueError('Explicit version IDs required')
    root=ET.fromstring(body)
    if root.tag!='{'+ATOM+'}feed':raise ValueError('Not an Atom feed')
    results={}
    for entry in root.findall('{'+ATOM+'}entry'):
        def text(name,ns=ATOM):return entry.findtext('{'+ns+'}'+name)
        ident=(text('id') or '').split('/abs/',1)[-1]
        if ident not in requested or ident in results:raise ValueError('Unexpected or duplicate version '+ident)
        primary=entry.find('{'+ARXIV+'}primary_category')
        if primary is None or not primary.get('term'):raise ValueError('Missing primary category')
        categories=[n.get('term') for n in entry.findall('{'+ATOM+'}category') if n.get('scheme') in ('http://arxiv.org/schemas/atom',None)]
        # Keep primary first explicitly; API categories need not arrive ordered.
        cats=[primary.get('term')]+[c for c in categories if c!=primary.get('term')]
        authors=[];affiliations=[]
        for a in entry.findall('{'+ATOM+'}author'):
            name=a.findtext('{'+ATOM+'}name')
            if not name:raise ValueError('Missing author name')
            authors.append(name)
            affiliations.append({'name':name,'affiliations':[n.text for n in a.findall('{'+ARXIV+'}affiliation')]})
        fields={'title':' '.join((text('title') or '').split()),'abstract':text('summary'),
                'authors':', '.join(authors),'authors_list':authors,'author_affiliations':affiliations,
                'primary_category':primary.get('term'),'categories':' '.join(cats),
                'comments':text('comment',ARXIV),'journal_ref':text('journal_ref',ARXIV),
                'doi':text('doi',ARXIV),'license':None,'report_num':None,'msc_class':None,'acm_class':None,
                'submitted_at':text('updated'),'first_submitted_at':text('published'),
                'source':'https://export.arxiv.org/api/query?id_list='+ident,
                'unavailable_fields':['report_num','msc_class','acm_class','license']}
        if not fields['title'] or not fields['abstract'] or not fields['submitted_at']:
            raise ValueError('Incomplete version '+ident)
        results[ident]=fields
    if set(results)!=set(requested):raise ValueError('API omitted requested versions: '+str(set(requested)-set(results)))
    return results
