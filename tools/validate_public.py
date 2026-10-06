#!/usr/bin/env python3
"""Validate links, public-safety markers and Office/PDF package content."""
from __future__ import annotations

import hashlib
import html.parser
import json
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".html", ".css", ".js", ".md", ".txt", ""}
OFFICE_SUFFIXES = {".docx", ".pptx"}
SKIP_SCAN = {Path("tools/validate_public.py"), Path(".gitignore")}
FORBIDDEN = {
    "windows_drive": re.compile(r"(?i)(?:[A-Z]:\\|[A-Z]:/)(?:Users|WorckBook|MS8AT|System|Codex)"),
    "localhost": re.compile(r"(?i)\b(?:localhost|127\.0\.0\.1)\b"),
    "private_ipv4": re.compile(r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "secret_assignment": re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9_./+\-=]{12,}"),
}


class LinkCollector(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for key in ("href", "src", "poster"):
            value = values.get(key)
            if value:
                self.links.append((key, value))


def read_public_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in TEXT_SUFFIXES:
        return path.read_text(encoding="utf-8-sig", errors="replace")
    if suffix in OFFICE_SUFFIXES:
        chunks: list[str] = []
        with zipfile.ZipFile(path) as archive:
            for item in archive.infolist():
                if item.filename.endswith((".xml", ".rels", ".txt")):
                    chunks.append(archive.read(item).decode("utf-8", errors="replace"))
        return "\n".join(chunks)
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
            return "\n".join(page.extract_text() or "" for page in PdfReader(str(path)).pages)
        except Exception:
            return path.read_bytes().decode("latin-1", errors="ignore")
    return ""


def main() -> int:
    errors: list[str] = []
    files = sorted(p for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts and p.name != "manifest.sha256")
    for path in files:
        rel = path.relative_to(ROOT)
        if rel in SKIP_SCAN:
            continue
        text = read_public_text(path)
        for label, pattern in FORBIDDEN.items():
            if pattern.search(text):
                errors.append(f"{rel.as_posix()}: forbidden marker {label}")

    html_path = ROOT / "index.html"
    parser = LinkCollector()
    parser.feed(html_path.read_text(encoding="utf-8"))
    for kind, target in parser.links:
        split = urlsplit(target)
        if split.scheme or target.startswith("#") or target.startswith("mailto:"):
            continue
        local = ROOT / unquote(split.path)
        if not local.is_file():
            errors.append(f"index.html: missing {kind} target {target}")

    required = {
        "ru": ["Future_Flow_Quick_RU", "Future_Flow_Short_RU", "Анкета_развития"],
        "zh": ["Future_Flow_Quick_ZH", "Future_Flow_Short_ZH", "商业发展问卷"],
        "en": ["Future_Flow_Quick_EN", "Future_Flow_Short_EN", "Business_Questionnaire"],
    }
    names = "\n".join(p.name for p in files)
    for lang, markers in required.items():
        for marker in markers:
            if marker not in names:
                errors.append(f"missing {lang} artifact marker: {marker}")

    result = {
        "status": "FAIL" if errors else "PASS",
        "files_checked": len(files),
        "links_checked": len(parser.links),
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
