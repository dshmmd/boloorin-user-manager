from django.contrib.auth.models import User
from django.db import models


class Server(models.Model):
    name = models.CharField(max_length=20, primary_key=True)
    host = models.URLField(max_length=200)
    username = models.CharField(max_length=20)
    password = models.CharField(max_length=32)
    last_disabled_users = models.TextField(default='', blank=True)
    set_cookie = models.TextField(default='', blank=True)
    set_cookie_expires = models.DateTimeField(default=None, blank=True, null=True)
    owner = models.ForeignKey(User,  on_delete=models.CASCADE, default=0, related_name='server_owner')
    viewer = models.ForeignKey(User, on_delete=models.PROTECT, default=None, null=True, related_name='server_viewer')
    sort_number = models.IntegerField(default=0)
    default_x_ui = models.BooleanField(default=True, null=True)

    def __str__(self):
        return self.name
