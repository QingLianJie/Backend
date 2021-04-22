from __future__ import absolute_import, unicode_literals
from celery import shared_task
from lib.heu import Crawler


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
