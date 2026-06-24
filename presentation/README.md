# Presentación ejecutiva

## Contenido

- [`RastroSeguro-Pitch.md`](./RastroSeguro-Pitch.md) — Pitch completo listo para exportar
- [`pitch.pdf`](./pitch.pdf) — PDF entregable

## Exportar a PDF

### Opción 1: Python (recomendado)

```bash
pip install fpdf2
python scripts/export_pitch_pdf.py
```

Salida: `presentation/pitch.pdf`

### Opción 2: Pandoc

```powershell
.\scripts\export_pitch_pdf.ps1
```

Requisito: [Pandoc](https://pandoc.org/installing.html) instalado.

### Opción 3: VS Code / Cursor

1. Abrir `presentation/RastroSeguro-Pitch.md`
2. Vista previa Markdown → Imprimir → Guardar como PDF
3. Guardar como `presentation/pitch.pdf`

## Entregable esperado

`presentation/pitch.pdf` — Problema, solución, impacto y próximos pasos (PDF §14).

Copia también en [`entregables/04-presentacion-ejecutiva/`](../entregables/04-presentacion-ejecutiva/).
