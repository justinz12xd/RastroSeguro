# Export pitch.md to presentation/pitch.pdf using Pandoc
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Input = Join-Path $Root "presentation\pitch.md"
$Output = Join-Path $Root "presentation\pitch.pdf"

if (-not (Get-Command pandoc -ErrorAction SilentlyContinue)) {
    Write-Host "Pandoc no está instalado. Exporta manualmente desde VS Code o instala pandoc."
    Write-Host "Markdown fuente: $Input"
    exit 1
}

pandoc $Input -o $Output --pdf-engine=wkhtmltopdf 2>$null
if ($LASTEXITCODE -ne 0) {
    pandoc $Input -o $Output
}
if (Test-Path $Output) {
    Write-Host "PDF generado: $Output"
} else {
    Write-Host "No se pudo generar PDF. Usa pitch.md directamente."
    exit 1
}
