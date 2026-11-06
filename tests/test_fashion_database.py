import hashlib
import asyncio
import importlib.util
import io
import json
import sqlite3
import tempfile
import unittest
import zipfile
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from lxml import etree as E
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


catalog, excel = load('fashion_database'), load('fashion_excel')
PID = '1731671341404360777'
S, R, X, A, REL = excel.S, excel.R, excel.X, excel.A, excel.REL


def make_workbook(path, products=False):
    def cells(row, values):
        return '<row r="%s">%s</row>' % (row, ''.join(
            f'<c r="{col}{row}" s="0" t="inlineStr"><is><t>{value}</t></is></c>' for col, value in values.items()))
    if products:
        sheets = [('rounded', [cells(1, {'A': 'PID', 'B': 'SPU'}), cells(2, {'A': '1.73167134140436e+18', 'B': 'sku-1'})]),
                  ('exact', [cells(1, {'A': 'PID', 'B': 'SPU'}), cells(2, {'A': PID, 'B': 'sku-1'})])]
    else:
        sheets = [('bnmb', [cells(1, {'A': '编号', 'B': 'PID', 'C': '商品名称'}), cells(2, {'A': 'A1', 'B': PID, 'C': 'Original title', 'I': 'https://example.com/old.mp4'})])]
    image = io.BytesIO()
    Image.new('RGB', (60, 80), 'blue').save(image, format='JPEG')
    with zipfile.ZipFile(path, 'w') as z:
        z.writestr('[Content_Types].xml', '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="jpg" ContentType="image/jpeg"/></Types>')
        z.writestr('xl/workbook.xml', f'<workbook xmlns="{S}" xmlns:r="{R}"><sheets>' + ''.join(f'<sheet name="{name}" sheetId="{i}" r:id="rId{i}"/>' for i, (name, _) in enumerate(sheets, 1)) + '</sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels', f'<Relationships xmlns="{REL}">' + ''.join(f'<Relationship Id="rId{i}" Target="worksheets/sheet{i}.xml" Type="{R}/worksheet"/>' for i in range(1, len(sheets) + 1)) + '</Relationships>')
        z.writestr('xl/styles.xml', f'<styleSheet xmlns="{S}"><cellXfs count="1"><xf numFmtId="0"/></cellXfs></styleSheet>')
        for i, (_, rows) in enumerate(sheets, 1):
            z.writestr(f'xl/worksheets/sheet{i}.xml', f'<worksheet xmlns="{S}" xmlns:r="{R}"><dimension ref="A1:N2"/><sheetData>{"".join(rows)}</sheetData>' + ('<drawing r:id="rId1"/>' if not products else '') + '</worksheet>')
        if not products:
            z.writestr('xl/worksheets/_rels/sheet1.xml.rels', f'<Relationships xmlns="{REL}"><Relationship Id="rId1" Target="../drawings/drawing1.xml" Type="{R}/drawing"/></Relationships>')
            marker = '<x:col>5</x:col><x:colOff>0</x:colOff><x:row>1</x:row><x:rowOff>0</x:rowOff>'
            z.writestr('xl/drawings/drawing1.xml', f'<x:wsDr xmlns:x="{X}" xmlns:a="{A}" xmlns:r="{R}"><x:twoCellAnchor><x:from>{marker}</x:from><x:to>{marker}</x:to><x:pic><x:nvPicPr><x:cNvPr id="1" name="Photo"/></x:nvPicPr><x:blipFill><a:blip r:embed="rId1"/></x:blipFill></x:pic></x:twoCellAnchor></x:wsDr>')
            z.writestr('xl/drawings/_rels/drawing1.xml.rels', f'<Relationships xmlns="{REL}"><Relationship Id="rId1" Target="../media/original.jpg" Type="{R}/image"/></Relationships>')
            z.writestr('xl/media/original.jpg', image.getvalue())
    return image.getvalue()


class FashionDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.video_book, self.product_book = self.root / 'videos.xlsx', self.root / 'products.xlsx'
        self.photo = make_workbook(self.video_book)
        make_workbook(self.product_book, True)
        self.db = self.root / 'catalog.sqlite3'
        catalog.migrate(self.db, self.video_book, self.product_book)

    def make_run(self, number=1, qc=True):
        run = self.root / f'run-{number}'
        (run / 'product').mkdir(parents=True)
        (run / 'product/01.jpg').write_bytes(self.photo)
        (run / 'final.mp4').write_bytes(b'video')
        data = {'analysis.json': {'pid': PID, 'title': 'Verified blouse', 'source_url': 'https://shop.example/product/' + PID},
                'product/manifest.json': {'pid': PID, 'images': [{'index': 1, 'file': '01.jpg', 'sha256': hashlib.sha256(self.photo).hexdigest()}]},
                'job.json': {'prompt_id': f'job-{number}'}}
        if qc:
            data['qc.json'] = {'transcript_english': 'Actual speech', 'translation_chinese': '真实口播', 'caption_english': '=not a formula', 'hashtags': ['#fashion']}
        for name, value in data.items():
            (run / name).write_text(json.dumps(value), encoding='utf-8')
        return run

    def record(self, run):
        return catalog.record_generation(self.db, run, {'path': str(run / 'final.mp4'), 'oss_uri': 'oss://bucket/video'}, 'bnmb', {'url': 'https://example.com/video.mp4'})

    def test_migration_indexes_exact_pids_and_keeps_original_rounded_values(self):
        result = catalog.lookup(self.db, PID)
        self.assertEqual(result['product']['spu'], 'sku-1')
        self.assertEqual(len(result['videos']), 1)
        again = catalog.migrate(self.db, self.video_book, self.product_book)
        self.assertEqual(again['videos'], 1)
        with closing(sqlite3.connect(self.db)) as db:
            raw = db.execute("SELECT values_json FROM source_rows WHERE kind='products' AND sheet='rounded' AND row_number=2").fetchone()[0]
            self.assertEqual(json.loads(raw)['A'], '1.73167134140436e+18')
            plan = db.execute('EXPLAIN QUERY PLAN SELECT pid FROM products WHERE pid=?', (PID,)).fetchall()
            self.assertIn('INDEX', str(plan))

    def test_concurrent_recording_allocates_unique_sequences_and_deduplicates_jobs(self):
        runs = [self.make_run(i) for i in range(4)]
        with ThreadPoolExecutor(max_workers=4) as pool:
            saved = list(pool.map(self.record, runs))
        self.assertEqual({r['sequence'] for r in saved}, {'A2', 'A3', 'A4', 'A5'})
        self.assertTrue(self.record(runs[0])['already_recorded'])
        self.assertEqual(len(catalog.lookup(self.db, PID)['videos']), 5)

    def test_export_preserves_photos_and_text_pids_and_adds_the_generated_record(self):
        original = self.video_book.read_bytes()
        self.record(self.make_run())
        target = self.root / 'export/videos.xlsx'
        result = excel.export_excel(self.db, 'videos', target)
        self.assertEqual(result['appended'][0]['sequence'], 'A2')
        self.assertEqual(self.video_book.read_bytes(), original)
        with zipfile.ZipFile(target) as z:
            self.assertEqual(z.read('xl/media/original.jpg'), self.photo)
            media = [n for n in z.namelist() if 'catalog-video-' in n]
            self.assertEqual(z.read(media[0]), self.photo)
            root = E.fromstring(z.read('xl/worksheets/sheet1.xml'))
            pid = root.find('s:sheetData/s:row/s:c[@r="B3"]', excel.NS)
            self.assertEqual(pid.get('t'), 'inlineStr')
            self.assertEqual(''.join(pid.itertext()), PID)
            caption = root.find('s:sheetData/s:row/s:c[@r="J3"]', excel.NS)
            self.assertEqual(caption.get('t'), 'inlineStr')
            self.assertIsNone(caption.find('s:f', excel.NS))
        products = self.root / 'export/products.xlsx'
        excel.export_excel(self.db, 'products', products)
        with zipfile.ZipFile(products) as z:
            for i in (1, 2):
                root = E.fromstring(z.read(f'xl/worksheets/sheet{i}.xml'))
                cell = root.find('s:sheetData/s:row/s:c[@r="A2"]', excel.NS)
                self.assertEqual(''.join(cell.itertext()), PID)
                self.assertEqual(cell.get('t'), 'inlineStr')

    def test_backup_contains_latest_committed_generation_without_original_workbooks(self):
        self.record(self.make_run())
        target = self.root / 'backup.sqlite3'
        catalog.backup(self.db, target)
        self.video_book.unlink()
        self.product_book.unlink()
        self.assertEqual(len(catalog.lookup(target, PID)['videos']), 2)
        excel.export_excel(target, 'videos', self.root / 'restored.xlsx')

    def test_missing_qc_is_recorded_without_invented_transcription(self):
        run = self.make_run(qc=False)
        self.record(run)
        saved = catalog.lookup(self.db, PID)['videos'][-1]
        self.assertEqual(saved['values']['H'], '')
        self.assertEqual(saved['metadata']['qc'], {})
        (run / 'qc.json').write_text(json.dumps({'transcript_english': 'Recovered speech'}))
        recovered = self.record(run)
        self.assertTrue(recovered['already_recorded'])
        records = catalog.lookup(self.db, PID)['videos']
        self.assertEqual(len(records), 2)
        self.assertEqual(records[-1]['values']['H'], 'Recovered speech')

    def test_changed_verified_photo_is_rejected(self):
        run = self.make_run()
        (run / 'product/01.jpg').write_bytes(b'wrong image')
        with self.assertRaisesRegex(ValueError, 'manifest'):
            self.record(run)

    def test_node_delivery_records_after_publication_and_preserves_video_on_database_error(self):
        from _loader import import_module
        delivery = import_module('fashion_delivery')
        run = self.make_run()
        record = SimpleNamespace(kind='output', status='success', content_type='video/mp4', path=str(run / 'final.mp4'),
                                 sha256=hashlib.sha256(b'video').hexdigest(), disk_dict=lambda: {'path': str(run / 'final.mp4')})
        config = {'oss_enabled': True, 'tiktok_ops': {'enabled': True, 'outbox': str(self.root / 'outbox.sqlite3'), 'sheet': 'bnmb', 'instance_id': 'cpu'}}
        publication = {'url': 'https://example.com/permanent.mp4', 'sha256': record.sha256, 'public_unauthenticated_get_verified': True}
        store = SimpleNamespace(publish_public_video=AsyncMock(return_value=publication))
        identity = {'external_user_id': 'actual-user', 'external_username': 'alice'}
        receipts = [{'sequence': 'A2', 'sheet': 'bnmb'}, {'sequence': 'A2', 'sheet': 'bnmb', 'already_recorded': True}]
        with patch.object(delivery, 'OSSArtifactStore', return_value=store), patch.object(delivery, 'record_generation', side_effect=receipts) as submit:
            result = asyncio.run(delivery.record_outputs([record], self.root, 'node-job', config, True, identity))
            again = asyncio.run(delivery.record_outputs([record], self.root, 'node-job', config, True, identity))
        self.assertEqual(result['records'][0]['sequence'], 'A2')
        self.assertTrue(again['records'][0]['already_recorded'])
        store.publish_public_video.assert_awaited_once()
        self.assertEqual(submit.call_args.args[3], identity)
        self.assertEqual(submit.call_args.args[4], publication)
        with patch.object(delivery, 'record_generation', side_effect=ValueError('invalid config')):
            failed = asyncio.run(delivery.record_outputs([record], self.root, 'node-job', config, True, identity))
        self.assertTrue(failed['warnings'])
        self.assertTrue((run / 'final.mp4').exists())


if __name__ == '__main__':
    unittest.main()
