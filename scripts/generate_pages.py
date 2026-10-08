#!/usr/bin/env python3
"""Regenere les pages web embarquees dans le composant a partir de leurs sources HTML.
Regenerate the web pages embedded in the component from their HTML sources.

  python3 scripts/generate_pages.py           # regenerer / regenerate
  python3 scripts/generate_pages.py --check   # verifier seulement / check only (exit 1 if stale)
"""
from __future__ import annotations

import gzip
import sys
from pathlib import Path

COMPONENT = Path(__file__).resolve().parents[1] / "esphome/components/nightmatiq_mesh"
# (source HTML, en-tete genere, symbole C++, format historique avec _RAW_SIZE)
PAGES = [
    ("steinel_dashboard.html", "steinel_dashboard.h", "STEINEL_DASHBOARD_GZ", False),  # /
    ("steinel_advanced.html", "steinel_advanced.h", "STEINEL_ADVANCED_GZ", False),     # /steinel/avance
    ("nightmatiq_page.html", "nightmatiq_page.h", "NIGHTMATIQ_PAGE_GZ", True),         # /steinel/classique
]


def render(raw: bytes, symbol: str, with_raw_size: bool) -> tuple[str, int]:
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)
    # octet "OS" de l'en-tete gzip fixe a 255 : sortie identique sur macOS, Linux et Windows
    compressed = compressed[:9] + b"\xff" + compressed[10:]
    rows = [
        "  " + ", ".join(f"0x{value:02x}" for value in compressed[offset : offset + 16]) + ","
        for offset in range(0, len(compressed), 16)
    ]
    if with_raw_size:
        head = (
            "#pragma once\n#include <cstddef>\n#include <cstdint>\n"
            "namespace esphome::nightmatiq_mesh {\n"
            f"static constexpr size_t {symbol.removesuffix('_GZ')}_RAW_SIZE = {len(raw)};\n"
        )
    else:
        head = "#pragma once\n#include <cstdint>\nnamespace esphome::nightmatiq_mesh {\n"
    body = f"static const uint8_t {symbol}[{len(compressed)}] = {{\n" + "\n".join(rows) + "\n};\n"
    return head + body + "}  // namespace esphome::nightmatiq_mesh\n", len(compressed)


def main() -> int:
    check = "--check" in sys.argv[1:]
    problems = 0
    for source_name, header_name, symbol, with_raw_size in PAGES:
        source, header = COMPONENT / source_name, COMPONENT / header_name
        if not source.exists():
            print(f"ABSENT : {source_name}")
            problems += 1
            continue
        raw = source.read_bytes()
        text, size = render(raw, symbol, with_raw_size)
        current = header.read_text(encoding="utf-8") if header.exists() else ""
        if check:
            up_to_date = current == text
            print(f"{'OK' if up_to_date else 'A REGENERER / STALE'} : {header_name}")
            problems += 0 if up_to_date else 1
        else:
            if current != text:
                header.write_text(text, encoding="utf-8")
            print(f"{header_name} : {len(raw)} -> {size} octets / bytes")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
