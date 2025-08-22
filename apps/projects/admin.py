from django.contrib import admin
from .models import Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}