import os, re

# Path mappings: old_path -> new_path
path_updates = {
    "'scripts/tuktuk_sitemap_index.json'": "'scripts/tuktukhd/data/tuktuk_sitemap_index.json'",
    '"scripts/tuktuk_sitemap_index.json"': '"scripts/tuktukhd/data/tuktuk_sitemap_index.json"',
    "'scripts/tuktuk_asian_index.json'": "'scripts/tuktukhd/data/tuktuk_asian_index.json'",
    '"scripts/tuktuk_asian_index.json"': '"scripts/tuktukhd/data/tuktuk_asian_index.json"',
    "'scripts/tuktuk_index.json'": "'scripts/tuktukhd/data/tuktuk_index.json'",
    '"scripts/tuktuk_index.json"': '"scripts/tuktukhd/data/tuktuk_index.json"',
    "'scripts/tuktuk_other_categories.json'": "'scripts/tuktukhd/data/tuktuk_other_categories.json'",
    '"scripts/tuktuk_other_categories.json"': '"scripts/tuktukhd/data/tuktuk_other_categories.json"',
    "'scripts/tuktuk_matched.json'": "'scripts/tuktukhd/data/tuktuk_matched.json'",
    '"scripts/tuktuk_matched.json"': '"scripts/tuktukhd/data/tuktuk_matched.json"',
    "'scripts/tuktuk_merge_results.json'": "'scripts/tuktukhd/data/tuktuk_merge_results.json'",
    '"scripts/tuktuk_merge_results.json"': '"scripts/tuktukhd/data/tuktuk_merge_results.json"',
    "'scripts/results_asian.json'": "'scripts/tuktukhd/data/results_asian.json'",
    '"scripts/results_asian.json"': '"scripts/tuktukhd/data/results_asian.json"',
}

files_to_update = [
    'final_aggressive_match.py',
    'final_remaining_match.py',
    'update_data_js.py',
    'find_remaining.py',
    'sitemap_scraper.py',
    'scrape_asian_pages.py',
    'scrape_asian.py',
    'scrape_remaining_categories.py',
    'scrape_tuktukhd.py',
    'deep_search_remaining.py',
    'keyword_match_remaining.py',
    'extract_and_merge.py',
    'fix_scraper.py',
    'full_scraper.py',
    'add_asian_results.py',
    'add_from_review.py',
    'fetch_new_asian.py',
    'check_coverage.py',
    'check_index.py',
    'check_new_asian.py',
    'check_sitemap_asian.py',
    'check_sitemap_detail.py',
    'debug_categories.py',
    'debug_match_detail.py',
    'debug_specific_matches.py',
    'search_remaining_asian.py',
]

updated = 0
for fname in files_to_update:
    fp = os.path.join('scripts', fname)
    if not os.path.exists(fp):
        continue
    with open(fp, 'r', encoding='utf-8') as f:
        content = f.read()
    new_content = content
    for old, new in path_updates.items():
        new_content = new_content.replace(old, new)
    if new_content != content:
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print('Updated: {}'.format(fname))
        updated += 1

print('\nTotal files updated: {}'.format(updated))
