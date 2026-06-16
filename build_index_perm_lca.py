#!/usr/bin/env python3
"""
Rebuild data/employer_index.json so every employer row carries THREE numbers:
  perm  -- PERM (green-card labor cert) filings, from the PERM store
           (data/employer_data.json), merged by canonical slug EXACTLY the way
           immilane-api/scripts/seed-kv.js merges them (so the index canonical
           names/slugs line up 1:1 with the already-seeded emp:<slug> detail KV
           -- this is what fixes the click-through 404).
  lca   -- H-1B LCA (ETA-9035) filings, from the H-1B store
           (h1b-build/multi/out/store_multi.json, sum of lcaByYear[].total),
           joined onto the PERM employer via the H-1B canonical/member slugs
           (same reunify keying the live /h1b endpoint uses).
  total -- perm + lca.

Output keeps backward-compat: `t` is set to `total` so any reader still keying
off `t` keeps working; `perm`, `lca`, `total` and `a` (search alias) are added.

PERM universe only: every emitted row has a real PERM detail record (emp:<slug>
already in KV) so it is clickable. H-1B-only employers (no PERM record) are NOT
added here -- see the report for that explicit limitation.
"""
import json, re, sys, unicodedata, datetime, os

HERE = os.path.dirname(os.path.abspath(__file__))
PERM_DATA = os.path.join(HERE, 'data', 'employer_data.json')
H1B_STORE = os.path.abspath(os.path.join(HERE, '..', 'h1b-build', 'multi', 'out', 'store_multi.json'))
OUT = os.path.join(HERE, 'data', 'employer_index.json')

# ---- seed-kv.js parity helpers -------------------------------------------
def normalize_slug(s):
    if not s:
        return ''
    s = unicodedata.normalize('NFKD', str(s))
    s = ''.join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace('&', ' and ')
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = s.strip('-')
    return s[:200]

def clean_text(s):
    return re.sub(r'\s+', ' ', '' if s is None else str(s)).strip()

def pick_canonical_name(members):
    # highest total -> prefer non-ALLCAPS -> shorter cleaned -> alphabetical
    def key(m):
        name = m['name']
        is_upper = 1 if name == name.upper() else 0
        c = clean_text(name)
        return (-(m.get('total') or 0), is_upper, len(c), c)
    return sorted(members, key=key)[0]['name']

def merge_group(members):
    canon = clean_text(pick_canonical_name(members))
    total = sum(m.get('total') or 0 for m in members)
    return {'name': canon, 'perm': total}

def merge_employers(employers_full):
    groups = {}
    for emp in employers_full:
        if not emp or not emp.get('name'):
            continue
        slug = normalize_slug(emp['name'])
        if not slug:
            continue
        groups.setdefault(slug, []).append(emp)
    merged = []
    for slug, members in groups.items():
        g = merge_group(members)
        merged.append({'slug': slug, 'name': g['name'], 'perm': g['perm']})
    return merged

# ---- LCA lookup from the H-1B store --------------------------------------
def build_lca_lookup(store_path):
    d = json.load(open(store_path))
    emps = d['employers']
    lookup = {}
    for canon_slug, rec in emps.items():
        lca = sum((y.get('total') or 0) for y in (rec.get('lcaByYear') or []))
        if lca <= 0:
            continue
        # key on the canonical slug AND every member slug variant, so a PERM
        # employer's slug resolves the same way the live /h1b endpoint does.
        lookup[canon_slug] = lca
        for ms in (rec.get('memberSlugs') or []):
            # canonical wins on collision (its lca already covers the members)
            lookup.setdefault(ms, lca)
    return lookup

def main():
    print(f'[build] PERM   <- {PERM_DATA}')
    perm_json = json.load(open(PERM_DATA))
    full = perm_json.get('employers') or []
    print(f'[build] H-1B   <- {H1B_STORE}')
    lca_lookup = build_lca_lookup(H1B_STORE)
    print(f'[build] LCA slugs indexed: {len(lca_lookup)}')

    merged = merge_employers(full)
    print(f'[build] PERM employers: {len(full)} raw -> {len(merged)} merged')

    matched = 0
    total_perm = 0
    total_lca = 0
    rows = []
    for m in merged:
        perm = m['perm']
        lca = lca_lookup.get(m['slug'], 0)
        if lca:
            matched += 1
        total = perm + lca
        total_perm += perm
        total_lca += lca
        rows.append({
            'n': m['name'],
            'perm': perm,
            'lca': lca,
            'total': total,
            't': total,                 # backward-compat for any reader keying off `t`
            'a': clean_text(m['name']).lower(),
        })

    # Default ordering: Total (perm+lca) desc, then name. The leaderboard lets
    # the user re-sort by any column; this is just the stored/default order.
    rows.sort(key=lambda r: (-r['total'], r['n'].lower()))

    out = {
        'generatedAt': datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
        'totalEmployers': len(rows),
        'totalPerm': total_perm,
        'totalLca': total_lca,
        'totalCases': total_perm + total_lca,   # perm + lca filings combined
        'employers': rows,
    }
    json.dump(out, open(OUT, 'w'), separators=(',', ':'))
    print(f'[build] wrote {OUT}')
    print(f'[build] employers={len(rows)} matched_lca={matched} '
          f'totalPerm={total_perm} totalLca={total_lca} totalCases={total_perm+total_lca}')
    # spot checks
    byslug = {normalize_slug(r['n']): r for r in rows}
    for s in ['cognizant-technology-solutions-us-corporation', 'microsoft-corporation',
              'amazon-com-services-llc', 'tata-consultancy-services-limited']:
        r = byslug.get(s)
        if r:
            print(f"  {r['n'][:44]:44} perm={r['perm']:>6} lca={r['lca']:>8} total={r['total']:>8}")
        else:
            print(f"  {s}: NOT FOUND")

if __name__ == '__main__':
    main()
