#!/usr/bin/env python3
"""Stream a consistent runtime archive to stdout; does not publish it.

Review redistribution terms before uploading. No images, author work directories,
private task material or original compressed downloads belong in --data.
"""
import argparse,gzip,shutil,sqlite3,sys,tarfile,tempfile
from pathlib import Path

def portable(info):
 info.uid=info.gid=0;info.uname=info.gname="";info.mode=0o644
 return info

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--data',type=Path,required=True);p.add_argument('--temporary-dir',type=Path,required=True);p.add_argument('--file',action='append',help='Relative file allowlist; otherwise include runtime data directory');a=p.parse_args()
 if shutil.disk_usage('/').free<5*1024**3:raise RuntimeError('Root free space below 5 GiB')
 root=a.data.resolve();files=[root/f for f in a.file] if a.file else sorted(root.rglob('*'))
 with tempfile.TemporaryDirectory(prefix='sgr-export-',dir=a.temporary_dir) as temp,gzip.GzipFile(fileobj=sys.stdout.buffer,mode='wb',compresslevel=3) as gz,tarfile.open(fileobj=gz,mode='w|') as archive:
  for f in files:
   if not f.is_file() or f.is_symlink() or f.name.startswith('.') or f.name.endswith(('-wal','-shm')):continue
   relative=f.resolve().relative_to(root)
   if f.suffix in ('.sqlite','.sqlite3','.db'):
    if shutil.disk_usage(a.temporary_dir).free<f.stat().st_size+1024**3:raise RuntimeError('Insufficient backup space')
    dest=Path(temp)/'snapshot.sqlite'
    with sqlite3.connect('file:'+str(f)+'?mode=ro',uri=True) as source,sqlite3.connect(dest) as backup:
     source.backup(backup)
     if backup.execute('pragma quick_check').fetchone()[0]!='ok':raise RuntimeError('Database integrity check failed')
    archive.add(dest,arcname=str(relative),filter=portable);dest.unlink()
   else:archive.add(f,arcname=str(relative),recursive=False,filter=portable)
if __name__=='__main__':main()
