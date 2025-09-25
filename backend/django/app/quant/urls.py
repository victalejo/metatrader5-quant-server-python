from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.mt5_login_view, name='mt5_login'),
    path('logout/', views.mt5_logout_view, name='mt5_logout'),
]