import markdown
from playwright.sync_api import sync_playwright
import re
from pathlib import Path


class MDPDF:
    def __init__(self, theme: str = "light", html_file: bool = False):
        self.theme = theme
        self.html_file = html_file
        # ── Themes ─────────────────────────────────────────────────────────────────────
        self.THEMES = {
            "light": {
                "mermaid_theme": "default",
                "bg": "#ffffff",
                "css": """
            body {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 15px; line-height: 1.7;
            color: #1a1a2e; background: #ffffff;
            max-width: 900px; margin: 40px auto; padding: 0 28px;
            }
            h1, h2, h3, h4 { color: #16213e; font-weight: 700; margin-top: 1.4em; }
            h1 { font-size: 2em;   border-bottom: 3px solid #0f3460; padding-bottom: 6px; }
            h2 { font-size: 1.5em; border-bottom: 1px solid #ddd;    padding-bottom: 4px; }
            h3 { font-size: 1.2em; }
            a  { color: #0f3460; }
            pre {
            background: #f4f4f8; border-left: 4px solid #0f3460;
            border-radius: 4px; padding: 14px 18px; overflow-x: auto; font-size: 13.5px;
            }
            code { background: #f0f0f5; padding: 2px 5px; border-radius: 3px; font-size: 13.5px; }
            pre code { background: none; padding: 0; }
            table { border-collapse: collapse; width: 100%; margin: 1em 0; }
            th { background: #0f3460; color: #fff; padding: 8px 12px; text-align: left; }
            td { border: 1px solid #ddd; padding: 8px 12px; }
            tr:nth-child(even) td { background: #f9f9fc; }
            blockquote {
            border-left: 4px solid #0f3460; background: #f0f4ff;
            margin: 1em 0; padding: 10px 16px; border-radius: 0 4px 4px 0;
            }
            .mermaid {
            background: #fafafa; border: 1px solid #e0e0e0;
            border-radius: 6px; padding: 20px; margin: 1.5em 0; text-align: center;
            }
            @media print { body { margin: 0; } pre { white-space: pre-wrap; } }
        """,
            },
            "dark": {
                "mermaid_theme": "dark",
                "bg": "#1e1e2e",
                "css": """
            /* Fill every edge of the PDF page with dark colour */
            html { background: #1e1e2e; }

            body {
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 15px; line-height: 1.7;
            color: #cdd6f4; background: #1e1e2e;
            max-width: 900px; margin: 0 auto; padding: 40px 28px;
            min-height: 100vh; box-sizing: border-box;
            }
            h1, h2, h3, h4 { color: #cba6f7; font-weight: 700; margin-top: 1.4em; }
            h1 { font-size: 2em;   border-bottom: 3px solid #cba6f7; padding-bottom: 6px; }
            h2 { font-size: 1.5em; border-bottom: 1px solid #45475a; padding-bottom: 4px; }
            h3 { font-size: 1.2em; }
            a  { color: #89b4fa; }
            pre {
            background: #181825; border-left: 4px solid #cba6f7;
            border-radius: 4px; padding: 14px 18px; overflow-x: auto; font-size: 13.5px;
            }
            code { background: #181825; color: #f38ba8; padding: 2px 5px; border-radius: 3px; font-size: 13.5px; }
            pre code { background: none; color: #cdd6f4; padding: 0; }
            table { border-collapse: collapse; width: 100%; margin: 1em 0; }
            th { background: #313244; color: #cba6f7; padding: 8px 12px; text-align: left; }
            td { border: 1px solid #45475a; padding: 8px 12px; color: #cdd6f4; }
            tr:nth-child(even) td { background: #24273a; }
            blockquote {
            border-left: 4px solid #cba6f7; background: #24273a;
            margin: 1em 0; padding: 10px 16px; border-radius: 0 4px 4px 0; color: #a6adc8;
            }
            .mermaid {
            background: #181825; border: 1px solid #45475a;
            border-radius: 6px; padding: 20px; margin: 1.5em 0; text-align: center;
            }
            @media print {
            html, body { background: #1e1e2e !important; }
            pre { white-space: pre-wrap; }
            }
        """,
            },
        }

        self.HTML_TEMPLATE = """\
        <!DOCTYPE html>
        <html lang="en">
        <head>
        <meta charset="UTF-8">
        <title>{title}</title>
        <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
        <script>mermaid.initialize({{ startOnLoad: true, theme: '{mermaid_theme}' }});</script>
        <style>
        {css}
        </style>
        </head>
        <body>
        {body}
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const check = setInterval(() => {{
            const divs = document.querySelectorAll('.mermaid');
            const allDone = [...divs].every(d => d.querySelector('svg'));
            if (allDone || divs.length === 0) {{
                clearInterval(check);
                document.body.setAttribute('data-mermaid-done', 'true');
            }}
            }}, 100);
        }});
        </script>
        </body>
        </html>
        """

    # ── Mermaid pre-processing ─────────────────────────────────────────────────────
    def replace_mermaid_fences(self, md_text: str) -> str:
        pattern = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)
        return pattern.sub(
            lambda m: f'<div class="mermaid">\n{m.group(1).strip()}\n</div>', md_text
        )

    # ── Conversion ─────────────────────────────────────────────────────────────────
    def md_to_html(self, md_path: Path, theme: str = "light") -> str:
        raw = md_path.read_text(encoding="utf-8")
        raw = self.replace_mermaid_fences(raw)

        md = markdown.Markdown(
            extensions=["tables", "fenced_code", "codehilite", "toc", "attr_list"]
        )
        body_html = md.convert(raw)
        title = md_path.stem.replace("_", " ").replace("-", " ").title()
        t = self.THEMES[theme]
        return self.HTML_TEMPLATE.format(
            title=title,
            body=body_html,
            mermaid_theme=t["mermaid_theme"],
            css=t["css"],
        )

    def html_to_pdf_playwright(
        self, html_str: str, pdf_path: Path, html_path: Path, bg: str
    ) -> None:
        html_path = html_path.resolve()
        pdf_path = pdf_path.resolve()
        html_path.write_text(html_str, encoding="utf-8")

        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox"])
            page = browser.new_page()
            page.goto(html_path.as_uri(), wait_until="networkidle")

            try:
                page.wait_for_selector("body[data-mermaid-done='true']", timeout=15_000)
            except Exception:
                print("⚠️  Mermaid render timeout — exporting what's visible so far.")

            # Zero browser margins for dark theme (CSS body padding handles spacing)
            # Non-zero margins for light theme to keep the classic page look
            m = "0" if bg != "#ffffff" else "1.8cm"
            page.pdf(
                path=str(pdf_path),
                format="A4",
                margin={"top": m, "bottom": m, "left": m, "right": m},
                print_background=True,  # required for dark backgrounds to show
            )
            browser.close()
