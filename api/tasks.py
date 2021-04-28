from __future__ import absolute_import, unicode_literals
from celery import shared_task
from lib.heu import Crawler
import os

@shared_task
def query_scores(username:str, password:str):
    crawler = Crawler()
    print(username, password)
    crawler.login(username, password)
    return crawler.getScores()


@shared_task
def query_time_table(username:str, password:str, term:str):
    crawler = Crawler()
    crawler.login(username, password)
    return crawler.getTermTimetable(term)


@shared_task
def report_daily():
    #os.environ.setdefault("DJANGO_SETTINGS_MODULE", "qinglianjie.settings")
    import django
    django.setup()
    from api.models import HEUAccountInfo
    print(HEUAccountInfo.objects.all())
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