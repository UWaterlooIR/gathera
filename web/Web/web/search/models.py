import uuid

from config.settings.base import AUTH_USER_MODEL as User
from django.contrib.postgres.fields import JSONField
from django.db import models

from web.core.models import Session


class Query(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    query = models.CharField(null=False,
                             blank=False,
                             max_length=1024)
    query_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True,
                                      editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "{}: {}".format(self.username, self.query)

    def __str__(self):
        return self.__unicode__()


class SearchResult(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    query = models.ForeignKey(Query, on_delete=models.CASCADE)
    SERP = JSONField()

    created_at = models.DateTimeField(auto_now_add=True,
                                      editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "{} - {}: {}".format(self.session, self.username, self.query.query)

    def __str__(self):
        return self.__unicode__()


class SERPClick(models.Model):
    username = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    docno = models.CharField(null=False, blank=False, max_length=1024)

    created_at = models.DateTimeField(auto_now_add=True,
                                      editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "{} - {}: {}".format(self.session, self.username, self.docno)

    def __str__(self):
        return self.__unicode__()
