from django.urls import path
from .views import (
    home,
    md_to_pdf,
)

urlpatterns = [
    path("", home),
    path("md-to-pdf/", md_to_pdf),
]
