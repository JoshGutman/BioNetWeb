from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about', views.about, name='about'),
    path('login', views.login, name='login'),
    path('feedback', views.feedback, name='feedback'),
    path('resources', views.resources, name='resources'),
    path('user', views.user, name='user'),
    path('admin', views.admin, name='admin'),
]
