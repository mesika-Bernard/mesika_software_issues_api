from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.list_all_features, name='list_all_features'),
    path('create/', views.create_feature, name='create_feature'),
    path('<int:feature_id>/update/', views.update_feature, name='update_feature'),
    path('associate/', views.associate_feature_to_project, name='associate_feature'),
    path('project-features/<int:association_id>/update/', views.update_project_feature, name='update_project_feature'),
    path('project-features/<int:association_id>/remove/', views.remove_feature_from_project, name='remove_feature_from_project'),
    path('projects-features/<int:project_id>/features/', views.list_features, name='list_features'),
     path('projects-feature/', views.list_features_denormalized, name='list_features_with_project_info'),
]