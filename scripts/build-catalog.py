"""Generate assets/js/catalog.js: the app's real wheel menus and the two counts on the page.

The website's demo and showcase read every menu from this file, so they match the app exactly.
Run it after each app release, against a current build:

  python scripts/build-catalog.py --app <ZestDrop.exe> --catalog-source <work/ZestDrop/Catalog.cs>

It asks `ZestDrop.exe --capabilities` for one empty sample file per extension (and a folder), in English
and Chinese. Menus therefore follow this machine: Office conversions appear only if desktop Office is
installed, and saved flows or the two-wheel layout would change the tool menus (check the warnings).
"""
import argparse
import json
import os
import re
import subprocess
import tempfile
from datetime import date
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument('--app', type=Path, required=True)
parser.add_argument('--catalog-source', type=Path, required=True)
args = parser.parse_args()
for path in (args.app, args.catalog_source):
    if not path.is_file():
        parser.error(f'Missing input: {path}')

source = args.catalog_source.read_text(encoding='utf-8')


def string_list(name):
    match = re.search(r'public static readonly string\[\] ' + name + r' = \[([^\]]*)\]', source)
    if not match:
        raise SystemExit(f'Could not find {name} in {args.catalog_source}')
    return re.findall(r'"([^"]+)"', match.group(1))


groups = {name: string_list(name) for name in ('Images', 'Audio', 'Video', 'Archives', 'OfficeSlides', 'OfficeWords', 'OfficeSheets')}
inputs = groups['Images'] + groups['Video'] + ['gif'] + groups['Audio'] + ['pdf', 'txt', 'srt', 'vtt'] \
    + groups['OfficeSlides'] + groups['OfficeWords'] + groups['OfficeSheets'] + groups['Archives']
office = set(groups['OfficeSlides'] + groups['OfficeWords'] + groups['OfficeSheets'])

# Every tool the app defines (one per id; "rotateImage" or "rotateVideo" is two tools), not combined entries.
definition = source[source.index('public static Operation Definition('):]
tool_ids = sorted(set(re.findall(r'"(\w+)"(?= or | =>)', definition)))
if not tool_ids:
    raise SystemExit('Could not find the tool definitions')


def capabilities(path, lang, scratch):
    out = scratch / f'{path.name}-{lang}.json'
    env = {**os.environ, 'ZESTDROP_LANG': lang}
    subprocess.run([str(args.app.resolve()), '--capabilities', str(path), str(out)],
                   cwd=args.app.resolve().parent, env=env, check=True, timeout=60)
    return json.loads(out.read_text(encoding='utf-8-sig'))


menus, labels, warnings = {}, {}, []
with tempfile.TemporaryDirectory(prefix='zestdrop-catalog-') as temp:
    scratch = Path(temp)
    samples = {}
    for ext in inputs:
        sample = scratch / f'sample.{ext}'
        sample.write_bytes(b'x')
        samples[ext] = sample
    folder = scratch / 'folder'
    folder.mkdir()
    samples['folder'] = folder
    # Outputs that are not inputs themselves (html, json, ...) behave like any other file: pack only.
    other = scratch / 'sample.other'
    other.write_bytes(b'x')
    samples['other'] = other
    for key, sample in samples.items():
        result = {lang: capabilities(sample, lang, scratch) for lang in ('en', 'zh')}
        en, zh = result['en'], result['zh']
        # Saved flows are personal, so they are left out of the website's menus.
        is_flow = lambda op: op['Id'].startswith('flow:') or op['Id'] == 'flows:menu'
        for op in en['Tools']:
            if is_flow(op):
                warnings.append(f'{key}: left out saved flow entry "{op["Label"]}"')
        en['Tools'] = [op for op in en['Tools'] if not is_flow(op)]
        zh['Tools'] = [op for op in zh['Tools'] if not is_flow(op)]
        conversions = [o['Id'] for o in en['Conversions']]
        tools = [o['Id'] for o in en['Tools']]
        for kind in ('Conversions', 'Tools'):
            for e, z in zip(en[kind], zh[kind]):
                labels[e['Id']] = {'en': e['Label'], 'zh': z['Label']}
        menus[key] = {'formats': conversions, 'tools': tools}

conversion_total = sum(len(menus[ext]['formats']) for ext in inputs)
office_total = sum(len(menus[ext]['formats']) for ext in inputs if ext in office)
if office_total == 0:
    warnings.append('No Office conversions: desktop Office is not installed here, so the total leaves them out')
if not any(op.startswith('merge:') for op in menus['jpg']['tools']):
    warnings.append('No combined tools: the two-wheel layout is selected in the tray menu; switch back and rerun')

data = {
    'generated': date.today().isoformat(),
    'counts': {
        'inputFormats': len(inputs),
        'conversions': conversion_total,
        'officeConversions': office_total,
        'tools': len(tool_ids),
    },
    'toolIds': tool_ids,
    'menus': menus,
    'labels': dict(sorted(labels.items())),
}
out = Path(__file__).resolve().parents[1] / 'assets' / 'js' / 'catalog.js'
out.write_text(
    '// Generated by scripts/build-catalog.py from the ZestDrop app. Do not edit by hand.\n'
    'window.ZD_CATALOG = ' + json.dumps(data, ensure_ascii=False, indent=1) + ';\n',
    encoding='utf-8', newline='\n')
print(json.dumps(data['counts']))
for warning in warnings:
    print('WARNING:', warning)
