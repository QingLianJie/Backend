from django.urls import path

from . import views

urlpatterns = [
    path('scores', views.scores, name="scores"),
    path('index', views.index, name="index"),
    path('timetable', views.timetable, name="timetable"),
    path('bind', views.bind, name="bind"),
    path('', views.index, name="home"),
]