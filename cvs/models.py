from django.db import models
from django.contrib.auth.models import User


class CV(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="cvs"
    )

    name = models.CharField(
        max_length=150
    )

    file = models.FileField(
        upload_to="cvs/"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = "user_cv"

    def __str__(self):
        return self.name

    @property
    def file_extension(self):
        return self.file.name.split(".")[-1].upper()