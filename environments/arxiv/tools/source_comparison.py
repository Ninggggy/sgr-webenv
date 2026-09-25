"""Compare source presentations without changing either stored observation."""
import importlib.util
import re
import unicodedata
from pathlib import Path

_path = Path(__file__).resolve().parents[1] / 'upstream/arxiv-base/arxiv/util/tex2utf.py'
_spec = importlib.util.spec_from_file_location('official_tex2utf', _path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)


def normalize(value, field):
    value = unicodedata.normalize('NFC', _module.tex2utf(value or ''))
    if field == 'authors':
        # Same punctuation spacing as official arxiv.util.authors._tidy_name.
        value = re.sub(r'(?<!\\)\.(\S)', r'. \g<1>', value)
    return ' '.join(value.split())
