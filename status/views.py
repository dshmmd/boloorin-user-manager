from django.shortcuts import render
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import redirect, HttpResponse
from django.contrib.auth.decorators import login_required
from .models import Server
import requests
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q
from operator import attrgetter


def home(request):
    return render(request, 'status/home.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('check_status')

    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('check_status')

    form = AuthenticationForm(request)
    context = {
        "form": form,
    }
    return render(request, "status/login.html", context)


@login_required(login_url='login_view')
def logout_view(request):
    logout(request)
    return redirect('login_view')


@login_required(login_url='login_view')
def check_status(request):
    if request.GET.get("start") == "true":
        if request.user.is_staff:
            servers = Server.objects.all()
        else:
            servers = Server.objects.filter(Q(owner=request.user) | Q(viewer=request.user))
        servers = sorted(servers, key=attrgetter('username', 'sort_number'))

        for server in servers:
            now = timezone.now()
            set_cookie = server.set_cookie
            set_cookie_expires = server.set_cookie_expires

            if not set_cookie or set_cookie_expires < now:
                try:
                    set_cookie = login_to_server(server.host, server.username, server.password)
                    set_cookie_expires = now + timedelta(days=25)
                    server.set_cookie = set_cookie
                    server.set_cookie_expires = set_cookie_expires
                    server.save()
                except ConnectionError:
                    server.last_disabled_users = f"Can't Login to Server {server}"
                    server.save()
                    continue

            try:
                inbounds = get_inbounds_list(server.host, set_cookie)
                users = []
                for i in inbounds:
                    remark = i['remark']
                    if not i["enable"]:
                        remaining_credit = get_remaining_credit(i['expiryTime'])
                        remaining_traffic = get_remaining_traffic(i['up'], i['down'], i['total'])
                        
                        if round(remaining_traffic, 1) != 0.0:
                            status = f"{remark}({remaining_traffic} GB left)"
                        elif remaining_credit > 0:
                            status = f"{remark}({remaining_credit} days left)"
                        elif remaining_credit == 0:
                            status = f"{remark}(Nothing left)"
                        else:
                            status = f"{remark}({-remaining_credit} days passed)"
                        users.append(status)

                server.last_disabled_users = ', '.join(users)
                server.save()
            except ConnectionError:
                server.last_disabled_users = f"Can't Get Inbounds of Server {server}"
                server.save()

            if not server.last_disabled_users:
                server.last_disabled_users = "All Users are Enable"
                server.save()

        for i in servers:
            print(i.name, ":", i.last_disabled_users)
        context = {"request": request, "servers": servers}
        return render(request, "status/status.html", context)

    else:
        return render(request, "status/status.html")


def get_remaining_traffic(up, down, total):
    up = up / 2 ** 30
    down = down / 2 ** 30
    total = total / 2 ** 30
    return abs(round(total - up - down, 1))


def get_remaining_credit(expiry_time):
    now = datetime.now()
    expiration = datetime.fromtimestamp(expiry_time / 1000)
    return (expiration - now).days


def get_inbounds_list(host, set_cookie):
    url = f"{host}/xui/inbound/list"

    payload = {}
    headers = {
        'Cookie': set_cookie
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
    except Exception:
        raise ConnectionError

    if response.status_code == 200 and response.json()["success"]:
        return response.json()["obj"]
    else:
        raise ConnectionError


def login_to_server(host, username, password):
    url = f"{host}/login"

    payload = f'username={username}&password={password}'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload)
    except Exception:
        raise ConnectionError

    if response.status_code == 200 and response.json()['success']:
        return response.headers.get("Set-Cookie")
    else:
        raise ConnectionError
