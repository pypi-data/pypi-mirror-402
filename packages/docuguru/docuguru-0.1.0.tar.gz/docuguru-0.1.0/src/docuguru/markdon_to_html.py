import markdown
from markdown.extensions.tables import TableExtension


class MarkdownToHTML:
    def __init__(self):
        self.md = markdown.Markdown(
            extensions=["tables", "fenced_code", "nl2br", "toc"]
        )

    def convert(self, markdown_text: str) -> str:
        html = self.md.convert(markdown_text)
        self.md.reset()
        return html

    def convert_file(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()
        return self.convert(markdown_content)
