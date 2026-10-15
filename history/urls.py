
from django.urls import path
from . import views

urlpatterns = [
    path(
        "",
        views.history_list,
        name="history"
    ),

    path(
        "delete/<int:analysis_id>/",
        views.delete_analysis,
        name="delete_analysis"
    ),
]
