"""Extract reviewable source text without treating uploads as instructions."""
import base64
import io
import zipfile
from pathlib import Path
from xml.etree import ElementTree

try:
    from defusedxml import ElementTree as SafeElementTree
except ImportError:
    SafeElementTree = None


def extract_document(data):
    name = str(data.get('name', ''))
    raw = base64.b64decode(data.get('data', ''), validate=True)
    if not raw or len(raw) > 10 * 1024 * 1024:
        raise ValueError('Choose a nonempty file smaller than 10 MB.')
    extension = Path(name).suffix.lower()
    if extension in ('.txt', '.md', '.csv'):
        text = raw.decode('utf-8-sig')
    elif extension == '.docx':
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            info = archive.getinfo('word/document.xml')
            if info.file_size > 20 * 1024 * 1024:
                raise ValueError('Document expands beyond the supported size.')
            xml = archive.read(info)
            if SafeElementTree is None and any(token in xml.upper() for token in (b'<!DOCTYPE', b'<!ENTITY')):
                raise ValueError('DOCX contains unsupported XML declarations. Re-save it as a standard DOCX file.')
            parser = SafeElementTree if SafeElementTree is not None else ElementTree
            root = parser.fromstring(xml)
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            text = '\n'.join(''.join(p.itertext()) for p in root.findall('.//w:p', ns))
    elif extension == '.pdf':
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise ValueError('PDF parsing requires pypdf. Start the server with the bundled Python runtime or install requirements.txt.') from exc
        reader = PdfReader(io.BytesIO(raw))
        if reader.is_encrypted:
            raise ValueError('Unlock the PDF before importing it.')
        if len(reader.pages) > 200:
            raise ValueError('Import up to 200 pages at a time.')
        text = '\n\n'.join(f'[Page {i + 1}]\n{page.extract_text() or ""}' for i, page in enumerate(reader.pages))
    else:
        raise ValueError('Supported formats: TXT, Markdown, CSV, PDF and DOCX.')
    if not text.strip():
        raise ValueError('No text found. Scanned documents need OCR before import.')
    return {'name': name, 'text': text[:500000], 'truncated': len(text) > 500000, 'status': 'Unapproved import — review before adding to the ledger'}
