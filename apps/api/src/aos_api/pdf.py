"""Minimal text-only PDF writer (ADR-010): Helvetica core font, escaped
text, deterministic pagination. No external dependencies, no HTML."""


def _escape(text: str) -> str:
    return (
        text.replace("\\", r"\\")
        .replace("(", r"\(")
        .replace(")", r"\)")
        .encode("ascii", "replace")
        .decode()
    )


def _wrap(text: str, width: int = 92) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word[:width]
            if len(word) > width:
                for start in range(width, len(word), width):
                    lines.append(word[start : start + width])
    if current:
        lines.append(current)
    return lines or [""]


def render_pdf(title: str, blocks: list[tuple[str, list[str]]]) -> bytes:
    """blocks = [(heading, [paragraph, ...]), ...] -> valid multi-page PDF.

    Object layout is decided up front:
      1 = font, 2..C+1 = content streams, C+2..C+P+1 = pages,
      C+P+2 = pages tree, C+P+3 = catalog.
    """
    lines: list[tuple[str, int]] = [(title, 18)]
    for heading, paragraphs in blocks:
        if heading:
            lines.append((heading, 13))
        for paragraph in paragraphs:
            lines.extend((text, 10) for text in _wrap(paragraph))
    pages: list[list[tuple[str, int]]] = [
        lines[index : index + 44] for index in range(0, max(len(lines), 1), 44)
    ] or [[("", 10)]]

    stream_ids = list(range(2, 2 + len(pages)))
    page_ids = list(range(2 + len(pages), 2 + 2 * len(pages)))
    pages_id = page_ids[-1] + 1
    catalog_id = pages_id + 1

    objects: dict[int, bytes] = {
        1: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        pages_id: (
            f"<< /Type /Pages /Count {len(pages)} /Kids [".encode()
            + b" ".join(f"{pid} 0 R".encode() for pid in page_ids)
            + b"] >>"
        ),
        catalog_id: f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode(),
    }
    for page_number, (stream_id, page_id) in enumerate(zip(stream_ids, page_ids, strict=True)):
        stream_lines = ["BT"]
        y = 780
        for text, size in pages[page_number]:
            stream_lines.append(f"/F1 {size} Tf 1 0 0 1 60 {y} Tm ({_escape(text)}) Tj")
            y -= size + 8
        stream_lines.append("ET")
        stream = "\n".join(stream_lines).encode("ascii")
        objects[stream_id] = (
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"
        )
        objects[page_id] = (
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 1 0 R >> >> /Contents {stream_id} 0 R >>".encode()
        )

    out = bytearray(b"%PDF-1.4\n")
    offsets: list[int] = []
    for number in range(1, catalog_id + 1):
        offsets.append(len(out))
        out += f"{number} 0 obj\n".encode() + objects[number] + b"\nendobj\n"
    xref_start = len(out)
    out += f"xref\n0 {len(offsets) + 1}\n0000000000 65535 f \n".encode()
    for offset in offsets:
        out += f"{offset:010d} 00000 n \n".encode()
    out += (
        f"trailer\n<< /Size {len(offsets) + 1} /Root {catalog_id} 0 R >>\n"
        f"startxref\n{xref_start}\n%%EOF\n"
    ).encode()
    return bytes(out)
