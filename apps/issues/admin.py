from django.contrib import admin
from .models import Issue

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "created_at", "updated_at")
    raw_id_fields = ("project",)  
