from django.shortcuts import render, redirect
from api.views import query_scores, query_time_table
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import datetime,timedelta
from api.models import HEUAccountInfo
import json, lib


def get_username(request):
    user_id = request.session.get('_auth_user_id')
    if user_id is None:
        return None
    return User.objects.get(id=user_id).username


def format_date(string):
    return str(datetime.strptime(string, "%Y-%m-%dT%H:%M:%S") + timedelta(hours=8))


def index(request):
    #return render(request, "account/_login.html")

    return render(request, 'index.html',{
        'login': not (request.session.get('_auth_user_id') is None),
        'index_page': True,
        'username': get_username(request),
    })


@login_required
def scores(request):
    result = query_scores(request)
    scores_dict = {}
    fail = True
    date = None
    scores_list = []
    if type(result) is JsonResponse:
        json_data = json.loads(result.content)
        if json_data['status'] == 'SUCCESS':
            date = json_data['date_done']
            fail = False
            for record in json_data['result']:
                term = record[1]
                if scores_dict.get(term) is None:
                    scores_dict[term] = []
                scores_dict[term].append([len(scores_dict[term])+1,record[3],record[4],record[5]])
            scores_list = list(scores_dict.items())
            scores_list.reverse()
    return render(request, 'scores.html', {
        'fail': fail,
        'scores': scores_list,
        'date': format_date(date.split('.')[0]) if not (date is None) else None,
        'username': get_username(request),
        'login': True,
        'scores_page': True,
    })


@login_required
def timetable(request):
    result = query_time_table(request)
    fail = True
    date = None
    timetable_list = None
    head = (
        ("第一大节", "8:00-9:35"),
        ("第二大节", "9:55-12:20"),
        ("第三大节", "13:30-15:05"),
        ("第四大节", "15:25-17:50"),
        ("第五大节", "18:30-20:55"),
        ("last", ""),
    )

    if type(result) is JsonResponse:
        json_data = json.loads(result.content)
        if json_data['status'] == 'SUCCESS':
            date = json_data['date_done']
            fail = False
            temp = json_data['result']
            timetable_list = []
            for i in range(len(temp)):
                t = []
                for j in range(len(temp[i])):
                    print(head[j],temp[i][j])
                    t.append([head[j],temp[i][j]])
                print(t)
                timetable_list.append([i+1,t])

    print(timetable_list)

    return render(request, 'timetable.html', {
        'fail': fail,
        'timetable': timetable_list,
        'date': format_date(date.split('.')[0]) if not (date is None) else None,
        'username': get_username(request),
        'login': True,
        'timetable_page': True,
    })


@login_required
def bind(request):
    user_id = request.session["_auth_user_id"]
    user_info = HEUAccountInfo.objects.get_or_create(user=User.objects.get(id=user_id))[0]
    username = user_info.heu_username
    # TODO change request method from GET to POST
    if request.method == "POST":
        user_id = request.session["_auth_user_id"]
        user_info = HEUAccountInfo.objects.get_or_create(user=User.objects.get(id=user_id))[0]
        # TODO change request method from GET to POST
        if request.POST.get("action") == "bind":
            username = request.POST.get('heu_username')
            password = request.POST.get('heu_password')
            if username is None or password is None:
                return render(request, "bind.html", {
                    "bind": user_info.account_verify_status,
                    "heu_username": username,
                    "error": "账号密码不能为空！",
                    'username': get_username(request),
                     'login': True,
                })
            if not lib.heu.verify(username, password):
                return render(request, "bind.html", {
                    "bind": user_info.account_verify_status,
                    "heu_username": username,
                    "error": "HEU账号验证失败！",
                    'username': get_username(request),
                    'login': True,
                })
            user_info.heu_username = username
            user_info.heu_password = password
            user_info.account_verify_status = True
            user_info.save()
            return render(request, "bind.html", {
                "bind": user_info.account_verify_status,
                "heu_username": username,
                "success_bind": True,
                'username': get_username(request),
                'login': True,
            })
        elif request.POST.get("action") == "remove":
            user_info.heu_username = ""
            user_info.heu_password = ""
            user_info.account_verify_status = False
            user_info.save()
            return render(request, "bind.html", {
                "bind": user_info.account_verify_status,
                "heu_username": username,
                "success_remove": True,
                'username': get_username(request),
                'login': True,
            })

    return render(request, "bind.html", {
        "bind": user_info.account_verify_status,
        "heu_username": username,
        'username': get_username(request),
        'login': True,
    })


@login_required
def report(request):
    user_id = request.session["_auth_user_id"]
    user_info = HEUAccountInfo.objects.get_or_create(user=User.objects.get(id=user_id))[0]
    username = user_info.heu_username
    success = False
    error = False

    if not user_info.account_verify_status:
        return redirect(reverse("frontend:bind"))

    if request.method == "POST":
        if request.POST.get("action") == "on":
            user_info.report_daily = True
            user_info.save()
            success = True

        if request.POST.get("action") == "off":
            user_info.report_daily = False
            user_info.save()
            error = True

    return render(request, "report.html", {
        "report": user_info.report_daily,
        "heu_username": username,
        'username': get_username(request),
        'login': True,
        'success': success,
        'error': error,
    })