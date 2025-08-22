from django.contrib import admin
from .models import Feature, ProjectFeature

@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name', 'description')

@admin.register(ProjectFeature)
class ProjectFeatureAdmin(admin.ModelAdmin):
    list_display = ('project', 'feature', 'status', 'priority', 'created_at')
    list_filter = ('status', 'priority')
    search_fields = ('project__name', 'feature__name', 'notes')