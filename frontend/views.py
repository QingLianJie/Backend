from django.shortcuts import render, redirect
from api.views import query_scores, query_time_table
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import datetime,timedelta
from api.models import HEUAccountInfo, CourseInfo, CourseScore, CourseComment
from frontend.models import Article
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from functools import wraps
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
        'posts': Article.objects.all(),
        'comments': [{
            "username": comment.user.username,
            "course_id": comment.course.course_id,
            "course_name": comment.course.name,
            "created": comment.created,
            "content": comment.content,
        } for comment in CourseComment.objects.all()[:5]],
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
            date = json_data['date']
            fail = False
            for record in json_data['data']:
                term = record[1]
                if scores_dict.get(term) is None:
                    scores_dict[term] = []
                scores_dict[term].append([len(scores_dict[term])+1,record[3],record[4],record[5],record[2]])
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
            date = json_data['date']
            fail = False
            temp = json_data['data']
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
        print(request.POST)
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
        return redirect(reverse("bind"))

    if request.method == "POST":
        print(request.POST)

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
        'report_page': True,
    })


def cache_on_user(timeout):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            return cache_page(timeout, key_prefix="_auth_%s_" % int(request.session["_auth_user_id"])
            if not (request.session.get("_auth_user_id") is None) else "anonymous")(view_func)(request, *args, **kwargs)
        return _wrapped_view
    return decorator


#@cache_on_user(3600*12*12)
def courses(request):
    print("test")

    all_courses = None
    if "s" in request.GET:
        all_courses = CourseInfo.objects.filter(name__icontains=request.GET.get("s"))
    else:
        all_courses = CourseInfo.objects.all()

    all_courses = list(all_courses)
    #all_courses.sort(key=lambda course:CourseScore.objects.filter(course=course).count(), reverse=True)

    paginator = Paginator(
        [[course.name, course.course_id, course.count]
            for course in all_courses],
        20,
    )
    print(paginator)

    page_num = request.GET.get('page')
    if page_num is None:
        page_num = 1
    elif type(page_num) is str:
        page_num = int(page_num)


    list_page = []
    for i in range(-5,6):
        if i+page_num>=1 and i+page_num<=paginator.num_pages:
            list_page.append(i+page_num)

    learned = None
    if not(request.session.get('_auth_user_id') is None):
        user_id = request.session["_auth_user_id"]
        user_info = HEUAccountInfo.objects.get(user=User.objects.get(id=user_id))
        heu_username = user_info.heu_username
        learned = [record.course for record in CourseScore.objects.filter(heu_username=heu_username)]
        for course in learned:
            course.num = course.count

    return render(request, "courses.html", {
        'courses_page': True,
        'page': paginator.page(page_num),
        'list_page': list_page,
        'pre': page_num-6 >= 1,
        'next': page_num+6 <= paginator.num_pages,
        's': request.GET.get('s'),
        'username': get_username(request),
        'login': not (request.session.get('_auth_user_id') is None),
        'learned': learned,
    })


def course(request, course_id):
    course = CourseInfo.objects.get(course_id=course_id)
    heu_username = None
    if not(request.session.get('_auth_user_id') is None):
        user_id = request.session["_auth_user_id"]
        user_info = HEUAccountInfo.objects.get(user=User.objects.get(id=user_id))
        heu_username = user_info.heu_username
    return render(request, "course.html", {
        "course_id": course_id,
        "course": course,
        "count": CourseScore.objects.filter(course=course).count(),
        'username': get_username(request),
        'login': not (request.session.get('_auth_user_id') is None),
        'comments': [{
            "username": comment.user.username,
            "course_id": comment.course.course_id,
            "course_name": comment.course.name,
            "created": comment.created,
            "content": comment.content,
         } for comment in CourseComment.objects.filter(course=course)],
        "score": CourseScore.objects.filter(course=course,heu_username=heu_username)[0].score if
            not(heu_username is None) and
            CourseScore.objects.filter(course=course,heu_username=heu_username).count()!=0 else None,
    })
