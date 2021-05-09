from __future__ import absolute_import, unicode_literals
from celery import shared_task
from lib.heu import Crawler
import os


@shared_task
def query_scores(username:str, password:str):
    crawler = Crawler()
    #print(username, password)
    crawler.login(username, password)
    return crawler.getScores()


@shared_task
def query_time_table(username:str, password:str, term:str):
    crawler = Crawler()
    crawler.login(username, password)
    return crawler.getTermTimetable(term)


@shared_task
def report_daily():
    import django
    django.setup()
    from api.models import HEUAccountInfo
    #print(HEUAccountInfo.objects.all())
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
        return "Ok"
    except Exception as e:
        return str(e)


@shared_task
def collect_scores():
    import django
    from api.models import HEUAccountInfo, CourseInfo, CourseScore
    django.setup()

    for info in HEUAccountInfo.objects.filter(account_verify_status=True):
        heu_username = info.heu_username
        scores = query_scores(info.heu_username, info.heu_password)
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
    return "Ok"