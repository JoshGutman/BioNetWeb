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
    path('example', views.example, name='example'),
    url(r'^example_download_project*$', views.example_download, name='example_download'),
    url(r'^example_bestfit_plot*$', views.example_bestfit, name='example_bestfit'),
    url(r'^example_generational_plot*$', views.example_generation, name='example_generation'),
    url(r'^bestfit_plot*$', views.bestfit_plot, name='bestfit_plot'),
    url(r'^generational_plot*$', views.generational_plot, name='generational_plot'),
    url(r'^fitval_plot*$', views.fitval_plot, name='fitval_plot'),
    url(r'^download_project*$', views.download_project, name='download_project'),
   # path('admin', views.admin, name='admin'),
]
