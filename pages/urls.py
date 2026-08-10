from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    # The site used to be four pages. Keep the old paths working — they point
    # at the matching section of the one-pager.
    path("about/", RedirectView.as_view(url="/#about", permanent=True), name="about"),
    path("projects/", RedirectView.as_view(url="/#work", permanent=True), name="projects"),
    path("contact/", RedirectView.as_view(url="/#contact", permanent=True), name="contact"),
]
