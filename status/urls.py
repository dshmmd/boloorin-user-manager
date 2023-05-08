from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^$', views.home, name='home'),
    re_path(r'^login/', views.login_view, name='login_view'),
    re_path(r'^logout/', views.logout_view, name='logout_view'),
    re_path(r'^check_status/', views.check_status, name='check_status'),
]
