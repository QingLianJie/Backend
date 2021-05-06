from django.db import models
from django.utils import timezone
from mdeditor.fields import MDTextField


class Article(models.Model):
    title = models.CharField(max_length=100)
    body = MDTextField()
    created = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ('-created',)

    def __str__(self):
        return self.title