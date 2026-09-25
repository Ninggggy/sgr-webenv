#!/usr/bin/env python3
"""Generate public dictionary from captured official form controls, not author answers."""
import json,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
d=json.loads((root/'validation/original-natality-controls.json').read_text());l=json.loads((root/'validation/original-lbd-controls.json').read_text())
fields={'year':('Year','20'),'month':('Month','25'),'race':("Mother's Single Race 6",'42'),'hispanic':("Mother's Hispanic Origin",'43'),'origin':("Mother's Expanded Hispanic Origin",'4'),'place':('Birthplace','45'),'place6':('Birthplace Recode 6','30'),'place3':('Birthplace Recode 3','46'),'mother_age':('Age of Mother 9','1'),'sex':('Sex of Infant','3'),'gestation':('OE Gestational Age Recode 10','32'),'weight':('Infant Birth Weight 12','9'),'plurality':('Plurality','7')}
result={}
for name,(label,v) in fields.items():
 e=next(x for x in d if x['name']=='V_D149.V'+v)
 result[name]={'label':label,'options':[[o['value'],o['text'].strip()] for o in e['options'] if o['value']!='*All*']}
for name,label,v in [('death_age','Age of Infant at Death 5','13'),('cause','ICD-10 130 Cause List (Infants)','18')]:
 e=next(x for x in l if x['name']=='V_D159.V'+v)
 result[name]={'label':label,'options':[[o['value'],o['text'].strip()] for o in e['options'] if o['value']!='*All*']}
result['death_days']={'label':'Age of Infant at Death in days','options':[[str(i),str(i)+' days'] for i in range(365)]}
# Hierarchy is captured from the official indentation, including rankable # markers.
e=next(x for x in l if x['name']=='V_D159.V18');stack=[];causes={}
for o in e['options'][1:]:
 s=o['text'];indent=len(s)-len(s.lstrip());code=o['value'];label=s.strip()
 while stack and stack[-1][0]>=indent:stack.pop()
 ancestors=[x[1] for x in stack]+[code]
 causes[code]={'label':label,'ancestors':ancestors,'rankable':label.startswith('#')}
 stack.append((indent,code))
result['leading']={'label':'15 Leading Causes of Death (Infants)','options':[[k,v['label']] for k,v in causes.items() if v['rankable']]}
(root/'app/dictionary.json').write_text(json.dumps(result,indent=2))
(root/'app/causes.json').write_text(json.dumps(causes,indent=2))
print(len(causes),'causes;',sum(x['rankable'] for x in causes.values()),'rankable')
