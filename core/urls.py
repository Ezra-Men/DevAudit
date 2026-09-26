from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    # 1. Main Single-Scroll Page (Search bar, active audit card, methodology & roadmap)
    path("", views.index_view, name="index"),

    # 2. Form submission endpoint for processing GitHub analysis
    path("audit/", views.audit_user_view, name="audit"),

    # 3. Dynamic SVG badge endpoint for README embeds (e.g., /badge/Ezra-Men.svg)
    path("badge/<str:username>.svg", views.badge_view, name="badge"),

    # 4. Peer review submission endpoint (supports HTMX partial updates)
    path("review/<str:username>/", views.add_review_view, name="add_review"),
]