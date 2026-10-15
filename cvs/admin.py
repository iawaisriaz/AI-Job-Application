from django.contrib import admin

from .models import CV


@admin.register(CV)
class CVAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "user",
        "uploaded_at",
    )

    search_fields = (
        "name",
        "user__username",
        "user__email",
    )

    list_filter = (
        "uploaded_at",
    )