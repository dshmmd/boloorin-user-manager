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


class Inbound:
    inbounds = []

    def __init__(self, remark, inbound_id, port, protocol, settings, stream_settings, sniffing, remaining_status):
        self.inbound_id = inbound_id
        self.remark = remark
        self.port = port
        self.protocol = protocol
        self.settings = settings
        self.stream_settings = stream_settings
        self.sniffing = sniffing
        self.remaining_status = remaining_status
        self.inbounds.append(self)

    def __str__(self):
        return self.remark

    @classmethod
    def get_inbound_by_id(cls, inbound_id):
        return [inbound for inbound in cls.inbounds if inbound.inbound_id == inbound_id]


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

        servers_context = []
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
                for inbound in inbounds:
                    if not inbound["enable"]:
                        remark = inbound['remark']
                        ID = inbound['id']
                        port = inbound['port']
                        protocol = inbound['protocol']
                        settings = inbound['settings']
                        stream_settings = inbound['streamSettings']
                        sniffing = inbound['sniffing']

                        remaining_credit = calc_remaining_credit(inbound['expiryTime'])
                        remaining_traffic = calc_remaining_traffic(inbound['up'], inbound['down'], inbound['total'])

                        if round(remaining_traffic, 1) > 0:
                            status = f"{remark}({remaining_traffic} GB left)"
                        elif remaining_credit > 0:
                            status = f"{remark}({remaining_credit} days left)"
                        else:
                            status = f"{remark}(Nothing left)"

                        disabled_inbound = Inbound(remark, ID, port, protocol, settings, stream_settings, sniffing,
                                                   status)
                        users.append(disabled_inbound)

            except ConnectionError:
                users = "ERROR"

            servers_context.append({'name': server.name, 'owner': server.owner, 'expired_inbounds': users})

        context = {"request": request, 'servers_context': servers_context}
        return render(request, "status/status.html", context)

    else:
        return render(request, "status/status.html")


def calc_remaining_traffic(up, down, total):
    up = up / 2 ** 30
    down = down / 2 ** 30
    total = total / 2 ** 30
    return abs(round(total - up - down, 1))


def calc_remaining_credit(expiry_time):
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
