#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os

os.chdir(os.path.dirname(__file__))
with open('data/turkish_series_detail.json','r',encoding='utf-8') as f:
    data = json.load(f)

for s in data:
    seasons = s.get('seasons', [])
    eps = s.get('episodes', [])
    if seasons:
        snums = [ss.get('seasonNumber',0) for ss in seasons]
        print(f'{s["title"][:35]:35s} | seasons={snums} | eps={len(eps)}')
        for ep in eps[:2]:
            print(f'        ep={ep.get("episodeNumber")} sn={ep.get("seasonNumber")} title={ep["title"][:40]}')
