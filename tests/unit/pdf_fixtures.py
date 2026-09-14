"""Tiny PDF bytes for ingest/extract tests. Not L1 proving corpora."""

from pathlib import Path


def _build_pdf(objects: list[bytes]) -> bytes:
    header = b"%PDF-1.4\n"
    chunks = [header]
    offsets = []
    pos = len(header)
    for i, obj in enumerate(objects, start=1):
        offsets.append(pos)
        block = f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
        chunks.append(block)
        pos += len(block)
    xref = [b"xref\n", f"0 {len(objects) + 1}\n".encode(), b"0000000000 65535 f \n"]
    for off in offsets:
        xref.append(f"{off:010d} 00000 n \n".encode())
    xref.append(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{pos}\n%%EOF\n"
        ).encode()
    )
    return b"".join(chunks + xref)


def empty_pdf_bytes() -> bytes:
    """One blank page, no text layer."""
    return _build_pdf(
        [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>",
        ]
    )


def text_pdf_bytes(text: str = "Hello narrative prose with no table.") -> bytes:
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({safe}) Tj ET\n".encode()
    contents = f"<< /Length {len(stream)} >>\nstream\n".encode() + stream + b"endstream"
    return _build_pdf(
        [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
            b"/Resources << /Font << /F1 5 0 R >> >> >>",
            contents,
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ]
    )


def write_empty_pdf(path: Path) -> Path:
    path.write_bytes(empty_pdf_bytes())
    return path


def write_text_pdf(path: Path, text: str = "Hello narrative prose with no table.") -> Path:
    path.write_bytes(text_pdf_bytes(text))
    return path
