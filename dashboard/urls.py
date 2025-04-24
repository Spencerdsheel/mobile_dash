from .dash_apps import dash_app
from django.urls import path, include
from django.contrib import admin
from . import views
#from dashboard import Dashboard

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('station/', views.station_view, name='station'),
    path('user/', views.user_view, name='user'),
    path('summary/', views.summary_view, name='summary'),
    path('login/', views.loginUser, name='login'),
    path('logout/', views.logoutUser, name='logout'),
]