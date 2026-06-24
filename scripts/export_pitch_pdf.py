"""Export presentation/RastroSeguro-Pitch.md to presentation/pitch.pdf (pure Python, no Pandoc)."""

from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "presentation" / "RastroSeguro-Pitch.md"
OUTPUT = ROOT / "presentation" / "pitch.pdf"

# Corporate palette
NAVY = (15, 45, 75)
ACCENT = (0, 120, 100)
GRAY = (80, 80, 80)
LIGHT = (245, 247, 250)

FONT_REGULAR = Path(r"C:\Windows\Fonts\arial.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\arialbd.ttf")
FONT_ITALIC = Path(r"C:\Windows\Fonts\ariali.ttf")
FONT_MONO = Path(r"C:\Windows\Fonts\consola.ttf")


class PitchPDF(FPDF):
    def __init__(self) -> None:
        super().__init__()
        if FONT_REGULAR.exists():
            self.add_font("Body", "", str(FONT_REGULAR))
            self.add_font("Body", "B", str(FONT_BOLD if FONT_BOLD.exists() else FONT_REGULAR))
            self.add_font("Body", "I", str(FONT_ITALIC if FONT_ITALIC.exists() else FONT_REGULAR))
            if FONT_MONO.exists():
                self.add_font("Mono", "", str(FONT_MONO))
            self._font = "Body"
        else:
            self._font = "Helvetica"

    def _set(self, style: str = "", size: int = 10) -> None:
        self.set_font(self._font, style, size)

    def header(self) -> None:
        self._set("B", 9)
        self.set_text_color(*GRAY)
        self.cell(0, 8, "RastroSeguro — hackIAthon 2026 — Aseguradora del Sur", align="R")
        self.ln(4)

    def footer(self) -> None:
        self.set_y(-15)
        self._set("I", 8)
        self.set_text_color(*GRAY)
        self.cell(0, 10, f"Página {self.page_no()}", align="C")


def _strip_md(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    return text.strip()


def export() -> Path:
    if not INPUT.exists():
        raise FileNotFoundError(f"Missing {INPUT}")

    pdf = PitchPDF()
    pdf.set_margins(20, 20, 20)
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    w = pdf.epw
    lines = INPUT.read_text(encoding="utf-8").splitlines()
    in_code = False
    code_lines: list[str] = []

    for raw in lines:
        line = raw.rstrip()

        if line.startswith("```"):
            if in_code:
                pdf.set_fill_color(*LIGHT)
                mono = "Mono" if FONT_MONO.exists() else pdf._font
                pdf.set_font(mono, "", 8)
                pdf.set_text_color(30, 30, 30)
                for cl in code_lines:
                    pdf.multi_cell(w, 5, cl, fill=True)
                pdf.ln(2)
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if line.startswith("# "):
            pdf.ln(4)
            pdf._set("B", 18)
            pdf.set_text_color(*NAVY)
            pdf.multi_cell(w, 10, _strip_md(line[2:]))
            pdf.ln(2)
            continue

        if line.startswith("## "):
            pdf.ln(6)
            pdf._set("B", 14)
            pdf.set_text_color(*ACCENT)
            pdf.multi_cell(w, 8, _strip_md(line[3:]))
            pdf.ln(1)
            continue

        if line.startswith("### "):
            pdf.ln(4)
            pdf._set("B", 11)
            pdf.set_text_color(*NAVY)
            pdf.multi_cell(w, 7, _strip_md(line[4:]))
            continue

        if line.startswith("---"):
            pdf.ln(3)
            pdf.set_draw_color(200, 200, 200)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(4)
            continue

        if line.startswith("|"):
            pdf._set("", 9)
            pdf.set_text_color(40, 40, 40)
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= {"-", " "} for c in cells):
                continue
            row = "  |  ".join(_strip_md(c) for c in cells)
            pdf.multi_cell(w, 6, row)
            continue

        if line.startswith("- "):
            pdf._set("", 10)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(w, 6, f"  - {_strip_md(line[2:])}")
            continue

        if re.match(r"^\d+\.\s", line):
            pdf._set("", 10)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(w, 6, f"  {_strip_md(line)}")
            continue

        if not line.strip():
            pdf.ln(2)
            continue

        pdf._set("", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.multi_cell(w, 6, _strip_md(line))

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUTPUT))
    return OUTPUT


if __name__ == "__main__":
    out = export()
    print(f"PDF generado: {out}")
