"""Shared text preparation for the full-text index and main-site queries.

Snowball English (Porter2) preserves vowel+y author names, unlike SQLite's
Porter1. Original-site morphology evidence is in docs/search-followup.json.
"""
import re,unicodedata
from functools import lru_cache
from vendor.snowballstemmer.english_stemmer import EnglishStemmer
from threading import local
_tls=local()
@lru_cache(maxsize=65536)
def stem(word):
 if not hasattr(_tls,'stemmer'):_tls.stemmer=EnglishStemmer()
 return _tls.stemmer.stemWord(word)
def text_tokens(text):
 text=unicodedata.normalize('NFKD',text.casefold())
 text=''.join(c for c in text if not unicodedata.combining(c))
 return re.findall(r'\w+',text)
def indexed(text):return ' '.join(stem(word) for word in text_tokens(text))
def record_text(raw):
 # TXT line prefixes are serialization metadata, not words between title fragments.
 return '\n'.join(line[5:] for line in raw.splitlines() if len(line)>5 and line[2:5]=='   ')
def search_body(raw,refs):
 return indexed(record_text(raw)+'\n'+'\n'.join(record_text(ref) for ref in refs))
