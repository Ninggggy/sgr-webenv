from html.parser import HTMLParser
class Page(HTMLParser):
 def __init__(self):
  super().__init__();self.tables=[];self.rows=None;self.row=None;self.cell=None;self.heading=None;self.head='';self.text=[];self.skip=0
 def handle_starttag(self,t,a):
  if t in ('script','style'):self.skip+=1
  if t in ('h1','h2','h3'):self.heading=[]
  if t=='table':self.rows=[];self.tablehead=self.head
  if t=='tr' and self.rows is not None:self.row=[]
  if t in ('td','th') and self.row is not None:self.cell=[]
 def handle_data(self,s):
  if self.skip:return
  if s.strip():self.text.append(s.strip())
  if self.heading is not None:self.heading.append(s)
  if self.cell is not None:self.cell.append(s)
 def handle_endtag(self,t):
  if t in ('script','style'):self.skip=max(0,self.skip-1)
  if t in ('h1','h2','h3') and self.heading is not None:self.head=' '.join(''.join(self.heading).split());self.heading=None
  if t in ('td','th') and self.cell is not None:self.row.append(' '.join(''.join(self.cell).split()));self.cell=None
  if t=='tr' and self.row is not None:self.rows.append(self.row);self.row=None
  if t=='table' and self.rows is not None:self.tables.append({'heading':self.tablehead,'rows':self.rows});self.rows=None
