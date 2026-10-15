from django.urls import path

from . import views


urlpatterns = [

    path("", views.cv_page, name="cv" ),

    path("upload/", views.upload_cv, name="upload_cv" ),

    path("download/<int:cv_id>/", views.download_cv, name="download_cv" ),

    path("delete/<int:cv_id>/", views.delete_cv, name="delete_cv" ),

]