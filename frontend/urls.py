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
    path('courses', views.courses, name="courses"),
    path('course/<int:course_id>', views.course, name="course"),
    path('profile', views.profile, name="profile"),
    path('pingjiao', views.pingjiao, name="pingjiao"),

    url(r'mdeditor/', include('mdeditor.urls')),
]