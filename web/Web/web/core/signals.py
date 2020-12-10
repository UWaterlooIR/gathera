from django.db.models.signals import post_delete
from django.db.models.signals import post_save
from django.dispatch import receiver
from notifications.signals import notify

from web.core.models import SharedSession


@receiver(post_delete, sender=SharedSession)
def post_delete_shared_session(sender, instance, using, **kwargs):
    # check if shared session is currently active by shared_with user
    if instance.shared_with.current_session == instance.refers_to:
        instance.shared_with.current_session = None
        instance.shared_with.save()
        # TODO: send signal to user to redirect (async)

    # check if we need to update is_shared field of session
    is_shared = SharedSession.objects.filter(
        refers_to=instance.refers_to
    ).exists()
    if not is_shared:
        instance.refers_to.is_shared = False
        instance.refers_to.save()

    # Send notification to shared with user
    notify.send(sender=instance.refers_to.username,
                recipient=instance.shared_with,
                verb='revoked',
                action_object=instance)


@receiver(post_save, sender=SharedSession)
def post_save_shared_session(sender, instance, **kwargs):
    instance.refers_to.is_shared = True
    instance.refers_to.save()

    shared_with_user = instance.shared_with
    shared_by_user = instance.creator

    # Send notification to shared with user
    notify.send(sender=shared_by_user,
                recipient=shared_with_user,
                verb='shared',
                description=f'{shared_by_user} shared a new session "{instance.refers_to.topic.title}" with you.',
                action_object=instance)
