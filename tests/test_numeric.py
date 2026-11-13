import importlib.util
from pathlib import Path
from unittest.mock import Mock
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('numeric',ROOT/'scripts'/'numeric.py')
numeric=importlib.util.module_from_spec(spec);spec.loader.exec_module(numeric)

def page(title,paragraph,date='2026-11-10'):
 return f'<html><head><meta property="article:published_time" content="{date}T08:00:00Z"></head><body><main><h1>{title}</h1><p>{paragraph}</p></main></body></html>'

def test_abc_positive():
 html=page('ABC’s Construction Backlog Indicator Drops in October','Associated Builders and Contractors reported today that its Construction Backlog Indicator fell to 8.1 months in October, according to an ABC member survey.')
 rows,issues=numeric.extract('https://www.abc.org/News-Media/News-Releases/abc-backlog-test',html)
 assert len(rows)==1 and rows[0]['value']==8.1 and rows[0]['period']=='October 2026',issues

def test_dmi_positive():
 html=page('Dodge Momentum Index – October 2026','The Dodge Momentum Index (DMI), issued by Dodge Construction Network, declined 9.0% in October to 260.4 (2000=100) from the revised September reading.',date='2026-11-06')
 rows,issues=numeric.extract('https://www.construction.com/dodge-momentum-index-test/',html)
 assert len(rows)==1 and rows[0]['value']==260.4,issues

def test_abi_positive():
 html=page('ABI September 2026: Architecture firm billings slump deepens','The AIA/Deltek Architecture Billings Index® (ABI) score of 44.7 for the month shows further weakening from August.',date='2026-10-21')
 rows,issues=numeric.extract('https://www.aia.org/resource-center/abi-september-2026-test',html)
 assert len(rows)==1 and rows[0]['value']==44.7,issues

def test_dodge_starts_positive():
 html=page('Construction Starts – September 2026','Total construction starts declined 1.5% in September to a seasonally adjusted annual rate of $1.33 trillion, according to Dodge Construction Network. On a year-to-date basis, total construction starts were up 14.3% through September.',date='2026-10-21')
 rows,issues=numeric.extract('https://www.construction.com/construction-starts-recede-test/',html)
 assert len(rows)==2 and {x['label']:x['value'] for x in rows}=={'Total construction starts annualized':1330,'Total construction starts YTD':14.3},issues

def test_reject_ambiguous():
 html=page('ABC Construction Backlog Indicator in October','Construction Backlog Indicator fell to 8.1 months in October. Construction Backlog Indicator fell to 8.9 months in October.')
 rows,issues=numeric.extract('https://www.abc.org/News-Media/News-Releases/abc-backlog-test',html)
 assert not rows and issues

def test_reject_unapproved_source():
 rows,issues=numeric.extract('https://example.com/abc-backlog',page('ABC backlog','Construction Backlog Indicator fell to 8.1 months in October.'))
 assert not rows
