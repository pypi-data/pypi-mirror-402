import re
from typing import Dict, List, Tuple, Union
from weasyprint import HTML, CSS


class HTMLToPDF:
    def __init__(self):
        pass

    def _process_css(self, css: Union[str, Dict[str, Dict[str, str]]]) -> str:
        if isinstance(css, str):
            return css
        css_rules = []
        for selector, properties in css.items():
            css_rule = f"{selector} {{\n"
            for property_name, property_value in properties.items():
                css_rule += f"    {property_name}: {property_value};\n"
            css_rule += "}"
            css_rules.append(css_rule)
        return "\n\n".join(css_rules)

    def _generate_html(
        self,
        body_content: str,
        title: str,
        css: Union[str, Dict[str, Dict[str, str]]],
    ) -> str:
        css_content = self._process_css(css)

        html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <style>
{css_content}
    </style>
</head>
<body>
{body_content}
</body>
</html>"""
        return html

    def generate_html(
        self,
        body_content: str,
        title: str,
        css: Union[str, Dict[str, Dict[str, str]]],
    ) -> str:
        return self._generate_html(body_content, title, css)

    def _extract_headings(self, html: str) -> List[Tuple[int, str, str]]:
        headings = []
        pattern = r"<h([1-6])[^>]*>(.*?)</h[1-6]>"

        for match in re.finditer(pattern, html, re.IGNORECASE | re.DOTALL):
            level = int(match.group(1))
            content = match.group(2)
            text = re.sub(r"<[^>]+>", "", content).strip()
            if text:
                headings.append((level, text, match.group(0)))

        return headings

    def _generate_heading_id(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[-\s]+", "-", text)
        text = text.strip("-")
        return text

    def _add_ids_to_headings(self, html: str) -> str:
        headings = self._extract_headings(html)
        used_ids = set()

        for level, text, original_tag in headings:
            base_id = self._generate_heading_id(text)
            heading_id = base_id
            counter = 1

            while heading_id in used_ids:
                heading_id = f"{base_id}-{counter}"
                counter += 1

            used_ids.add(heading_id)

            if "id=" not in original_tag.lower():
                new_tag = re.sub(
                    r"(<h[1-6])", rf'\1 id="{heading_id}"', original_tag, count=1
                )
                html = html.replace(original_tag, new_tag, 1)

        return html

    def generate_table_of_contents(self, html: str) -> str:
        pattern = r"<h([1-6])[^>]*(?:id=\"([^\"]+)\")?[^>]*>(.*?)</h[1-6]>"
        headings = []

        for match in re.finditer(pattern, html, re.IGNORECASE | re.DOTALL):
            level = int(match.group(1))
            if level > 2:
                continue
            heading_id = match.group(2) or self._generate_heading_id(
                re.sub(r"<[^>]+>", "", match.group(3)).strip()
            )
            text = re.sub(r"<[^>]+>", "", match.group(3)).strip()
            if text:
                headings.append((level, text, heading_id))

        if not headings:
            return ""

        toc_items = []
        for level, text, heading_id in headings:
            indent_class = f"toc-level-{level}"
            toc_items.append(
                f'<li class="{indent_class} no-style">'
                f'<a href="#{heading_id}">{text}</a>'
                f"</li>"
            )

        toc_html = f"""<div class="toc">
        <h2 class="toc-heading">Tabla de Contenidos</h2>
        <ul class="toc-list">
{chr(10).join(toc_items)}
        </ul>
    </div>"""

        return toc_html

    def generate_cover_page(
        self,
        title: str,
        badge: str = "Propuesta técnica",
        date: str = None,
    ) -> str:
        if date is None:
            from datetime import datetime

            months = [
                "Enero",
                "Febrero",
                "Marzo",
                "Abril",
                "Mayo",
                "Junio",
                "Julio",
                "Agosto",
                "Septiembre",
                "Octubre",
                "Noviembre",
                "Diciembre",
            ]
            now = datetime.now()
            date = f"{months[now.month - 1]} {now.year}"

        cover_html = f"""<div class="header">
        <div class="header-content">
            <div>
                <h1>{title}</h1>
                <span class="badge">{badge}</span>
                <div class="header-date">{date}</div>
            </div>
        </div>
    </div>"""
        return cover_html

    def generate_pdf(
        self,
        body_content: str,
        title: str,
        css: Union[str, Dict[str, Dict[str, str]]],
        output_path: str,
        include_cover: bool = True,
        cover_badge: str = "Propuesta técnica",
        cover_date: str = None,
        include_toc: bool = True,
    ) -> None:
        body_content = self._add_ids_to_headings(body_content)

        if include_cover:
            cover_page = self.generate_cover_page(title, cover_badge, cover_date)
            body_content = cover_page + '\n<div class="content">\n' + body_content
        else:
            body_content = '<div class="content">\n' + body_content

        if include_toc:
            toc = self.generate_table_of_contents(body_content)
            if toc:
                body_content = body_content.replace(
                    '<div class="content">\n', '<div class="content">\n' + toc + "\n", 1
                )

        body_content = body_content + "\n</div>"

        html_content = self._generate_html(body_content, title, css)
        HTML(string=html_content).write_pdf(output_path)
