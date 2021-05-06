from django.urls import path
from django.conf.urls import url
from django.urls import include

from . import views

urlpatterns = [
    path('scores', views.scores, name="scores"),
    path('index', views.index, name="index"),
    path('timetable', views.timetable, name="timetable"),
    path('bind', views.bind, name="bind"),
    path('report', views.report, name="report"),
    path('', views.index, name="home"),
    url(r'mdeditor/', include('mdeditor.urls')),
]