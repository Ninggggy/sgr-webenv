"""Parse real version pages; no copying latest content into historical versions."""
from html.parser import HTMLParser
import json
from email.utils import parsedate_to_datetime
import re
from pathlib import Path


class Node:
    def __init__(self, tag='', attrs=()):
        self.tag=tag; self.attrs=dict(attrs); self.children=[]

    def text(self):
        return ''.join(c if isinstance(c,str) else c.text() for c in self.children)

    def source_text(self):
        # Browse abbreviates literal URLs; Atom retains the submitted URL.
        if self.tag == 'a' and self.text().strip() in ('this http URL', 'this https URL'):
            href = self.attrs.get('href', '')
            if href.startswith(('http://', 'https://')):
                return href
        return ''.join(c if isinstance(c,str) else c.source_text() for c in self.children)

    def walk(self):
        yield self
        for child in self.children:
            if isinstance(child,Node): yield from child.walk()


class Page(HTMLParser):
    def __init__(self, body):
        super().__init__(convert_charrefs=True)
        self.root=Node(); self.stack=[self.root]; self.feed(body)

    def handle_starttag(self,tag,attrs):
        node=Node(tag,attrs); self.stack[-1].children.append(node)
        if tag not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):
            self.stack.append(node)

    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag:
                del self.stack[i:];break

    def handle_data(self,data): self.stack[-1].children.append(data)


def parse(body, requested):
    if not re.fullmatch(r'(?:\d{4}\.\d{4,5}|[a-z][a-z.-]*/\d{7})v[1-9]\d*',requested):
        raise ValueError('Require an explicit version ID')
    page=Page(body); nodes=list(page.root.walk())
    title=next((n.text() for n in nodes if n.tag=='title'),'')
    if not title.startswith('['+requested+']'):
        raise ValueError('Response does not identify the requested historical version')
    meta={}
    for n in nodes:
        if n.tag=='meta': meta.setdefault(n.attrs.get('name'),[]).append(n.attrs.get('content',''))
    def by_class(name):
        return next((n for n in nodes if name in n.attrs.get('class','').split()),None)
    def value(name):
        n=by_class(name);return ' '.join(n.text().split()) if n else None
    primary=re.search(r'\(([^()]+)\)$',value('primary-subject') or '')
    if not primary or not meta.get('citation_title') or not meta.get('citation_abstract'):
        raise ValueError('Missing required version fields')
    cells={}; display_cells={}
    for row in nodes:
        if row.tag!='tr':continue
        columns=[n for n in row.children if isinstance(n,Node) and n.tag=='td']
        if len(columns)==2:
            label=re.sub(r'[^a-z]','',columns[0].text().lower())
            display_cells[label]=' '.join(columns[1].text().split())
            cells[label]=' '.join(columns[1].source_text().split())
    fields={'title':meta['citation_title'][0], 'abstract':meta['citation_abstract'][0],
            'authors':re.sub(r'^Authors:\s*','',value('authors') or ''),
            'authors_list':meta.get('citation_author',[]),
            'primary_category':primary.group(1),
            'categories':' '.join(re.findall(r'\(([^()]+)\)',value('subjects') or '')),
            'comments':cells.get('comments'), 'journal_ref':cells.get('journalreference'),
            'report_num':cells.get('reportnumber'),
            'msc_class':value('msc-classes'), 'acm_class':value('acm-classes')}
    # DOI table cell differs from arxiv-issued DOI table cell.
    doi_node=by_class('doi')
    fields['doi']=' '.join(n.attrs['href'].split('doi.org/',1)[1] for n in doi_node.walk()
                           if n.tag=='a' and 'doi.org/' in n.attrs.get('href','')) if doi_node else None
    fields['citation_date']=(meta.get('citation_date') or [None])[0]
    fields['source']='https://arxiv.org/abs/'+requested
    history=value('submission-history') or ''
    submitter=re.search(r'From:\s*(.*?)\s*\[view email\]',history)
    fields['submitter_name']=submitter.group(1) if submitter else None
    fields['history_display']=[]
    for number,date,size in re.findall(r'\[v(\d+)\]\s*([A-Za-z]{3},.*? UTC)\s*\(([^()]*)\)',history):
        fields['history_display'].append({'number':int(number),'submitted_at':parsedate_to_datetime(date).isoformat(),'size_display':size})
    target=next((v for v in fields['history_display'] if v['number']==int(requested.rsplit('v',1)[1])),None)
    if not target:raise ValueError('Requested version missing from displayed submission history')
    fields['submitted_at']=target['submitted_at']
    license_node=by_class('abs-license')
    fields['license']=next((n.attrs['href'] for n in license_node.walk() if n.tag=='a' and n.attrs.get('href')),None) if license_node else None
    full_text=by_class('full-text')
    fields['download_entrances']=[{'label':' '.join(n.text().split()),'href':n.attrs['href']} for n in full_text.walk() if n.tag=='a' and 'abs-button' in n.attrs.get('class','').split() and n.attrs.get('href')] if full_text else []
    fields['html_fields_acquired']=True
    fields['metadata_display']=display_cells
    return fields


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('html',type=Path);p.add_argument('version_id')
    args=p.parse_args();print(json.dumps(parse(args.html.read_text(),args.version_id),ensure_ascii=False,indent=2))
