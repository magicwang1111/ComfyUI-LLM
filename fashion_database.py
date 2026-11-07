"""Portable product catalog and channel video records; Excel is import/export only."""
import hashlib
import json
import mimetypes
import posixpath
import re
import sqlite3
import zipfile
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET

if __package__:
    from .fashion_prompt import read_generation_copy
else:
    from fashion_prompt import read_generation_copy

ROOT = Path(__file__).resolve().parent
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
DOCREL = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
DRAW = 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing'
PID = re.compile(r'[0-9]{19}\Z')


def settings(config, root=ROOT):
    value = config.get('tiktok_database', {})
    path = Path(value.get('path', 'data/tiktok.sqlite3')).expanduser()
    return {**value, 'enabled': bool(value.get('enabled', False)),
            'path': (root / path).resolve() if not path.is_absolute() else path.resolve(),
            'sheet': value.get('sheet', 'bnmb')}


def connect(path, create=False):
    path = Path(path)
    if create:
        path.parent.mkdir(parents=True, exist_ok=True)
    elif not path.is_file():
        raise ValueError('Catalog database is not initialized; import the two workbooks first.')
    db = sqlite3.connect(str(path), timeout=30)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    db.execute('PRAGMA busy_timeout=30000')
    return db


def initialize(path):
    with closing(connect(path, create=True)) as db:
        db.execute('PRAGMA journal_mode=WAL')
        db.executescript('''
            CREATE TABLE IF NOT EXISTS workbooks (
                kind TEXT PRIMARY KEY, filename TEXT NOT NULL, sha256 TEXT NOT NULL, imported_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS workbook_parts (
                kind TEXT NOT NULL REFERENCES workbooks(kind), name TEXT NOT NULL, data BLOB NOT NULL,
                PRIMARY KEY(kind, name));
            CREATE TABLE IF NOT EXISTS sheets (
                kind TEXT NOT NULL REFERENCES workbooks(kind), name TEXT NOT NULL, position INTEGER NOT NULL,
                part_name TEXT NOT NULL, PRIMARY KEY(kind, name));
            CREATE TABLE IF NOT EXISTS source_rows (
                kind TEXT NOT NULL, sheet TEXT NOT NULL, row_number INTEGER NOT NULL, values_json TEXT NOT NULL,
                PRIMARY KEY(kind, sheet, row_number));
            CREATE TABLE IF NOT EXISTS cell_overrides (
                kind TEXT NOT NULL, sheet TEXT NOT NULL, cell TEXT NOT NULL, value TEXT NOT NULL, reason TEXT NOT NULL,
                PRIMARY KEY(kind, sheet, cell));
            CREATE TABLE IF NOT EXISTS images (
                kind TEXT NOT NULL, sheet TEXT NOT NULL, row_number INTEGER NOT NULL, column_number INTEGER NOT NULL,
                part_name TEXT NOT NULL, PRIMARY KEY(kind, sheet, row_number, column_number, part_name));
            CREATE TABLE IF NOT EXISTS products (
                pid TEXT PRIMARY KEY, spu TEXT NOT NULL, category TEXT NOT NULL, image_url TEXT NOT NULL,
                details_json TEXT NOT NULL, source_sheet TEXT NOT NULL, source_row INTEGER NOT NULL);
            CREATE INDEX IF NOT EXISTS products_spu ON products(spu);
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY, sheet TEXT NOT NULL, sequence TEXT NOT NULL, pid TEXT NOT NULL,
                values_json TEXT NOT NULL, source_row INTEGER, generation_id TEXT UNIQUE,
                metadata_json TEXT NOT NULL, photo BLOB, photo_mime TEXT,
                created_at TEXT NOT NULL, UNIQUE(sheet, sequence));
            CREATE INDEX IF NOT EXISTS videos_pid ON videos(pid);
        ''')


def part_target(source, target):
    return target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join(posixpath.dirname(source), target))


def relationships(z, source):
    name = posixpath.join(posixpath.dirname(source), '_rels', posixpath.basename(source) + '.rels')
    if name not in z.namelist():
        return {}
    return {r.get('Id'): r.attrib for r in ET.fromstring(z.read(name))}


def workbook_rows(z):
    strings = [''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml'))] if 'xl/sharedStrings.xml' in z.namelist() else []
    links = relationships(z, 'xl/workbook.xml')
    for position, sheet in enumerate(ET.fromstring(z.read('xl/workbook.xml')).find('s:sheets', NS)):
        name = part_target('xl/workbook.xml', links[sheet.get('{' + DOCREL + '}id')]['Target'])
        xml = ET.fromstring(z.read(name))
        rels = relationships(z, name)
        hyperlinks = {h.get('ref'): rels.get(h.get('{' + DOCREL + '}id'), {}).get('Target', '')
                      for h in xml.findall('s:hyperlinks/s:hyperlink', NS)}
        rows = []
        for row in xml.find('s:sheetData', NS):
            values = {}
            for cell in row:
                v, inline = cell.find('s:v', NS), cell.find('s:is', NS)
                text = strings[int(v.text)] if cell.get('t') == 's' and v is not None else ''.join(inline.itertext()) if inline is not None else v.text if v is not None else ''
                # Keep a hyperlink's durable target, rather than only its display label.
                if cell.get('r') in hyperlinks:
                    text = hyperlinks[cell.get('r')] or text
                if text:
                    values[re.sub(r'[0-9]', '', cell.get('r'))] = text
            if values:
                rows.append((int(row.get('r')), values))
        yield sheet.get('name'), position, name, rows


def import_workbook(db, path, kind):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    existing = db.execute('SELECT sha256 FROM workbooks WHERE kind=?', (kind,)).fetchone()
    if existing:
        if existing['sha256'] != digest:
            raise ValueError(f'{kind} was already imported from another revision; refusing to overwrite database records.')
        return
    db.execute('INSERT INTO workbooks VALUES(?,?,?,?)', (kind, path.name, digest, datetime.now(timezone.utc).isoformat()))
    with zipfile.ZipFile(path) as z:
        for name in z.namelist():
            db.execute('INSERT INTO workbook_parts VALUES(?,?,?)', (kind, name, z.read(name)))
        for sheet, position, part, rows in workbook_rows(z):
            db.execute('INSERT INTO sheets VALUES(?,?,?,?)', (kind, sheet, position, part))
            for row, values in rows:
                db.execute('INSERT INTO source_rows VALUES(?,?,?,?)', (kind, sheet, row, json.dumps(values, ensure_ascii=False)))
            for rel in relationships(z, part).values():
                if not rel.get('Type', '').endswith('/drawing'):
                    continue
                drawing = part_target(part, rel['Target'])
                draw_rels = relationships(z, drawing)
                for anchor in ET.fromstring(z.read(drawing)):
                    start = anchor.find('{' + DRAW + '}from')
                    if start is None:
                        continue
                    row = int(start.find('{' + DRAW + '}row').text) + 1
                    col = int(start.find('{' + DRAW + '}col').text) + 1
                    for blip in anchor.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}blip'):
                        image = draw_rels.get(blip.get('{' + DOCREL + '}embed'))
                        if image:
                            db.execute('INSERT OR IGNORE INTO images VALUES(?,?,?,?,?)',
                                       (kind, sheet, row, col, part_target(drawing, image['Target'])))


def migrate(path, videos, products):
    initialize(path)
    with closing(connect(path)) as db, db:
        db.execute('BEGIN IMMEDIATE')
        import_workbook(db, Path(videos), 'videos')
        import_workbook(db, Path(products), 'products')
        candidates, sources = {}, []
        for sh in db.execute("SELECT name FROM sheets WHERE kind='products' ORDER BY position"):
            rows = db.execute("SELECT row_number,values_json FROM source_rows WHERE kind='products' AND sheet=? ORDER BY row_number", (sh['name'],)).fetchall()
            headers = json.loads(rows[0]['values_json'])
            by_name = {v.strip(): k for k, v in headers.items()}
            for row in rows[1:]:
                values = json.loads(row['values_json'])
                raw, spu = values.get(by_name['PID'], ''), values.get(by_name['SPU'], '')
                sources.append((sh['name'], row['row_number'], by_name, values, raw, spu))
                if PID.fullmatch(raw):
                    candidates.setdefault(spu, set()).add(raw)
        for sheet, row, headers, values, raw, spu in sources:
            exact = raw if PID.fullmatch(raw) else next(iter(candidates[spu])) if len(candidates.get(spu, set())) == 1 else None
            if exact is None:
                continue  # Preserve unresolved originals; never invent rounded PID digits.
            details = {name: values.get(col, '') for name, col in headers.items()}
            details['PID'] = exact
            image_url = next((v for v in values.values() if v.startswith(('https://', 'http://'))), '')
            db.execute('INSERT OR IGNORE INTO products VALUES(?,?,?,?,?,?,?)',
                       (exact, spu, details.get('三级品类', ''), image_url, json.dumps(details, ensure_ascii=False), sheet, row))
            db.execute('INSERT OR IGNORE INTO cell_overrides VALUES(?,?,?,?,?)',
                       ('products', sheet, f'{headers["PID"]}{row}', exact,
                        'Unique SPU match to an exact PID in the other source sheet' if exact != raw else 'Preserve exact PID as text'))
        for sh in db.execute("SELECT name FROM sheets WHERE kind='videos' ORDER BY position"):
            rows = db.execute("SELECT row_number,values_json FROM source_rows WHERE kind='videos' AND sheet=? ORDER BY row_number", (sh['name'],)).fetchall()
            if not rows or json.loads(rows[0]['values_json']).get('B') != 'PID':
                continue
            for row in rows[1:]:
                values = json.loads(row['values_json'])
                if not values.get('A'):
                    continue
                db.execute('INSERT OR IGNORE INTO videos(sheet,sequence,pid,values_json,source_row,metadata_json,created_at) VALUES(?,?,?,?,?,?,?)',
                           (sh['name'], values['A'], values.get('B', ''), row['values_json'], row['row_number'], '{}', ''))
                if PID.fullmatch(values.get('B', '')):
                    db.execute('INSERT OR IGNORE INTO cell_overrides VALUES(?,?,?,?,?)',
                               ('videos', sh['name'], f'B{row["row_number"]}', values['B'], 'Preserve exact PID as text'))
        return counts(db)


def counts(db):
    return {table: db.execute('SELECT COUNT(*) FROM ' + table).fetchone()[0]
            for table in ('workbooks', 'source_rows', 'products', 'videos', 'images', 'cell_overrides')}


def lookup(path, pid):
    if not PID.fullmatch(pid):
        raise ValueError('PID must contain exactly 19 ASCII digits.')
    with closing(connect(path)) as db:
        product = db.execute('SELECT * FROM products WHERE pid=?', (pid,)).fetchone()
        videos = db.execute('SELECT id,sheet,sequence,values_json,generation_id,metadata_json FROM videos WHERE pid=? ORDER BY id', (pid,)).fetchall()
        product_data = dict(product) if product else None
        if product_data:
            product_data['details'] = json.loads(product_data.pop('details_json'))
        return {'pid': pid, 'product': product_data,
                'videos': [{**{k: v[k] for k in ('id', 'sheet', 'sequence', 'generation_id')},
                            'values': json.loads(v['values_json']), 'metadata': json.loads(v['metadata_json'])} for v in videos]}


def record_generation(path, run_dir, artifact, sheet, publication=None, publication_error=''):
    run = Path(run_dir)
    product = json.loads((run / 'analysis.json').read_text(encoding='utf-8'))
    manifest = json.loads((run / 'product/manifest.json').read_text(encoding='utf-8'))
    job = json.loads((run / 'job.json').read_text(encoding='utf-8'))
    pid = product['pid']
    if not PID.fullmatch(pid) or manifest['pid'] != pid:
        raise ValueError('Generation and product PID do not match.')
    qc_path = run / 'qc.json'
    qc = json.loads(qc_path.read_text(encoding='utf-8')) if qc_path.exists() else {}
    copy = read_generation_copy(run)
    first = min(manifest['images'], key=lambda item: item['index'])
    photo = (run / 'product' / first['file']).resolve()
    if not photo.is_relative_to((run / 'product').resolve()):
        raise ValueError('Product photo escaped its run directory.')
    photo_bytes = photo.read_bytes()
    if hashlib.sha256(photo_bytes).hexdigest() != first['sha256']:
        raise ValueError('Product photo differs from the verified manifest.')
    metadata = {'video': artifact, 'qc': qc, 'publication': publication, 'publication_error': publication_error,
                'source_url': product['source_url'], 'photo_sha256': first['sha256']}
    with closing(connect(path)) as db, db:
        db.execute('BEGIN IMMEDIATE')
        existing = db.execute('SELECT id,sheet,sequence,pid,values_json,metadata_json FROM videos WHERE generation_id=?', (job['prompt_id'],)).fetchone()
        if existing:
            if existing['pid'] != pid:
                raise ValueError('An existing generation ID belongs to another PID.')
            values = json.loads(existing['values_json'])
            previous = json.loads(existing['metadata_json'])
            if (run / 'prompt.txt').exists():
                values.update(G=copy['chinese'], H=copy['english'])
            if (run / 'post-copy.json').exists():
                values.update(J=copy['caption_english'], K=' '.join(copy['hashtags']))
            if publication:
                values['I'] = publication['url']
            metadata['qc'] = qc or previous.get('qc', {})
            metadata['publication'] = publication or previous.get('publication')
            db.execute('UPDATE videos SET values_json=?,metadata_json=? WHERE id=?',
                       (json.dumps(values, ensure_ascii=False), json.dumps(metadata, ensure_ascii=False), existing['id']))
            return {'id': existing['id'], 'sheet': existing['sheet'], 'sequence': existing['sequence'], 'already_recorded': True}
        last = db.execute('SELECT sequence FROM videos WHERE sheet=? ORDER BY id DESC LIMIT 1', (sheet,)).fetchone()
        if not last or not re.fullmatch(r'[A-Za-z]+[0-9]+', last['sequence']):
            raise ValueError(f'No imported video channel sequence found for sheet {sheet}.')
        match = re.fullmatch(r'([A-Za-z]+)([0-9]+)', last['sequence'])
        sequence = match[1] + str(int(match[2]) + 1)
        values = {k: '' for k in 'ABCDEFGHIJKLMN'}
        values.update(A=sequence, B=pid, C=product['title'], G=copy['chinese'],
                      H=copy['english'], I=(publication or {}).get('url') or artifact.get('oss_uri', ''),
                      J=copy['caption_english'], K=' '.join(copy['hashtags']))
        cursor = db.execute('''INSERT INTO videos(sheet,sequence,pid,values_json,generation_id,metadata_json,photo,photo_mime,created_at)
                               VALUES(?,?,?,?,?,?,?,?,?)''',
                            (sheet, sequence, pid, json.dumps(values, ensure_ascii=False), job['prompt_id'],
                             json.dumps(metadata, ensure_ascii=False), photo_bytes,
                             mimetypes.guess_type(photo.name)[0] or 'image/jpeg', datetime.now(timezone.utc).isoformat()))
        result = {'id': cursor.lastrowid, 'sheet': sheet, 'sequence': sequence, 'pid': pid, 'already_recorded': False}
    (run / 'database-record.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def backup(path, output):
    if Path(path).resolve() == Path(output).resolve() or Path(output).exists():
        raise ValueError('Use a new database backup filename.')
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with closing(connect(path)) as source, closing(sqlite3.connect(str(output))) as target:
        source.backup(target)
