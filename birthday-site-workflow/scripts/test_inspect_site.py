"""Resource references must use decoded HTML attributes and complete CSS URLs."""
import unittest
from inspect_site import html_references,css_references


class References(unittest.TestCase):
    def test_encoded_inline_style_and_attributes(self):
        refs=html_references('<html style="--motif:url(&quot;assets/my%20motif.svg&quot;)"><img src="assets/a&amp;b.png"><a href="#quiz">Quiz</a></html>')
        self.assertEqual(refs,['assets/my%20motif.svg','assets/a&b.png','#quiz'])

    def test_css_paths_with_spaces_and_queries(self):
        self.assertEqual(css_references('a{background:url("assets/my image.png")}b{background:url(assets/b.png?v=1)}'),['assets/my image.png','assets/b.png?v=1'])

    def test_style_element_but_not_script_or_prose(self):
        refs=html_references('<style>p{background:url(assets/p.png)}</style><script>const example="url(missing.png)";</script><p>url(example.png)</p>')
        self.assertEqual(refs,['assets/p.png'])


if __name__=='__main__':unittest.main()
