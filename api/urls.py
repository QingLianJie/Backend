from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    path('query/scores', views.query_scores, name="query_scores"),
    path('refresh/scores', views.refresh_scores, name="refresh_scores"),
    path('query/timetable', views.query_time_table, name="query_time_table"),
    path('refresh/timetable', views.refresh_time_table, name="refresh_time_table"),
    # path('report', views.test_auto_report, name="auto_report"),
    path('collect/scores', views.test_collect_scores, name="collect_scores"),
    path('query/course_scores', views.query_course_scores, name="query_course_scores"),
    path('query/courses', views.query_course_info, name="query_courses"),
    #path('heu/update', views.update_heu_accounts, name="update_heu_accounts"),
    #path('heu/remove', views.remove_heu_accounts, name="remove_heu_accounts"),

    path('course/comment', views.CourseCommentView.as_view(), name="course_comment"),
    path('course/count', views.course_count, name="course_count"),
    path('course/comment/my', views.query_my_comment, name="query_my_comment"),
    path('course/comment/remove', views.remove_my_comment, name="remove_my_comment"),
    path('course/recent', views.recent_grade_course, name="recent_grade_course"),

    path('pingjiao', views.pingjiao, name="query_pingjiao"),
    path('pingjiao/do', views.do_pingjiao, name="do_pingjiao"),

    path('grade/notify', login_required(views.MailWhenGradeView.as_view()),
                                        name="grade_notify"),
]
