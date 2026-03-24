from django.shortcuts import render
from django.http import HttpResponse
from .service import MDPDF
import tempfile
from pathlib import Path


# Create your views here.
def home(request):
    return render(request, "home.html")


def md_to_pdf(request):
    if request.method == "POST":
        md_text = request.POST.get("markdown")
        theme = request.POST.get("theme", "light")
        filename = request.POST.get("filename", "output")

        # Create temp files
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)

            md_file = tmp_path / "input.md"
            html_file = tmp_path / "output.html"
            pdf_file = tmp_path / f"{filename}.pdf"

            # Save markdown text
            md_file.write_text(md_text, encoding="utf-8")

            # Convert using your class
            converter = MDPDF(theme=theme)
            html_str = converter.md_to_html(md_file, theme=theme)

            converter.html_to_pdf_playwright(
                html_str, pdf_file, html_file, converter.THEMES[theme]["bg"]
            )

            # Return PDF
            with open(pdf_file, "rb") as f:
                response = HttpResponse(f.read(), content_type="application/pdf")
                response["Content-Disposition"] = (
                    f'attachment; filename="{filename}.pdf"'
                )
                return response

    return render(request, "mdtopdf.html")
