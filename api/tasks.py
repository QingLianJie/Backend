from __future__ import absolute_import, unicode_literals
from celery import shared_task
from lib.heu import Crawler
from api.models import HEUAccountInfo, CourseInfo, CourseScore, ScoreQueryResult, TimetableQueryResult, RecentGradeCourse
from django.utils import timezone
from django.core.mail import send_mail
from qinglianjie.settings import EMAIL_FROM
import os, json, django


@shared_task
def query_scores(username:str, password:str):
    django.setup()
    ScoreQueryResult.objects.filter(heu_username=username).delete()
    try:
        crawler = Crawler()
        crawler.login(username, password)
        ScoreQueryResult.objects.get_or_create(heu_username=username,result=json.dumps(crawler.getScores()))[0].save()
    except Exception as e:
        ScoreQueryResult.objects.get_or_create(heu_username=username,fail=True)[0].save()
        print(e)
        return "Fail"
    return "Success"


@shared_task
def query_time_table(username:str, password:str, term:str):
    django.setup()
    TimetableQueryResult.objects.filter(heu_username=username).delete()
    try:
        crawler = Crawler()
        crawler.login(username, password)
        TimetableQueryResult.objects.get_or_create(heu_username=username,result=json.dumps(crawler.getTermTimetable(term)))[0].save()
    except Exception as e:
        TimetableQueryResult.objects.get_or_create(heu_username=username,fail=True)[0].save()
        print(e)
        return "Fail"
    return "Success"


@shared_task
def report_daily():
    django.setup()
    for info in HEUAccountInfo.objects.filter(report_daily=True, account_verify_status=True):
        print(HEUAccountInfo.heu_username)
        do_report.delay(info.heu_username, info.heu_password)
    return "Done"


@shared_task
def do_report(username:str, password:str):
    try:
        crawler = Crawler()
        crawler.login_one(username, password)
        crawler.report()
        return "Success"
    except Exception as e:
        return str(e)


@shared_task
def do_collect_scores(id):
    django.setup()
    info = HEUAccountInfo.objects.get(id=id)
    heu_username = info.heu_username
    try:
        crawler = Crawler()
        crawler.login(info.heu_username, info.heu_password)
        scores = crawler.getScores()
    except Exception as e:
        info.fail_last_time = True
        info.save()
        return "Fail"

    for record in scores:
        course_id = record[2]
        name = record[3]
        credit = record[5]
        total_time = record[6]
        assessment_method = record[7]
        course_kind = record[8]
        attributes = record[9]
        kind = record[10]
        general_category = record[11]

        if len(CourseInfo.objects.filter(course_id=course_id)) == 0:
            course = CourseInfo.objects.create(
                course_id=course_id,
                name=name,
                credit=credit,
                total_time=total_time,
                assessment_method=assessment_method,
                attributes=attributes,
                kind=kind,
                general_category=general_category,
            )
            course.save()

        course = CourseInfo.objects.get(course_id=course_id)

        if len(CourseScore.objects.filter(course=course, heu_username=heu_username)) == 0 \
                and record[4] != "---" \
                and course_kind == "正常考试":
            CourseScore.objects.create(
                course=course,
                heu_username=heu_username,
                score=record[4],
                term=record[1],
            ).save()

            if not info.fail_last_time:
                recent = RecentGradeCourse.objects.filter(course=course)
                flag = True
                if len(recent) >= 1:
                    delta = timezone.now() - recent[0].created
                    if delta.total_seconds() <= 60 * 60 * 24:
                        flag = False
                if flag:
                    RecentGradeCourse.objects.create(course=course).save()

            #出分时邮件发给我！
            if info.mail_when_grade:
                if not info.fail_last_time:
                    recent = RecentGradeCourse.objects.filter(course=course)
                    flag = False
                    if len(recent) >= 1:
                        delta = timezone.now() - recent[0].created
                        if delta.total_seconds() <= 60 * 60 * 24:
                            flag = True
                    else:
                        flag = True
                    print(info,course,record)
                    print(flag)
                    if flag:
                        print(info.user.email)
                        try:
                            send_mail(
                                '%s 出分提醒' % course.name,
                                '你的分数是 %s，欢迎到清廉街发表课程评论。\n' % str(record[4]) +
                                '如果你不想再收到出分提醒，可以在个人主页里关闭该功能。\n' +
                                'Qinglianjie',
                                EMAIL_FROM,
                                [info.user.email],
                            )
                        except Exception as e:
                            #邮件发送失败:( do nothing
                            pass

    if info.fail_last_time:
        info.fail_last_time = False
        info.save()

    return "Success"


@shared_task
def collect_scores():
    django.setup()
    for info in HEUAccountInfo.objects.filter(account_verify_status=True):
        do_collect_scores.delay(info.id)
    return "Success"


#统计学过某课程的人数
@shared_task
def count_courses():
    django.setup()
    for course in CourseInfo.objects.all():
        course.count = CourseScore.objects.filter(course=course).count()
        course.save()
    return "Success"
