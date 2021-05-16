from django.db import models
from django.contrib.auth import settings
from django.utils import timezone
import json


class HEUAccountInfo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    heu_username = models.CharField(max_length=100)
    heu_password = models.CharField(max_length=100)
    account_verify_status = models.BooleanField(default=False)
    report_daily = models.BooleanField(default=False)

    def __str__(self):
        return " ".join([str(self.user), self.heu_username])


class CourseInfo(models.Model):
    #课程编号
    course_id = models.CharField(max_length=20)
    #课程名称
    name = models.CharField(max_length=100)
    #学分
    credit = models.CharField(max_length=20)
    #总学时
    total_time = models.CharField(max_length=20)
    #考察方式 test:考查 exam:考试
    assessment_method = models.CharField(max_length=100)
    #课程属性 compulsory:必修 elective:选修
    attributes = models.CharField(max_length=100)
    #课程性质
    kind = models.CharField(max_length=100)
    #通识类别
    general_category = models.CharField(max_length=100)
    #参与统计人数
    count = models.IntegerField(default=0)

    def __str__(self):
        return " ".join([str(self.course_id),self.name])


class CourseScore(models.Model):
    heu_username = models.CharField(max_length=100)
    course = models.ForeignKey(CourseInfo, on_delete=models.DO_NOTHING)
    score = models.CharField(max_length=20)
    term = models.CharField(max_length=50)

    def __str__(self):
        return " ".join([self.heu_username,str(self.course),self.score])


#课程评论
class CourseComment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    course = models.ForeignKey(CourseInfo, on_delete=models.DO_NOTHING)
    content = models.TextField(max_length=100)
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ('-created',)


class ScoreQueryResult(models.Model):
    heu_username = models.CharField(max_length=100)
    result = models.TextField(default="")
    created = models.DateTimeField(default=timezone.now)
    fail = models.BooleanField(default=False)

    def set_result(self, value):
        self.result = json.jumps(value)

    def get_result(self):
        return json.loads(self.result)

    class Meta:
        ordering = ('-created',)


class TimetableQueryResult(models.Model):
    heu_username = models.CharField(max_length=100)
    result = models.TextField(default="")
    created = models.DateTimeField(default=timezone.now)
    fail = models.BooleanField(default=False)

    def set_result(self, value):
        self.result = json.jumps(value)

    def get_result(self):
        return json.loads(self.result)

    class Meta:
        ordering = ('-created',)