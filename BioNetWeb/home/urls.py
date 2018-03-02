from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('about', views.about, name='about'),
    url(r'^login/$', auth_views.login, name='login'),
    url(r'^signup/$', views.signup, name='signup'),
    url(r'^logout/$', auth_views.logout, {'next_page': settings.LOGOUT_REDIRECT_URL}, name='logout'),
    path('feedback', views.feedback, name='feedback'),
    path('resources', views.resources, name='resources'),
    path('user', views.user, name='user'),
    path('admin', views.admin, name='admin'),
]
