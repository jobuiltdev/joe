from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    # Project case studies. Real URLs, server-rendered, so they survive a
    # refresh and a cold share with no JavaScript involved.
    path("work/<slug:slug>/", views.project_detail, name="project_detail"),
    # There is no work index of its own; the deck on the home page is it.
    path("work/", RedirectView.as_view(url="/#work", permanent=False), name="work"),
    # The CV. Only the download is a route: viewing it goes straight to the
    # static file, and this exists so the response can carry the header that
    # actually makes a browser save it.
    path("cv/", views.cv_download, name="cv_download"),
    # The site used to be four pages. Keep the old paths working; they point
    # at the matching section of the one-pager.
    path("about/", RedirectView.as_view(url="/#about", permanent=True), name="about"),
    path("projects/", RedirectView.as_view(url="/#work", permanent=True), name="projects"),
    path("contact/", RedirectView.as_view(url="/#contact", permanent=True), name="contact"),
]
