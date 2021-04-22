from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from api.models import HEUAccountInfo
from api import tasks
from django_redis import get_redis_connection
from qinglianjie.settings import QUERY_INTERVAL
import lib.heu, time, json


# def index(request):
#     #res = tasks.add.delay(1, 3)
#     # 任务逻辑
#     #return JsonResponse({'status': 'successful', 'task_id': res.task_id})
#     #print(request.session.keys())
#     #print(request.session["_auth_user_id"])
#     return HttpResponse("test")


# @login_required
# def get_id(request):
#     return HttpResponse(str(request.session["_auth_user_id"]))
#
#
# @login_required
# def update_user_info(request):
#     user_id = request.session["_auth_user_id"]
#     user_info = UserInfo.objects.get_or_create(user=User.objects.get(id=user_id))[0]
#     if not request.GET.get("heu_username") is None:
#         user_info.heu_username = request.GET["heu_username"]
#     if not request.GET.get("heu_password") is None:
#         user_info.heu_password = request.GET["heu_password"]
#     user_info.save()
#     return HttpResponse("ok")
#
#
# @login_required
# def verify_heu_account(request):
#     user_id = request.session["_auth_user_id"]
#     try:
#         user_info = UserInfo.objects.get(user=User.objects.get(id=user_id))
#         username = user_info.heu_username
#         password = user_info.heu_password
#         if not lib.heu.verify(username, password):
#             raise Exception()
#     except Exception as e:
#         print(e)
#         return HttpResponse("no")
#     return HttpResponse("ok")

def heu_account_verify_required(func):
    def wrapper(request, *args, **kwargs):
        user_id = request.session["_auth_user_id"]
        flag = True
        try:
            flag = HEUAccountInfo.objects.get(user=User.objects.get(id=user_id)).account_verify_status
        except Exception as e:
            flag = False
        print(flag)
        if not flag:
            return JsonResponse({"status": "FAILURE", "message": "You need to configure your HEU accounts first!"})
        return func(request, *args, **kwargs)

    return wrapper


@login_required
def update_heu_accounts(request):
    user_id = request.session["_auth_user_id"]
    user_info = HEUAccountInfo.objects.get_or_create(user=User.objects.get(id=user_id))[0]
    #TODO change request method from GET to POST
    username = request.GET.get('heu_username')
    password = request.GET.get('heu_password')
    if username is None or password is None:
        return JsonResponse({"status": "FAILURE", "message": "Username and password can't not be empty!"})
    if not lib.heu.verify(username, password):
        return JsonResponse({"status": "FAILURE", "message": "HEU account failed to login!"})
    user_info.heu_username = username
    user_info.heu_password = password
    user_info.account_verify_status = True
    user_info.save()
    return JsonResponse({"status": "SUCCESS"})


@login_required
def remove_heu_accounts(request):
    user_id = request.session["_auth_user_id"]
    user_info = HEUAccountInfo.objects.get_or_create(user=User.objects.get(id=user_id))[0]
    # TODO change request method from GET to POST
    user_info.heu_username = ""
    user_info.heu_password = ""
    user_info.account_verify_status = False
    user_info.save()
    return JsonResponse({"status": "SUCCESS"})


@login_required
@heu_account_verify_required
def query_scores(request):
    user_id = request.session["_auth_user_id"]
    user_info = HEUAccountInfo.objects.get(user=User.objects.get(id=user_id))
    try:
        conn = get_redis_connection('default')
        # res = json.loads(conn.get("celery-task-meta-" + request.session["refresh_scores_task_id"]))
        res = json.loads(conn.get("celery-task-meta-"+str(conn.get(user_id+"refresh_scores_task_id"), encoding="utf-8")))
    except Exception as e:
        print(e)
        return JsonResponse({"status": "FAILURE"})
    return JsonResponse(res)


@login_required
@heu_account_verify_required
def refresh_scores(request):
    if request.session.get("last_refresh_scores_time") is None or (
            time.time() - request.session["last_refresh_scores_time"]) > QUERY_INTERVAL:
        user_id = request.session["_auth_user_id"]
        user_info = HEUAccountInfo.objects.get(user=User.objects.get(id=user_id))
        username = user_info.heu_username
        password = user_info.heu_password
        res = tasks.query_scores.delay(username, password)
        print(username, password)
        request.session["last_refresh_scores_time"] = time.time()
        conn = get_redis_connection('default')
        # last_task_id = request.session.get("refresh_scores_task_id")
        last_task_id = None
        try:
            last_task_id = str(conn.get(user_id+"refresh_scores_task_id") , encoding="utf-8")
        except:
            pass
        print(last_task_id)
        if not (last_task_id is None):
            remove_last_task_id(last_task_id)
        # request.session["refresh_scores_task_id"] = res.task_id
        conn.set(user_id+"refresh_scores_task_id", res.task_id)
    else:
        return JsonResponse({"status": "FAILURE", "message": "Query interval too short!"})
    return JsonResponse({"status": "SUCCESS"})


@login_required
@heu_account_verify_required
def query_time_table(request):
    user_id = request.session["_auth_user_id"]
    user_info = HEUAccountInfo.objects.get(user=User.objects.get(id=user_id))
    try:
        conn = get_redis_connection('default')
        # res = json.loads(conn.get("celery-task-meta-" + request.session["refresh_time_table_task_id"]))
        res = json.loads(conn.get("celery-task-meta-"+str(conn.get(user_id+"refresh_time_table_task_id"), encoding="utf-8")))
        print(res)
    except Exception as e:
        return JsonResponse({"status": "FAILURE"})
    return JsonResponse(res)


@login_required
@heu_account_verify_required
def refresh_time_table(request):
    #request.content_params
    if request.session.get("last_refresh_time_table_time") is None or (
            time.time() - request.session['last_refresh_time_table_time']) > QUERY_INTERVAL:
        term = request.GET.get("term")
        #TODO change request method from GET to POST
        if term is None:
            return JsonResponse({"status": "FAILURE", "message": "You must provide argv term!"})
        print(term)
        user_id = request.session["_auth_user_id"]
        user_info = HEUAccountInfo.objects.get(user=User.objects.get(id=user_id))
        username = user_info.heu_username
        password = user_info.heu_password
        res = tasks.query_time_table.delay(username, password, term)
        request.session["last_refresh_time_table_time"] = time.time()
        conn = get_redis_connection('default')
        # last_task_id = request.session.get("refresh_time_table_task_id")
        last_task_id = None
        try:
            last_task_id = str(conn.get(user_id + "refresh_time_table_task_id"), encoding="utf-8")
        except:
            pass
        if not (last_task_id is None):
            remove_last_task_id(last_task_id)
        # request.session["refresh_time_table_task_id"] = res.task_id
        conn.set(user_id + "refresh_time_table_task_id", res.task_id)
        # print(res.task_id)
    else:
        return JsonResponse({"status": "FAILURE", "message": "Query interval too short!"})
    return JsonResponse({"status": "SUCCESS"})


# Redis
def remove_last_task_id(task_id):
    conn = get_redis_connection('default')
    conn.delete("celery-task-meta-"+task_id)


def set_key(key, value):
    conn = get_redis_connection('default')
    conn.set(key, value)


def get_key(key):
    conn = get_redis_connection('default')
    return conn.get(key)
