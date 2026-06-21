#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, re, urllib.request, urllib.parse

with open('data/turkish_series_full.json','r',encoding='utf-8') as f:
    data = json.load(f)

for s in data:
    vid = s.get('vid','')
    if vid:
        print('Series:', s['title'], 'vid:', vid)
        url = 'https://yam.ahwaktv.net/watch.php?vid=' + vid
        req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=20).read().decode('utf-8','replace')
        with open('watch_page_sample.html','w',encoding='utf-8') as f2:
            f2.write(html)
        print('Watch page:', len(html), 'chars')

        m = re.search(r'view-serie\.php\?name=([^"\'&]+)', html)
        if m:
            name = urllib.parse.unquote(m.group(1).replace('-', ' ').replace('+', ' '))
            print('Series name from page:', name)
            print('Full link: view-serie.php?name=' + m.group(1))
            serie_url = 'https://yam.ahwaktv.net/view-serie.php?name=' + m.group(1)
            req2 = urllib.request.Request(serie_url, headers={'User-Agent':'Mozilla/5.0'})
            html2 = urllib.request.urlopen(req2, timeout=20).read().decode('utf-8','replace')
            with open('view_serie_sample.html','w',encoding='utf-8') as f3:
                f3.write(html2)
            print('Serie page:', len(html2), 'chars')
            if '\u0647\u0630\u0627 \u0627\u0644\u0645\u0633\u0644\u0633\u0644 \u063a\u064a\u0631 \u0645\u062a\u0648\u0641\u0631' in html2:
                print('WARNING: not available')
            
            seasons_sec = re.findall(r'seasons-sec|SeasonsEpisodes|data-season', html2)
            print('Season refs:', len(seasons_sec))
            
            ep_links = re.findall(r'<a\s+href="(watch\.php\?vid=[a-f0-9]+)"[^>]*>([^<]*)</a>', html2)
            print('Episode links:', len(ep_links))
            for url2, etitle in ep_links[:5]:
                print(' ', etitle[:50], '->', url2)
            
            # Check for season containers
            conts = re.findall(r'<div[^>]*class="[^"]*SeasonsEpisodes[^"]*"[^>]*data-season="(\d+)"', html2)
            print('Season containers:', conts)
        break
