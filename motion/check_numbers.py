#!/usr/bin/env python3
"""Audit every number printed in the compositions and the script against the brief/ledger allow-list; no em/en dashes."""
import re, os, json, sys
here = os.path.dirname(os.path.abspath(__file__))
ALLOWED = {'7', '10', '5', '90', '1.25', '2,000,000', '1,800,000', '100,000', '1', '2026', '50', '8.1', '2', '0'}
# allowed contexts: 7(a); 10%; 5%; 90%; 1.25x; $2,000,000; $1,800,000; $100,000; October 1, 2026; SOP 50 10 8.1; "2026" credit; 'a 5%'
bad = []
for f in sorted(os.listdir(os.path.join(here, 'compositions'))):
    s = open(os.path.join(here, 'compositions', f)).read()
    txt = re.sub(r'<style>.*?</style>', '', s, flags=re.S)
    txt = re.sub(r'<script>.*?</script>', '', txt, flags=re.S)
    txt = re.sub(r'<svg.*?</svg>', '', txt, flags=re.S)
    txt = re.sub(r'style="[^"]*"', '', txt)
    txt = re.sub(r'<[^>]+>', ' ', txt)
    for m in re.findall(r'\$?\d[\d,]*(?:\.\d+)?', txt):
        n = m.lstrip('$').rstrip(',')
        if n not in ALLOWED: bad.append((f, m))
    if re.search('[—–]', s): bad.append((f, 'dash'))
S = json.load(open(os.path.join(here, 'script.json')))
for sc in S['scenes']:
    for k in ('vo', 'caption'):
        if re.search('[—–]', sc[k]): bad.append((sc['id'], 'dash in ' + k))
        for w in ('record', 'transcri', 'taped'):
            if w in sc[k].lower(): bad.append((sc['id'], w))
print('numbers/dashes audit:', 'OK' if not bad else bad)
sys.exit(1 if bad else 0)
