import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from tools.docx_renderer.render_docx import render_docx


class DocxRendererTests(unittest.TestCase):
    def test_render_docx_creates_readable_docx(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output = Path(temp_dir) / "report.docx"

            render_docx(
                output,
                "Redis RDB Analysis Report",
                [{"heading": "Target", "lines": ["dump.rdb"]}],
            )

            self.assertTrue(output.exists())
            with ZipFile(output) as archive:
                self.assertIn("[Content_Types].xml", archive.namelist())
                self.assertIn("word/document.xml", archive.namelist())
                document_xml = archive.read("word/document.xml").decode("utf-8")

            self.assertIn("Redis RDB Analysis Report", document_xml)
            self.assertIn("dump.rdb", document_xml)


if __name__ == "__main__":
    unittest.main()
