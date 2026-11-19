import base64
import io
import unittest
import zipfile

from document_ingestion import extract_document


def make_docx(xml):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as archive:
        archive.writestr('word/document.xml', xml)
    return base64.b64encode(buffer.getvalue()).decode('ascii')


class DocumentIngestionTests(unittest.TestCase):
    def test_extracts_paragraph_text_from_docx(self):
        xml = b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Hello brand review</w:t></w:r></w:p></w:body></w:document>'
        result = extract_document({'name': 'draft.docx', 'data': make_docx(xml)})
        self.assertIn('Hello brand review', result['text'])

    def test_rejects_malformed_docx_xml(self):
        with self.assertRaises(Exception):
            extract_document({'name': 'broken.docx', 'data': make_docx(b'<w:document>')})

    def test_rejects_xml_entity_declarations(self):
        xml = b'<!DOCTYPE x [<!ENTITY secret "unexpected">]><w:document xmlns:w="urn:w"><w:p>&secret;</w:p></w:document>'
        with self.assertRaises(Exception):
            extract_document({'name': 'entity.docx', 'data': make_docx(xml)})

    def test_rejects_docx_without_document_part(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            archive.writestr('word/header.xml', '<header/>')
        data = base64.b64encode(buffer.getvalue()).decode('ascii')
        with self.assertRaises(KeyError):
            extract_document({'name': 'missing-part.docx', 'data': data})


if __name__ == '__main__':
    unittest.main()
