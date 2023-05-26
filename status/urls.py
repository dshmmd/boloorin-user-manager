from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r'^$', views.home, name='home'),
    re_path(r'^login/', views.login_view, name='login_view'),
    re_path(r'^logout/', views.logout_view, name='logout_view'),
    re_path(r'^dashboard/', views.dashboard, name='dashboard'),
    re_path(r'^check-status/$', views.check_status, name='check_status'),
    re_path(r'^check-status/add-inbound/', views.add_inbound, name='add_inbound'),
    re_path(r'^check-status/renew-inbound/', views.renew_inbound, name='renew_inbound'),
    re_path(r'^check-status/delete-inbound/', views.delete_inbound, name='delete_inbound'),
]
