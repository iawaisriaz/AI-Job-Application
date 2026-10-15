from django.urls import path
from . import views

urlpatterns = [
    path("", views.new_analysis, name="new_analysis"),

    path(
        "select-cv/<int:analysis_id>/",
        views.select_cv,
        name="select_cv"
    ),

    path(
        "loading/<int:analysis_id>/",
        views.analysis_loading,
        name="analysis_loading"
    ),

    path(
        "run/<int:analysis_id>/",
        views.run_analysis,
        name="run_analysis"
    ),

    path(
        "result/<int:analysis_id>/",
        views.result_analysis,
        name="result_analysis"
    ),
]