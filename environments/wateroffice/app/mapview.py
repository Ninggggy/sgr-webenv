import json,re
from downloads import value_text

def render(template,kind="historical"):
 if kind not in ("historical","real_time"):raise ValueError("Invalid map type")
 s=template('map-accepted' if kind=='historical' else 'index_e-real')
 s=s.replace('<script src="/js/bundle.js"></script>','<script src="/vendor/leaflet/leaflet.js"></script><script src="/js/offline-map.js"></script>')
 s=s.replace('</head>','<link rel="stylesheet" href="/vendor/leaflet/leaflet.css"><style>#menu{z-index:1001}#popup{z-index:1100}.leaflet-container{font:14px Arial,sans-serif}#map{min-height:600px}.leaflet-control-attribution{font-size:10px}</style></head>')
 return s

def stations(db,data,kind):
 if kind not in ('historical','real_time'):raise ValueError('Invalid map type')
 rows=json.loads((data/f'map-stations-{kind}.json').read_text())
 return [dict(source=r,number=r['station_id'],name=r['station_name'],province=r['province'],latitude=float(r['latitude']),longitude=float(r['longitude']),status=r['data_available'],operation=r['operation_schedule'],agency=r['operating_agency_en'],basin=r['basin_id'],partner=r.get('partner_operated','F'),parameters=r.get('parameters',''),conditions=r.get('current_conditions',''),level=value_text(float(r['recent_water_level']),'Level') if r.get('recent_water_level') is not None else None,flow=value_text(float(r['recent_flow']),'Flow') if r.get('recent_flow') is not None else None,level_time=r.get('recent_water_level_datestamp'),flow_time=r.get('recent_flow_datestamp'),timezone=r.get('timezone_abbr_en'),operation_start=r.get('operation_start_month'),operation_end=r.get('operation_end_month')) for r in rows]
