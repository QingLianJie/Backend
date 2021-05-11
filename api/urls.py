from django.urls import path

from . import views

urlpatterns = [
    path('query/scores', views.query_scores, name="query_scores"),
    path('refresh/scores', views.refresh_scores, name="refresh_scores"),
    path('query/timetable', views.query_time_table, name="query_time_table"),
    path('refresh/timetable', views.refresh_time_table, name="refresh_time_table"),
    path('report', views.test_auto_report, name="auto_report"),
    path('collect/scores', views.test_collect_scores, name="collect_scores"),
    path('query/course_scores', views.query_course_scores, name="query_course_scores"),
    path('query/courses', views.query_course_info, name="query_courses"),
    #path('heu/update', views.update_heu_accounts, name="update_heu_accounts"),
    #path('heu/remove', views.remove_heu_accounts, name="remove_heu_accounts"),

    path('course/comment', views.CourseCommentView.as_view(), name="course_comment"),
]