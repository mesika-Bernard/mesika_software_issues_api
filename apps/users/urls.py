from django.urls import path
from . import views

urlpatterns = [
    path('', views.users, name='users'),
    path('<int:user_id>/', views.user_detail, name='user_detail'),
    path('update/<int:user_id>/', views.update_user, name='update_user'),
]