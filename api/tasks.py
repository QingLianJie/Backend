from __future__ import absolute_import, unicode_literals
from celery import shared_task
from lib.heu import Crawler
from api.models import HEUAccountInfo, CourseInfo, CourseScore, ScoreQueryResult, TimetableQueryResult
import os, json, django


@shared_task
def query_scores(username:str, password:str):
    django.setup()
    ScoreQueryResult.objects.filter(heu_username=username).delete()
    try:
        crawler = Crawler()
        crawler.login(username, password)
        ScoreQueryResult.objects.create(heu_username=username,result=json.dumps(crawler.getScores())).save()
    except Exception as e:
        ScoreQueryResult.objects.create(heu_username=username,fail=True).save()
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
        TimetableQueryResult.objects.create(heu_username=username,result=json.dumps(crawler.getTermTimetable(term))).save()
    except Exception as e:
        TimetableQueryResult.objects.create(heu_username=username,fail=True).save()
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
def collect_scores():
    django.setup()
    for info in HEUAccountInfo.objects.filter(account_verify_status=True):
        heu_username = info.heu_username
        heu_password = info.heu_password
        try:
            crawler = Crawler()
            crawler.login(info.heu_username, info.heu_password)
            scores = crawler.getScores()
        except Exception as e:
            continue

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
                    and record[4] != "---"\
                    and course_kind == "正常考试":
                CourseScore.objects.create(
                    course=course,
                    heu_username=heu_username,
                    score=record[4],
                    term=record[1],
                ).save()
    return "Success"


#统计学过某课程的人数
@shared_task
def count_courses():
    django.setup()
    for course in CourseInfo.objects.all():
        course.count = CourseScore.objects.filter(course=course).count()
        course.save()
    return "Success"
