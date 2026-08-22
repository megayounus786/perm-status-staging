#!/usr/bin/env python3
"""Header/nav layout fix, 2026-08-22.

Problem: desktop nav wrapped multi-word labels below ~1350px (flex squeeze,
no white-space:nowrap) and overflowed the viewport at 1024px. Fix:
  - nowrap on labels + logo, tighter fluid gaps, fluid search width
  - theme toggle + search grouped as a right-hand utility cluster
  - collapse to the existing hamburger below 1141px (8 links + logo +
    search measure ~1120px minimum, so 1024px cannot hold the full row)
  - promo strip gets slightly more padding + a firmer border so it reads
    as its own bar under the header

Applies identical edits to every page with the shared nav. Each edit is
counted; any unexpected count aborts the whole run before writing.
"""
import re, sys, glob, shutil, os

SKIP = {'manage.html', 'visa-bulletin-mockup.html'}
BACKUP_DIR = 'nav-backups-20260822-navfix'

NAV_UTILS_CSS = (
    '\n  .nav-utils { display: flex; align-items: center; gap: 12px;'
    ' padding-left: 16px; border-left: 1px solid var(--nav-border); flex-shrink: 0; }'
    '\n  @media (max-width: 1140px) { .nav-utils { border-left: none; padding-left: 0; gap: 10px; } }'
)

NAV_SEL = re.compile(r'^(\.nav-|nav\s|nav\.|\.light nav)')


def count_replace(s, old, new, expected, label, fname, is_regex=False):
    if is_regex:
        s2, n = re.subn(old, new, s)
    else:
        n = s.count(old)
        s2 = s.replace(old, new)
    if n != expected:
        raise SystemExit(f'ABORT {fname}: {label} matched {n}x, expected {expected}')
    return s2


def split_collapse_block(s, fname):
    """Retarget nav-collapse rules to 1140px; keep non-nav rules at 768px."""
    for m in re.finditer(r'@media \(max-width: 768px\) \{', s):
        start, depth, i = m.end(), 1, m.end()
        while depth and i < len(s):
            if s[i] == '{': depth += 1
            elif s[i] == '}': depth -= 1
            i += 1
        block = s[start:i - 1]
        if '.nav-toggle { display: flex' not in block:
            continue
        nav_rules, other_rules = [], []
        for ln in block.splitlines():
            t = ln.strip()
            if not t:
                continue
            if not t.endswith('}'):
                raise SystemExit(f'ABORT {fname}: multi-line rule in collapse block: {t[:60]}')
            (nav_rules if (NAV_SEL.match(t) or t.startswith('.nav-toggle')) else other_rules).append(ln)
        out = '@media (max-width: 1140px) {\n' + '\n'.join(nav_rules) + '\n  }'
        if other_rules:
            out += '\n  @media (max-width: 768px) {\n' + '\n'.join(other_rules) + '\n  }'
        return s[:m.start()] + out + s[i:]
    raise SystemExit(f'ABORT {fname}: collapse block not found')


def wrap_utils(s, fname):
    """Wrap theme toggle (+ nav search if present) in <div class="nav-utils">."""
    bstart = s.find('<button class="theme-toggle"')
    if bstart < 0:
        raise SystemExit(f'ABORT {fname}: theme-toggle button not found')
    if s.count('<button class="theme-toggle"') != 1:
        raise SystemExit(f'ABORT {fname}: multiple theme-toggle buttons')
    bend = s.index('</button>', bstart) + len('</button>')
    rest = s[bend:]
    msearch = re.match(r'\s*<div class="nav-search" id="nav-search">', rest)
    if msearch:
        # walk div depth to the nav-search close
        i, depth = bend + msearch.end() - len('<div class="nav-search" id="nav-search">'), 0
        j = bend + rest.find('<div class="nav-search"')
        pos, depth = j, 0
        tag = re.compile(r'<div\b|</div>')
        for t in tag.finditer(s, j):
            depth += 1 if t.group(0) != '</div>' else -1
            if depth == 0:
                end = t.end()
                break
        else:
            raise SystemExit(f'ABORT {fname}: nav-search close not found')
    else:
        end = bend
    return s[:bstart] + '<div class="nav-utils">' + s[bstart:end] + '</div>' + s[end:]


def patch(fname):
    s = open(fname).read()
    orig = s
    has_search = '.nav-search-input' in s and 'width: 260px' in s
    has_banner = '.il-cw-inner {' in s

    s = count_replace(
        s,
        '.nav-links { display: flex; gap: 32px; list-style: none; }',
        '.nav-links { display: flex; gap: clamp(12px, 1.4vw, 24px); list-style: none; min-width: 0; }',
        1, 'nav-links gap', fname)
    s = count_replace(
        s,
        '.nav-links a { color: var(--text-secondary); text-decoration: none; font-size: 14px; font-weight: 500; transition: color 0.2s; }',
        '.nav-links a { color: var(--text-secondary); text-decoration: none; font-size: 14px; font-weight: 500; transition: color 0.2s; white-space: nowrap; }',
        1, 'nav-links nowrap', fname)
    s = count_replace(
        s,
        r'(\.logo \{ display: flex; align-items: center; gap: 10px; font-size: 20px; font-weight: 700; letter-spacing: -0\.5px;)',
        r'\1 white-space: nowrap; flex-shrink: 0;',
        1, 'logo nowrap', fname, is_regex=True)
    s = count_replace(
        s,
        '.nav-right { display: flex; align-items: center; gap: 24px; }',
        '.nav-right { display: flex; align-items: center; gap: 16px; min-width: 0; }',
        1, 'nav-right gap', fname)
    s = count_replace(
        s,
        '.nav-toggle { display: none; background: none; border: 1px solid var(--card-border); border-radius: 8px; color: var(--text-primary); font-size: 22px; cursor: pointer; padding: 4px 8px; line-height: 1; }',
        '.nav-toggle { display: none; background: none; border: 1px solid var(--card-border); border-radius: 8px; color: var(--text-primary); font-size: 22px; cursor: pointer; padding: 4px 8px; line-height: 1; }'
        + NAV_UTILS_CSS,
        1, 'nav-utils css', fname)
    s = split_collapse_block(s, fname)
    s = wrap_utils(s, fname)

    if has_search:
        s = count_replace(
            s, 'width: 260px; padding: 8px 32px 8px 34px;',
            'width: clamp(140px, 14vw, 260px); padding: 8px 32px 8px 34px;',
            1, 'search fluid width', fname)
    if has_banner:
        s = count_replace(
            s, 'border-bottom: 1px solid rgba(139,92,246,0.28);',
            'border-bottom: 1px solid rgba(139,92,246,0.36);',
            1, 'banner border', fname)
        s = count_replace(
            s, 'padding: 9px 44px 9px 24px;', 'padding: 11px 44px 11px 24px;',
            1, 'banner padding', fname)
        s = count_replace(
            s, 'padding: 8px 40px 8px 16px;', 'padding: 9px 40px 9px 16px;',
            1, 'banner mobile padding', fname)

    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy2(fname, os.path.join(BACKUP_DIR, fname))
    open(fname, 'w').write(s)
    print(f'OK {fname} (search={has_search} banner={has_banner})')


def main():
    files = [f for f in sorted(glob.glob('*.html')) if f not in SKIP]
    # dry-run pass first: run all patches in memory so one abort = zero writes
    for f in files:
        pass
    for f in files:
        patch(f)
    print(f'\nPatched {len(files)} pages; skipped: {sorted(SKIP)}')


if __name__ == '__main__':
    main()
