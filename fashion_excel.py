"""Export the catalog using preserved OOXML parts, retaining native Excel pictures."""
import copy
import io
import json
import os
import posixpath
import re
import sqlite3
import zipfile
from contextlib import closing
from pathlib import Path

from lxml import etree as E
from PIL import Image

S = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
REL = 'http://schemas.openxmlformats.org/package/2006/relationships'
X = 'http://schemas.openxmlformats.org/drawingml/2006/spreadsheetDrawing'
A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
NS = {'s': S, 'x': X, 'a': A}


def rel_name(part):
    return posixpath.join(posixpath.dirname(part), '_rels', posixpath.basename(part) + '.rels')


def target_name(part, target):
    return target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join(posixpath.dirname(part), target))


def next_rel(root):
    return 'rId' + str(max([int(r.get('Id')[3:]) for r in root if re.fullmatch(r'rId[0-9]+', r.get('Id', ''))] or [0]) + 1)


def text_cell(cell, value, style=None):
    for child in list(cell):
        cell.remove(child)
    cell.set('t', 'inlineStr')
    if style is not None:
        cell.set('s', str(style))
    inline = E.SubElement(cell, '{' + S + '}is')
    text = E.SubElement(inline, '{' + S + '}t')
    text.set('{http://www.w3.org/XML/1998/namespace}space', 'preserve')
    text.text = value


def export_excel(database, kind, output):
    output = Path(output)
    with closing(sqlite3.connect('file:' + Path(database).resolve().as_posix() + '?mode=ro', uri=True)) as db:
        db.row_factory = sqlite3.Row
        db.execute('BEGIN')  # Export one consistent snapshot while other jobs append.
        workbook = db.execute('SELECT * FROM workbooks WHERE kind=?', (kind,)).fetchone()
        if workbook is None:
            raise ValueError(f'Workbook {kind} has not been imported.')
        parts = {r['name']: r['data'] for r in db.execute('SELECT name,data FROM workbook_parts WHERE kind=?', (kind,))}
        original_media = {name: data for name, data in parts.items() if name.startswith('xl/media/')}
        styles = E.fromstring(parts['xl/styles.xml'])
        xfs = styles.find('s:cellXfs', NS)
        pid_styles = {}

        def pid_style(original):
            original = int(original or 0)
            if original not in pid_styles:
                xf = copy.deepcopy(xfs[original])
                xf.set('numFmtId', '49')
                xf.set('applyNumberFormat', '1')
                pid_styles[original] = len(xfs)
                xfs.append(xf)
                xfs.set('count', str(len(xfs)))
            return pid_styles[original]
        appended = []
        for sheet in db.execute('SELECT * FROM sheets WHERE kind=? ORDER BY position', (kind,)):
            part = sheet['part_name']
            root = E.fromstring(parts[part])
            sheet_data = root.find('s:sheetData', NS)
            for override in db.execute('SELECT cell,value FROM cell_overrides WHERE kind=? AND sheet=?', (kind, sheet['name'])):
                cell = sheet_data.find(f's:row/s:c[@r="{override["cell"]}"]', NS)
                if cell is None:
                    raise ValueError('PID normalization target missing from the preserved workbook.')
                text_cell(cell, override['value'], pid_style(cell.get('s')))
            records = db.execute('SELECT * FROM videos WHERE source_row IS NULL AND sheet=? ORDER BY id', (sheet['name'],)).fetchall() if kind == 'videos' else []
            if records:
                sheet_rels = E.fromstring(parts[rel_name(part)])
                draw_rel = next(r for r in sheet_rels if r.get('Type').endswith('/drawing'))
                draw_part = target_name(part, draw_rel.get('Target'))
                drawing = E.fromstring(parts[draw_part])
                draw_rels = E.fromstring(parts[rel_name(draw_part)])
                template = next(a for a in reversed(list(drawing)) if a.find('x:pic', NS) is not None)
                last = db.execute('SELECT MAX(row_number) FROM source_rows WHERE kind=? AND sheet=?', (kind, sheet['name'])).fetchone()[0]
                previous = sheet_data.find(f's:row[@r="{last}"]', NS)
                column_styles = {re.sub(r'[0-9]', '', c.get('r')): c.get('s', '0') for c in previous}
                links = root.find('s:hyperlinks', NS)
                if links is None:
                    links = E.Element('{' + S + '}hyperlinks')
                    before = next((child for child in root if E.QName(child).localname in {
                        'printOptions', 'pageMargins', 'pageSetup', 'headerFooter', 'drawing', 'legacyDrawing', 'extLst'}), None)
                    root.insert(root.index(before), links) if before is not None else root.append(links)
                for offset, record in enumerate(records, 1):
                    number = last + offset
                    old_row = sheet_data.find(f's:row[@r="{number}"]', NS)
                    if old_row is not None:
                        if old_row.find('s:c/s:v', NS) is not None or old_row.find('s:c/s:is', NS) is not None:
                            raise ValueError('Export append would replace an existing row.')
                        sheet_data.remove(old_row)
                    row = E.Element('{' + S + '}row', r=str(number), customHeight='1', ht='240')
                    values = json.loads(record['values_json'])
                    for col in 'ABCDEFGHIJKLMN':
                        cell = E.SubElement(row, '{' + S + '}c', r=f'{col}{number}', s=column_styles.get(col, '0'))
                        text_cell(cell, values.get(col, ''), pid_style(cell.get('s')) if col == 'B' else None)
                    after = next((r for r in sheet_data if int(r.get('r')) > number), None)
                    sheet_data.insert(sheet_data.index(after), row) if after is not None else sheet_data.append(row)
                    if values.get('I', '').startswith(('https://', 'http://')):
                        link_id = next_rel(sheet_rels)
                        E.SubElement(sheet_rels, '{' + REL + '}Relationship', Id=link_id, Type=R + '/hyperlink', Target=values['I'], TargetMode='External')
                        link = E.SubElement(links, '{' + S + '}hyperlink', ref=f'I{number}')
                        link.set('{' + R + '}id', link_id)
                    if record['photo']:
                        with Image.open(io.BytesIO(record['photo'])) as image:
                            width = min(56, 220 * image.width / image.height)
                            height = width * image.height / image.width
                            ext = 'png' if image.format == 'PNG' else 'jpg'
                        media = f'xl/media/catalog-video-{record["id"]}.{ext}'
                        if media in parts:
                            raise ValueError('Generated photo name collides with an imported workbook asset.')
                        parts[media] = record['photo']
                        image_id = next_rel(draw_rels)
                        E.SubElement(draw_rels, '{' + REL + '}Relationship', Id=image_id, Type=R + '/image', Target='../media/' + posixpath.basename(media))
                        anchor = copy.deepcopy(template)
                        for tag, col_offset, row_offset in [('from', 4, 4), ('to', 4 + width, 4 + height)]:
                            marker = anchor.find('x:' + tag, NS)
                            if marker is None:
                                raise ValueError('BC photo template requires a two-cell anchor.')
                            for key, value in [('col', 5), ('colOff', round(col_offset * 9525)), ('row', number - 1), ('rowOff', round(row_offset * 9525))]:
                                marker.find('x:' + key, NS).text = str(value)
                        prop = anchor.find('x:pic/x:nvPicPr/x:cNvPr', NS)
                        prop.set('id', str(max(int(p.get('id')) for p in drawing.findall('.//x:cNvPr', NS)) + 1))
                        prop.set('name', f'Catalog video {record["id"]}')
                        prop.set('descr', f'Original product photo PID {record["pid"]}')
                        anchor.find('.//a:blip', NS).set('{' + R + '}embed', image_id)
                        drawing.append(anchor)
                        types = E.fromstring(parts['[Content_Types].xml'])
                        if not any(e.get('Extension') == ext for e in types):
                            E.SubElement(types, '{http://schemas.openxmlformats.org/package/2006/content-types}Default', Extension=ext, ContentType='image/png' if ext == 'png' else 'image/jpeg')
                            parts['[Content_Types].xml'] = E.tostring(types)
                    appended.append({'sheet': sheet['name'], 'row': number, 'sequence': record['sequence'], 'pid': record['pid']})
                dimension = root.find('s:dimension', NS)
                if dimension is not None:
                    bounds = dimension.get('ref').split(':')
                    old_end = int(re.search(r'[0-9]+$', bounds[-1])[0])
                    dimension.set('ref', bounds[0] + ':N' + str(max(old_end, last + len(records))))
                parts[rel_name(part)] = E.tostring(sheet_rels)
                parts[draw_part] = E.tostring(drawing)
                parts[rel_name(draw_part)] = E.tostring(draw_rels)
            parts[part] = E.tostring(root)
        parts['xl/styles.xml'] = E.tostring(styles)
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix('.xlsx.tmp')
        with zipfile.ZipFile(temporary, 'w', zipfile.ZIP_DEFLATED) as z:
            for name, data in parts.items():
                z.writestr(name, data)
        with zipfile.ZipFile(temporary) as z:
            if z.testzip() is not None or any(z.read(name) != data for name, data in original_media.items()):
                raise ValueError('Export validation failed; existing pictures were not preserved.')
        os.replace(temporary, output)
    return {'file': str(output.resolve()), 'existing_images_preserved': len(original_media), 'appended': appended}
