from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.list_issues, name='list_issues'),          
    path('create/', views.create_issue, name='create_issue'),
    path('<int:issue_id>/', views.get_issue, name='get_issue'),
    path('<int:issue_id>/update/', views.update_issue, name='update_issue'),
    path('<int:issue_id>/delete/', views.delete_issue, name='delete_issue'),
]
