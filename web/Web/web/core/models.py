from config.settings.base import AUTH_USER_MODEL as User
import uuid

from django.apps import apps
from django.db import models

from web.CAL.exceptions import CALError
from web.interfaces.CAL import functions as CALFunctions
from web.topic.models import Topic


class Session(models.Model):
    STRATEGY_CHOICES = (
        ('doc', 'Document (CAL)'),
        ('para', 'Paragraph (CAL)'),
        ('doc_scal', 'Document (S-CAL)'),
        ('para_scal', 'Paragraph (S-CAL)'),
    )

    username = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4,
                            editable=False)

    # max number of judgments you wish for this task. 0 or negative to have no max.
    max_number_of_judgments = models.IntegerField(null=False, blank=False)
    max_number_of_judgments_reached = models.BooleanField(default=False)

    strategy = models.CharField(max_length=64,
                                choices=STRATEGY_CHOICES,
                                null=False,
                                blank=False)
    # For paragraphs strategies
    show_full_document_content = models.BooleanField(null=False,
                                                     blank=False)

    # show debugging
    show_debugging_content = models.BooleanField(null=False,
                                                 blank=False)

    # whether this session is being shared with other people
    is_shared = models.BooleanField(null=True, blank=True, default=False)
    # current task active time (in seconds)
    timespent = models.FloatField(default=0)
    # last activity timestamp
    last_activity = models.FloatField(default=None, null=True, blank=True)

    last_activity_timestamp = models.DateTimeField(default=None, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True,
                                      editable=False)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return f'{self.username}-{self.topic.title}-{self.topic.seed_query}'[:25]


    def begin_session_in_cal(self):
        try:
            judgments = self.judgment_set.all()
            judgments_list = [(j.doc_id, j.relevance) for j in judgments]
            CALFunctions.add_session(str(self.uuid),
                                     self.topic.seed_query,
                                     self.strategy,
                                     judgments_list)
        except (CALError, ConnectionRefusedError, Exception) as e:
            # TODO: log error
            pass

    def is_summary(self):
        return "para" in self.strategy

    def get_judgments(self):
        return apps.get_model('judgment.Judgment').objects.filter(session__uuid=self.uuid)

    def __unicode__(self):
        return "<User:{}, Num:{}>".format(self.username, self.topic.number)


class SharedSession(models.Model):

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    refers_to = models.ForeignKey(Session, on_delete=models.CASCADE)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='creator')
    shared_with = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shared_with')

    disallow_search = models.BooleanField(null=True, blank=True, default=False)
    disallow_CAL = models.BooleanField(null=True, blank=True, default=False)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return "<Shared by:{} to {}>".format(self.creator, self.shared_with)

    def __str__(self):
        return self.__unicode__()


class SessionTimer(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='timers')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    time_spent = models.FloatField(null=True, blank=True)


    def save(self, *args, **kwargs):
        old_time = self.time_spent if self.time_spent else 0
        if self.end_time:
            self.time_spent = (self.end_time - self.start_time).total_seconds()
        time_delta = self.time_spent - old_time
        self.session.timespent += time_delta
        self.session.save()
        super().save(*args, **kwargs)

    def __unicode__(self):
        return "<Session:{}>".format(self.session)

    def __str__(self):
        return self.__unicode__()



class LogEvent(models.Model):
    """
    Model for logging user actions
    """
    created_at = models.DateTimeField(auto_now_add=True,
                                      editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    action = models.CharField(max_length=256)
    data = models.TextField(null=True, blank=True)

    # class Meta:
    #     abstract = True
    #     ordering = ['-created_at']
