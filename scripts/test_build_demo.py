import hashlib
import pathlib
import tempfile
import unittest
from build_demo import build_demo,TEMPLATE


class Demo(unittest.TestCase):
    def test_subdirectory_output_is_dist_only_and_preserves_template(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=pathlib.Path(temporary)/'pages'
            before={name:hashlib.sha256((TEMPLATE/name).read_bytes()).hexdigest()
                    for name in ('site.json','content.json','dist/index.html')}
            build_demo(output,'https://example.com/demo/')
            page=(output/'index.html').read_text(encoding='utf-8')
            self.assertIn('content="https://example.com/demo/"',page)
            self.assertIn('https://example.com/demo/assets/branding/social-card.png?v=',page)
            self.assertIn('id="demoNotice"',page);self.assertIn('replacement-guide.md',page)
            self.assertTrue((output/'.nojekyll').is_file())
            self.assertFalse((output/'site.json').exists());self.assertFalse((output/'materials').exists())
            self.assertTrue((output/'assets/branding/favicon.svg').is_file())
            self.assertEqual(before,{name:hashlib.sha256((TEMPLATE/name).read_bytes()).hexdigest() for name in before})
            with self.assertRaisesRegex(ValueError,'new output'):build_demo(output,'https://example.com/demo/')


if __name__=='__main__':unittest.main()
