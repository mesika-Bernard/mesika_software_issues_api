from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.list_projects, name='list_projects'),
    path('create/', views.create_project, name='create_project'),
    path('<int:project_id>/', views.get_project, name='get_project'),
    path('update/<int:project_id>/', views.update_project, name='update_project'),
    path('delete/<int:project_id>/', views.delete_project, name='delete_project'),
]