#!/usr/bin/env python3
"""
Rebuild data/employer_index.json so every employer row carries THREE numbers:
  perm  -- PERM (green-card labor cert) filings. Primary source is the H-1B
           store's DOL-disclosure PERM series (store_multi.json permByYear, sum
           of cert+denied+withdrawn) -- the SAME number the profile page's PERM
           section and the live /h1b endpoint show (e.g. Cognizant 27,788). When
           an employer has no disclosure PERM, fall back to the live PERM-tracker
           total (data/employer_data.json) so it still has a number.
  lca   -- H-1B LCA (ETA-9035) filings, from the same H-1B store
           (sum of lcaByYear[].total).
  total -- perm + lca.

Universe + canonical names come from data/employer_data.json, merged by slug
EXACTLY the way immilane-api/scripts/seed-kv.js merges them, so the index
canonical names/slugs line up 1:1 with the already-seeded emp:<slug> detail KV
-- this is what fixes the click-through 404. perm/lca are joined on from the
H-1B store via its canonical + member slugs (same reunify keying /h1b uses).

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

# ---- PERM+LCA lookup from the H-1B store ---------------------------------
def build_h1b_lookup(store_path):
    """slug -> {'perm': <cert+denied+withdrawn over permByYear>,
               'lca':  <sum lcaByYear.total>}, keyed by canonical AND member
    slugs so a PERM employer's slug resolves the way the live /h1b endpoint
    does (which folds member/alias slugs onto the canonical record)."""
    d = json.load(open(store_path))
    emps = d['employers']
    lookup = {}
    for canon_slug, rec in emps.items():
        lca = sum((y.get('total') or 0) for y in (rec.get('lcaByYear') or []))
        perm = sum(((y.get('cert') or 0) + (y.get('denied') or 0) + (y.get('withdrawn') or 0))
                   for y in (rec.get('permByYear') or []))
        if lca <= 0 and perm <= 0:
            continue
        entry = {'perm': perm, 'lca': lca}
        lookup[canon_slug] = entry
        for ms in (rec.get('memberSlugs') or []):
            lookup.setdefault(ms, entry)  # canonical wins on collision
    return lookup

def main():
    print(f'[build] PERM   <- {PERM_DATA}')
    perm_json = json.load(open(PERM_DATA))
    full = perm_json.get('employers') or []
    print(f'[build] H-1B   <- {H1B_STORE}')
    h1b_lookup = build_h1b_lookup(H1B_STORE)
    print(f'[build] H-1B slugs indexed: {len(h1b_lookup)}')

    merged = merge_employers(full)
    print(f'[build] PERM employers: {len(full)} raw -> {len(merged)} merged')

    matched = 0          # rows that joined to an H-1B record (perm or lca)
    perm_from_dol = 0     # rows whose PERM came from DOL disclosure
    total_perm = 0
    total_lca = 0
    rows = []
    for m in merged:
        h = h1b_lookup.get(m['slug'])
        if h:
            matched += 1
        # PERM: prefer DOL disclosure (cert+denied+withdrawn) when present,
        # else fall back to the live PERM-tracker total. This mirrors
        # employer.html's permStatsFromDisclosure() || permStats() so the
        # leaderboard `perm` always equals the profile's Green Card (PERM) figure.
        if h and h['perm'] > 0:
            perm = h['perm']
            perm_from_dol += 1
        else:
            perm = m['perm']
        lca = h['lca'] if h else 0
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
    print(f'[build] employers={len(rows)} joined_h1b={matched} perm_from_dol_disclosure={perm_from_dol} '
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
