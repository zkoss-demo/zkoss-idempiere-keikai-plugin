#!/usr/bin/env python3
"""Regenerate THIRD-PARTY.md from the jars actually present in the fragment's lib/.

Everything except the License column is read out of the jars themselves. The License column
uses each jar's own declaration where it has one - Bundle-License in the manifest, or <licenses>
in the embedded Maven pom - and falls back to FALLBACK below for the jars that declare nothing.
Fallback rows are marked, so a reader can tell a jar's own statement from our research.
"""
import os, re, sys, zipfile

LIB = 'org.idempiere.keikai.fragment/lib'
OUT = 'THIRD-PARTY.md'

# jars that ship no machine-readable license of their own
FALLBACK = {
    'failureaccess':   'Apache-2.0',
    'jfreechart':      'LGPL-2.1 or later',
    'jcommon':         'LGPL-2.1 or later',
    'curvesapi':       'BSD-3-Clause',
    'SparseBitSet':    'Apache-2.0',
    'filters':         'Apache-2.0',
    'poi':             'Apache-2.0',
    'poi-ooxml':       'Apache-2.0',
    'poi-ooxml-lite':  'Apache-2.0',
    'poi-ooxml-full':  'Apache-2.0',
    'xmlbeans':        'Apache-2.0',
}
# the commercial jars: never guess, state them explicitly
COMMERCIAL = {
    'keikai':       'Commercial - Keikai EE Evaluation',
    'keikai-ex':    'Commercial - Keikai EE Evaluation',
    'keikai-pdf':   'Commercial - Keikai EE Evaluation',
    'keikai-model': 'Commercial - Keikai EE Evaluation',
    'keikai-native':'Commercial - Keikai EE Evaluation',
    'zkex':         'Commercial - ZK PE/EE Evaluation',
    'zkcharts':     'Commercial - ZK Charts Evaluation',
}

def text(z, name):
    try:
        return z.read(name).decode('utf-8', 'replace').replace('\r', '')
    except KeyError:
        return ''

def unfold(manifest):
    """MANIFEST.MF wraps at 72 bytes and continues with a leading space."""
    return re.sub(r'\n ', '', manifest)

# raw license strings are URLs and vendor prose; normalize the ones we recognize
NORMALIZE = [
    (r'mozilla.*2\.0|MPL-2\.0',                                'MPL-2.0'),
    (r'lgpl-2\.1|lesser general public licen[cs]e.*2\.1',      'LGPL-2.1'),
    (r'lesser general public licen[cs]e|lgpl',                  'LGPL-2.1 or later'),
    (r'apache.*2\.0|Apache-2\.0',                              'Apache-2.0'),
    (r'\bBSD\b',                                               'BSD-3-Clause'),
    (r'\bMIT\b|jsoup\.org/license',                            'MIT'),
]

def normalize(raw):
    hits, families = [], set()
    for pattern, name in NORMALIZE:
        family = name.split('-')[0]
        if family not in families and re.search(pattern, raw, re.I):
            families.add(family)
            hits.append(name)
    return ' or '.join(hits) if hits else raw

def field(manifest, key):
    m = re.search(rf'^{key}: *(.+)$', manifest, re.M)
    return m.group(1).strip() if m else ''

def inspect(path):
    base = os.path.basename(path)[:-4]
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        manifest = unfold(text(z, 'META-INF/MANIFEST.MF'))
        coords = ''
        for n in names:
            if n.endswith('pom.properties'):
                p = dict(l.split('=', 1) for l in text(z, n).splitlines() if '=' in l and not l.startswith('#'))
                if 'groupId' in p:
                    coords = f"{p['groupId']}:{p.get('artifactId','')}:{p.get('version','')}"
                break
        if not coords:
            title = field(manifest, 'Implementation-Title') or field(manifest, 'Bundle-Name')
            ver = field(manifest, 'Implementation-Version') or field(manifest, 'Bundle-Version')
            coords = f'{title} {ver}'.strip() or '-'
        license, sourced = COMMERCIAL.get(base, ''), 'stated here'
        if not license:
            license, sourced = field(manifest, 'Bundle-License'), 'jar manifest'
        if not license:
            for n in names:
                if n.endswith('pom.xml'):
                    pom = text(z, n)
                    m = re.search(r'<licenses>.*?<name>([^<]+)</name>', pom, re.S)
                    if m:
                        license, sourced = m.group(1).strip(), 'jar pom'
                    break
        if license and base not in COMMERCIAL:
            license = normalize(license)
        if not license:
            license = FALLBACK.get(base, '')
            sourced = 'researched - not declared in the jar' if license else ''
        if not license:
            license, sourced = '**unknown - verify before redistributing**', ''
        bundled = sorted(n for n in names
                         if re.match(r'META-INF/(LICENSE|NOTICE|COPYING|LICENSES|licenses/)', n) and not n.endswith('/'))
    return dict(jar=base, coords=coords, license=license, sourced=sourced,
                size=os.path.getsize(path), bundled=bundled)

if not os.path.isdir(LIB):
    sys.exit(f'{LIB} not found - build the fragment first.')

rows = [inspect(os.path.join(LIB, f)) for f in sorted(os.listdir(LIB)) if f.endswith('.jar')]

def mb(n): return f'{n/1048576:.1f} MB'

with open(OUT, 'w') as f:
    w = f.write
    w('# Third-party contents of `org.idempiere.keikai.fragment`\n\n')
    w("This project's own source is GPLv2 or later - see [LICENSE.md](LICENSE.md). The\n"
      '**released fragment jar is not just that source**: a fragment exists to put a whole runtime\n'
      "on the host bundle's class loader, so every jar below is embedded under `lib/` inside the\n"
      'jar you download. This file lists what is in there and under what terms.\n\n')
    w(f'Generated by `./make-third-party.py` from `{LIB}` - '
      f'{len(rows)} jars, {mb(sum(r["size"] for r in rows))} total.\n\n')

    w('## Commercially licensed - not covered by the GPL\n\n')
    w('| Jar | Maven coordinates | Size | License |\n|---|---|---|---|\n')
    for r in rows:
        if r['jar'] in COMMERCIAL:
            w(f"| `{r['jar']}.jar` | `{r['coords']}` | {mb(r['size'])} | {r['license']} |\n")
    w('\nThese are **Evaluation** builds. Installing one to evaluate it is fine; redistributing it\n'
      'is not, and production use requires a license from ZK - <info@zkoss.org>.\n\n')

    w('## Open-source components, redistributed unmodified\n\n')
    w('| Jar | Maven coordinates | Size | License | Source of that statement |\n|---|---|---|---|---|\n')
    for r in rows:
        if r['jar'] not in COMMERCIAL:
            w(f"| `{r['jar']}.jar` | `{r['coords']}` | {mb(r['size'])} | {r['license']} | {r['sourced']} |\n")

    lgpl = [r['jar'] for r in rows if 'LGPL' in r['license']]
    if lgpl:
        w('\n## Components under the LGPL\n\n')
        w('`' + '`, `'.join(lgpl) + '`\n\n')
        w('The LGPL allows redistribution inside a larger work, but it attaches obligations that\n'
          'Apache-2.0 and MIT do not: recipients must be told the library is LGPL, be able to obtain\n'
          "its source, and be able to replace it with their own build. Because these sit inside the\n"
          'fragment jar rather than beside it, satisfying that means pointing at upstream sources in\n'
          'the release notes. Check this before publishing a release publicly.\n')

    w('\n## Bundled license texts\n\n')
    w('Jars carrying their own license or notice files inside `META-INF/`:\n\n')
    for r in rows:
        if r['bundled']:
            w(f"- `{r['jar']}.jar`: {', '.join(r['bundled'])}\n")
    missing = [r['jar'] for r in rows if not r['bundled'] and r['jar'] not in COMMERCIAL]
    if missing:
        w('\nOpen-source jars with no license text inside them, whose terms come from the table above\n'
          'rather than from the artifact: `' + '`, `'.join(missing) + '`\n')
