import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / 'skills/tiktok-fashion-video/scripts/browser_collect.cjs'
PID = '1732686009998413897'
CDN = 'https://p16-oec-general.ttcdn-us.com/'
PLACEHOLDER = 'https://lf-gs-frontend-cn.fanchenstatic.com/assets/image-upload-placeholder-06.gqw624xw.png'


@unittest.skipUnless(shutil.which('node'), 'Browser collector tests require Node.js')
class TikTokBrowserTests(unittest.TestCase):
    def collect(self, images):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            (directory / 'images.json').write_text(json.dumps(images), encoding='utf-8')
            (directory / 'index.js').write_text('''
const fs = require('node:fs');
const images = JSON.parse(fs.readFileSync(__dirname + '/images.json', 'utf8'));
const page = {
  goto: async url => { global.location = { href: url }; },
  locator: () => ({ first: () => ({ waitFor: async () => {} }) }),
  evaluate: async fn => {
    global.document = {
      querySelector: () => ({ innerText: 'Verified product' }),
      images: images.map(image => ({ src: image.url, closest: () => ({ id: image.id }) })),
    };
    return fn();
  },
};
exports.chromium = {
  launchPersistentContext: async () => ({ pages: () => [page], close: async () => {} }),
};
''', encoding='utf-8')
            return subprocess.run(
                ['node', str(SCRIPT)],
                input=json.dumps({'pid': PID, 'playwright_module': str(directory), 'profile_dir': str(directory)}),
                capture_output=True, text=True, encoding='utf-8', timeout=15,
            )

    def test_five_product_photos_and_three_upload_placeholders(self):
        photos = [{'id': f'main_image_item_{index}', 'url': CDN + f'{index}.jpeg'} for index in range(5)]
        placeholders = [{'id': f'main_image_item_{index}', 'url': PLACEHOLDER} for index in range(6, 9)]
        result = self.collect(list(reversed(photos + placeholders)))
        self.assertEqual(result.returncode, 0, result.stderr)
        product = json.loads(result.stdout)
        self.assertEqual(product['pid'], PID)
        self.assertEqual(product['images'], photos)

    def test_placeholder_cannot_replace_real_photo_in_same_slot(self):
        photo = {'id': 'main_image_item_0', 'url': CDN + 'real.jpeg'}
        unknown_cdn = {'id': 'main_image_item_1', 'url': 'https://unknown.example/product.jpeg'}
        result = self.collect([photo, dict(photo, url=PLACEHOLDER + '?version=1'), unknown_cdn])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['images'], [photo, unknown_cdn])

    def test_only_placeholders_do_not_count_as_product_photos(self):
        result = self.collect([{'id': 'main_image_item_0', 'url': PLACEHOLDER}])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertIn('未返回完整商品资料', result.stderr)


if __name__ == '__main__':
    unittest.main()
