from django.db import models

from django.db import models
from django.contrib.auth import settings


class HEUAccountInfo(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.DO_NOTHING)
    heu_username = models.CharField(max_length=100)
    heu_password = models.CharField(max_length=100)
    account_verify_status = models.BooleanField(default=False)
