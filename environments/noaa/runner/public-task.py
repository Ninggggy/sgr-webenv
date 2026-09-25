#!/usr/bin/env python3
import json,sys
from pathlib import Path
root=Path(__file__).resolve().parents[3]
if len(sys.argv)!=2:sys.exit("Usage: public-task.py task_id")
for filename in ["constraint.jsonl","goal.jsonl"]:
 for line in (root/"runs/open-source/sgr-bench"/filename).read_text().splitlines():
  t=json.loads(line)
  if t["task_id"]==sys.argv[1]:
   if not t["task_id"].startswith("climategov_"):sys.exit("Not a NOAA task")
   print(json.dumps({"instruction":t["instruction"],"output_format":t["output_format"],"start_url":"http://noaa-web:8080/access/monitoring/climate-at-a-glance/national"},ensure_ascii=False));sys.exit(0)
sys.exit("Unknown task")
