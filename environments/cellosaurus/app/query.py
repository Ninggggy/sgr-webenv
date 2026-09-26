"""Local query semantics; FTS candidate sets never define presentation ranking."""
import re,sqlite3,unicodedata
from search_text import indexed
class QueryError(ValueError):pass
def normalize(s):return unicodedata.normalize('NFKC',s).casefold()
def search(db,q):
 q=q.strip()
 if not q:return []
 if len(q)>1000:raise QueryError('Query is too long')
 if any(x in q for x in ['(',')','~','^','?','[',']','{','}']):raise QueryError('This query syntax has not been reproduced in the offline release')
 # Main-site punctuation behavior was observed independently from the API.
 literal_q=q
 # ':' is punctuation inside a phrase here, not an API field selector.
 tokens=re.findall(r'"[^"\n]*"|\x27[^\x27\n]*\x27|\S+',q)
 if sum(t.count('"') for t in tokens)%2 or sum(t.count("'") for t in tokens)%2:raise QueryError('Unclosed quoted phrase')
 expr=[];need_term=True
 for t in tokens:
  if t in ['AND','OR','NOT']:
   if need_term:raise QueryError('Operator has no left operand')
   expr.append(t);need_term=True;continue
  if not need_term:expr.append('AND')
  term=t.strip('"\x27')
  if not re.search(r'\w',term):raise QueryError('Query needs a word or identifier')
  expr.append('"'+indexed(term)+'"');need_term=False
 if need_term:raise QueryError('Missing operand')
 try:rows=db.execute('SELECT c.ac,c.name,c.species FROM search s JOIN cell c ON c.ac=s.ac WHERE search MATCH ?',(' '.join(expr),)).fetchall()
 except sqlite3.OperationalError as e:raise QueryError('Invalid search expression') from e
 exact=normalize(literal_q) if re.fullmatch(r'[\w /.-]+',literal_q) else ''
 # Original responses vary within equal casefold names; use an accession tie-break.
 rows.sort(key=lambda r:((normalize(r[1])!=exact and normalize(r[0])!=exact),normalize(r[1]),r[0]));return rows
