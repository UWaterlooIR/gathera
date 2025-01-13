from django.contrib import admin

from web.core.models import Session, SharedSession, SessionTimer, ExperimentForm
from web.core.models import Session, SharedSession, SessionTimer, LogEvent
from web.core.models import Session, SharedSession, SessionTimer


class NoAddNoDeleteAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False



class SessionAdmin(NoAddNoDeleteAdmin):
    list_display = ('username', 'get_topic',  'created_at', 'timespent')
    def get_topic(self, obj):
        return obj.topic.title

    list_filter = ('username', 'topic', 'created_at', 'timespent')
    search_fields = ('username', 'topic', 'created_at', 'timespent')

admin.site.register(Session, SessionAdmin)
admin.site.register(SharedSession)

@admin.register(SessionTimer)
class SessionTimerAdmin(admin.ModelAdmin):
    list_display = ('session', 'start_time', 'end_time', 'time_spent')
    list_filter = ('session', 'start_time', 'end_time', 'time_spent')
    search_fields = ('session', 'start_time', 'end_time', 'time_spent')

@admin.register(LogEvent)
class LogEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'user', 'session', 'action', 'data')
    list_filter = ('created_at', 'user', 'session','action')
    search_fields = ('created_at', 'user', 'session','action', 'data')


@admin.register(ExperimentForm)
class ExperimentFormAdmin(admin.ModelAdmin):
    list_display = ('user', 'session', 'form_type', 'form_data')
    list_filter = ('user', 'session', 'form_type' )
    search_fields = ('user', 'session', 'form_type', 'form_data')
