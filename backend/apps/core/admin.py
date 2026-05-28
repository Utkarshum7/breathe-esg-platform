from django.contrib import admin
from .models import Organization, DataSource

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "id", "created_at")
    search_fields = ("name",)
    readonly_fields = ("id", "created_at", "updated_at")

@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ("name", "organization", "source_type", "created_at")
    list_filter = ("source_type", "organization")
    search_fields = ("name",)
    readonly_fields = ("id", "created_at", "updated_at")
