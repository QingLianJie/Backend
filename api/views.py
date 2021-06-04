from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from api.models import HEUAccountInfo, CourseScore, CourseInfo, CourseComment
from api import tasks
from django_redis import get_redis_connection
from qinglianjie.settings import QUERY_INTERVAL
from api.tasks import *
from django.views.generic import View
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from qinglianjie.settings import COURSE_COMMENT_INTERVAL
from django.http import QueryDict
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
    user_info.first_time_collect_scores = True
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
    username = user_info.heu_username
    password = user_info.heu_password
    try:
        print(type(ScoreQueryResult.objects.get(heu_username=username).result))
        res = ScoreQueryResult.objects.get(heu_username=username)
        date = res.created
        data = json.loads(res.result)
    except Exception as e:
        print(e)
        return JsonResponse({"status": "FAILURE"})
    return JsonResponse({
        'status': 'SUCCESS',
        'date': date,
        'data': data,
    })


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
    else:
        return JsonResponse({"status": "FAILURE", "message": "Query interval too short!"})
    return JsonResponse({"status": "SUCCESS"})


@login_required
@heu_account_verify_required
def query_time_table(request):
    user_id = request.session["_auth_user_id"]
    user_info = HEUAccountInfo.objects.get(user=User.objects.get(id=user_id))
    username = user_info.heu_username
    password = user_info.heu_password
    try:
        print(type(TimetableQueryResult.objects.get(heu_username=username).result))
        res = TimetableQueryResult.objects.get(heu_username=username)
        date = res.created
        data = json.loads(res.result)
    except Exception as e:
        print(e)
        return JsonResponse({"status": "FAILURE"})
    return JsonResponse({
        'status': 'SUCCESS',
        'date': date,
        'data': data,
    })


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
    else:
        return JsonResponse({"status": "FAILURE", "message": "Query interval too short!"})
    return JsonResponse({"status": "SUCCESS"})


@login_required
@heu_account_verify_required
def test_auto_report(request):
    user_id = request.session["_auth_user_id"]
    user_info = HEUAccountInfo.objects.get(user=User.objects.get(id=user_id))
    username = user_info.heu_username
    password = user_info.heu_password
    tasks.report_daily.delay()
    return JsonResponse({"status": "SUCCESS"})


def test_collect_scores(request):
    collect_scores.delay()
    return HttpResponse("ok")


def query_course_scores(request):
    course_id = request.GET.get("course_id")
    if course_id is None:
        return JsonResponse({"status": "FAILURE", "message": "You must provide course_id !"})
    term = request.GET.get("term")
    course = CourseInfo.objects.get(course_id=course_id)
    print(course, term)
    res = []
    if term is None:
        res = [record.score for record in CourseScore.objects.filter(course=course)]
    else:
        res = [record.score for record in CourseScore.objects.filter(
            course=course,
            term=term,
        )]
    return JsonResponse({
        "status": "SUCCESS",
        "data": res,
    })


def query_course_info(request):
    res = []
    for course in CourseInfo.objects.all():
        res.append([
            course.course_id,
            course.name,
            course.credit,
            course.total_time,
            course.assessment_method,
            course.attributes,
            course.kind,
            course.general_category,
        ])

    return JsonResponse({
        "status": "SUCCESS",
        "data": res,
    })


@login_required
def query_my_comment(request):
    user_id = request.session["_auth_user_id"]
    user = User.objects.get(id=user_id)
    return JsonResponse({
        "data": [{
            "id": comment.id,
            "username": comment.user.username,
            "course_id": comment.course.course_id,
            "course_name": comment.course.name,
            "created": comment.created,
            "content": comment.content,
            "anonymous": comment.anonymous,
        } for comment in CourseComment.objects.filter(user=user)],
    })


@login_required
def remove_my_comment(request):
    user_id = request.session["_auth_user_id"]
    user = User.objects.get(id=user_id)

    # DELETE = QueryDict(request.body)
    comment_id = int(request.POST.get("id"))
    comment = CourseComment.objects.get(id=comment_id)

    if comment.user != user: #删除别人的评论？
        return JsonResponse({
            "status": 401,
            "message": "不是你的评论，你想做什么？",
        }, status=401)

    comment.delete()
    return JsonResponse({
        "status": 204,
        "message": "删除成功",
    }, status=204)


def recent_grade_course(request):
    return JsonResponse({
        "status": "SUCCESS",
        "data": [{
            "course_name": record.course.name,
            "course_id": record.course.course_id,
            "time": record.created,
        } for record in RecentGradeCourse.objects.all()],
    })


class CourseCommentView(View):
    def get(self, request):
        course_id = request.GET.get("course_id")

        if course_id is None:
            return JsonResponse({
                "data": [{
                    "id": comment.id,
                    "username": comment.user.username if not comment.anonymous else "匿名",
                    "course_id": comment.course.course_id,
                    "course_name": comment.course.name,
                    "created": comment.created,
                    "content": comment.content,
                    "anonymous": comment.anonymous,
                } for comment in CourseComment.objects.all()],
            })

        try:
            course = CourseInfo.objects.get(course_id=course_id)
        except Exception as e:
            return JsonResponse({
                "status": 404,
                "message": "无效课程号",
            }, status=404)

        return JsonResponse({
            "data": [{
                "id": comment.id,
                "username": comment.user.username if not comment.anonymous else "匿名",
                "course_id": comment.course.course_id,
                "course_name": comment.course.name,
                "created": comment.created,
                "content": comment.content,
                "anonymous": comment.anonymous,
            } for comment in CourseComment.objects.filter(course=CourseInfo.objects.get(course_id=course_id))],
        })

    def post(self, request):
        user_id = request.session["_auth_user_id"]
        if user_id is None:
            return JsonResponse({
                "status": 401,
                "message": "请先登录",
            }, status=401)
        user = User.objects.get(id=user_id)

        # print(request.FORM)
        # print(request.POST)
        # print(request.GET)
        course_id = request.POST.get("course_id")
        # print(course_id)
        try:
            course = CourseInfo.objects.get(course_id=course_id)
        except Exception as e:
            print(e)
            return JsonResponse({
                "status": 404,
                "message": "无效课程号",
            }, status=404)

        content = request.POST.get("content")
        if content is None or len(content) == 0:
            return JsonResponse({
                "status": 400,
                "message": "评论内容不能为空",
            }, status=400)
        if len(content) > 100:
            return JsonResponse({
                "status": 400,
                "message": "评论字数限制在100字以内",
            }, status=400)

        if CourseComment.objects.filter(user=user).count() != 0:
            last_comment_time = CourseComment.objects.filter(user=user).first().created
            delta = timezone.now() - last_comment_time
            print(last_comment_time, delta.total_seconds())
            if delta.total_seconds() <= COURSE_COMMENT_INTERVAL:
                return JsonResponse({
                    "status": 400,
                    "message": "评论间隔限制为 %s 秒" % str(COURSE_COMMENT_INTERVAL),
                }, status=400)

        anonymous = bool(request.POST.get("anonymous") == "true")
        CourseComment.objects.create(
            user=user,
            content=content,
            course=course,
            anonymous=anonymous,
        ).save()

        return JsonResponse({
            "status": 201,
            "message": "评论成功",
        }, status=201)


def course_count(request):
    tasks.count_courses.delay()
    return HttpResponse("ok")

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
