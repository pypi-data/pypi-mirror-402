import os
from pathlib import Path
from typing import Annotated, Optional

from typer import Argument, Option, Typer

from docuguru.default import DEFAULT_CSS
from docuguru.html_to_pdf import HTMLToPDF
from docuguru.markdon_to_html import MarkdownToHTML

app = Typer(help="Herramienta para convertir documentos Markdown a PDF.")


@app.command(name="convert")
def convert(
    markdown_file: str = Argument(help="Ruta al archivo Markdown a convertir."),
    output: Optional[str] = Option(
        None,
        "--output",
        "-o",
        help="Ruta del archivo PDF de salida. Si no se especifica, se usa el nombre del archivo Markdown con extensión .pdf",
    ),
    title: Optional[str] = Option(
        None,
        "--title",
        "-t",
        help="Título del documento. Si no se especifica, se extrae del primer h1 o se usa el nombre del archivo.",
    ),
    no_cover: bool = Option(
        False,
        "--no-cover",
        help="No incluir página de portada en el PDF.",
    ),
    badge: Optional[str] = Option(
        None,
        "--badge",
        "-b",
        help="Texto del badge en la portada. Por defecto: 'Propuesta técnica'.",
    ),
    date: Optional[str] = Option(
        None,
        "--date",
        "-d",
        help="Fecha para la portada (ej: 'Diciembre 2025'). Si no se especifica, se usa la fecha actual.",
    ),
):
    """
    Convierte un archivo Markdown a PDF.

    Soporta títulos (h1-h6), tablas y listas ordenadas/no ordenadas.
    Genera un PDF con estilos predefinidos e incluye una página de portada por defecto.
    """
    markdown_to_html = MarkdownToHTML()
    body_html = markdown_to_html.convert_file(markdown_file)

    if title is None:
        title = _extract_title_from_html(body_html) or Path(markdown_file).stem

    if output is None:
        output = str(Path(markdown_file).with_suffix(".pdf"))

    html_to_pdf = HTMLToPDF()
    html_to_pdf.generate_pdf(
        body_html,
        title,
        DEFAULT_CSS,
        output,
        include_cover=not no_cover,
        cover_badge=badge if badge else "Propuesta técnica",
        cover_date=date,
    )
    print(f"PDF generado exitosamente: {output}")


@app.command(name="blocks")
def list_blocks(
    output_file: Optional[str] = Option(
        None,
        "--output",
        "-o",
        help="Archivo donde guardar la documentación de bloques. Si no se especifica, se imprime en stdout.",
    ),
):
    """
    Muestra la documentación de todos los bloques HTML personalizados disponibles.

    Lista todos los componentes custom con ejemplos de uso y explicación.
    """
    blocks_doc = _generate_blocks_documentation()

    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(blocks_doc)
        print(f"Documentación guardada en: {output_file}")
    else:
        print(blocks_doc)


def _generate_blocks_documentation() -> str:
    return """# Bloques HTML Personalizados Disponibles

## 1. Architecture Diagram

Muestra un diagrama de arquitectura centrado.

**Uso:**
```html
<div class="architecture-diagram">
    <img src="ruta/imagen.png" alt="Descripción" />
</div>
```

---

## 2. Info Card

Tarjeta informativa con bordes y sombras, ideal para fases o información destacada.

**Uso:**
```html
<div class="info-card">
    <h3>Título</h3>
    <p><strong>Subtítulo en negrita</strong></p>
    <p>Información adicional</p>
    <p>Más detalles</p>
</div>
```

---

## 3. Timeline

Línea de tiempo vertical con items conectados.

**Uso:**
```html
<div class="timeline">
    <div class="timeline-item">
        <strong>Título del Hito</strong>
        <p>Descripción del hito o fase</p>
    </div>
    <div class="timeline-item">
        <strong>Siguiente Hito</strong>
        <p>Otra descripción</p>
    </div>
</div>
```

---

## 4. Summary Cards

Tarjetas de resumen horizontales con valores destacados.

**Uso:**
```html
<div class="summary-cards">
    <div class="summary-card">
        <h3>Categoría</h3>
        <div class="value">$1.000.000</div>
        <div class="label">periodo</div>
    </div>
    <div class="summary-card">
        <h3>Otra Categoría</h3>
        <div class="value">500</div>
        <div class="label">unidades</div>
    </div>
</div>
```

---

## 5. Support Packages

Tarjetas de paquetes de servicios lado a lado.

**Uso:**
```html
<div class="support-packages">
    <div class="package-card">
        <div class="package-header">
            <h3 class="package-name">Básico</h3>
            <div class="package-price">$500.000</div>
            <div class="package-price-label">mensual</div>
        </div>
        <ul class="package-features">
            <li class="no-style">Feature 1</li>
            <li class="no-style">Feature 2</li>
        </ul>
    </div>
    
    <div class="package-card featured">
        <div class="package-header">
            <span class="package-badge">Recomendado</span>
            <h3 class="package-name">Premium</h3>
            <div class="package-price">$1.200.000</div>
            <div class="package-price-label">mensual</div>
        </div>
        <ul class="package-features">
            <li class="no-style">Feature premium 1</li>
            <li class="no-style">Feature premium 2</li>
        </ul>
    </div>
</div>
```

**Nota:** Usa `class="featured"` para destacar un paquete.

---

## 6. Styled List

Lista con checkmarks personalizados (✔).

**Uso:**
```html
<ul class="styled-list">
    <li>Item 1 con checkmark</li>
    <li>Item 2 con checkmark</li>
    <li>Item 3 con checkmark</li>
</ul>
```

---

## 7. Warranty Notice

Bloque de aviso o garantía destacado con fondo azul claro.

**Uso:**
```html
<div class="warranty-notice">
    <p><strong>Título del Aviso:</strong> Texto del aviso o garantía aquí.</p>
</div>
```

---

## Características Adicionales

### Listas Ordenadas Estilizadas

Las listas ordenadas (`<ol>`) se muestran con números en círculos azules automáticamente.

**Para desactivar el estilo:**
```html
<ol class="no-style">
    <li>Item con numeración estándar</li>
    <li>Otro item sin estilización</li>
</ol>
```

### Listas dentro de Package Features

Usa `class="no-style"` en cada `<li>` dentro de `package-features` para evitar los checkmarks:

```html
<ul class="package-features">
    <li class="no-style">Sin checkmark</li>
</ul>
```

---

## Notas Importantes

1. Todos los bloques respetan `page-break-inside: avoid` para evitar cortes en medio del contenido.
2. Los colores utilizan variables CSS definidas en el tema (--primary, --accent, --accent-dark, etc.).
3. Los gradientes usan la paleta azul del tema (#7dd3fc, #3b82f6).
"""


def _extract_title_from_html(html: str) -> str:
    import re

    match = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    if match:
        title_text = re.sub(r"<[^>]+>", "", match.group(1))
        return title_text.strip()
    return None
