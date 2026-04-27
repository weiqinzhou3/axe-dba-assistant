"""Minimal reusable docx renderer.

This module intentionally contains no Redis-specific business logic.
"""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import html


CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""

ROOT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""

DOCUMENT_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>
"""

APP_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">
  <Application>axe-dba-assistant</Application>
</Properties>
"""

CORE_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <dc:creator>axe-dba-assistant</dc:creator>
</cp:coreProperties>
"""


def _paragraph(text, style=None):
    escaped = html.escape(str(text), quote=False)
    if style:
        style_xml = '<w:pPr><w:pStyle w:val="%s"/></w:pPr>' % html.escape(style)
    else:
        style_xml = ""
    return "<w:p>%s<w:r><w:t>%s</w:t></w:r></w:p>" % (style_xml, escaped)


def _document_xml(title, sections):
    body = [_paragraph(title, "Title")]
    for section in sections:
        heading = section.get("heading", "")
        if heading:
            body.append(_paragraph(heading, "Heading1"))
        for line in section.get("lines", []):
            body.append(_paragraph(line))

    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    %s
    <w:sectPr/>
  </w:body>
</w:document>
""" % "\n".join(body)


def render_docx(output_path, title, sections):
    """Render a minimal docx file with a title and section paragraphs."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", CONTENT_TYPES)
        archive.writestr("_rels/.rels", ROOT_RELS)
        archive.writestr("word/_rels/document.xml.rels", DOCUMENT_RELS)
        archive.writestr("word/document.xml", _document_xml(title, sections))
        archive.writestr("docProps/app.xml", APP_XML)
        archive.writestr("docProps/core.xml", CORE_XML)

    return output
