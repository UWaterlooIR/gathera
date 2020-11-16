from django.contrib import messages

from web.CAL.exceptions import CALError
from web.interfaces.CAL import functions as CALFunctions
from web.core.forms import SessionForm
from web.core.forms import SessionPredefinedTopicForm
from web.core.models import Session
from web.core.models import SharedSession
from web.users.models import User

NEW_SESSION_MESSAGE = 'Your session has been initialized and activated. ' \
                      'Choose a retrieval method to start searching.'


def submit_new_predefined_topic_session_form(request):
    success_message = NEW_SESSION_MESSAGE

    form = SessionPredefinedTopicForm(request.POST)
    if form.is_valid():
        f = form.save(commit=False)
        f.username = request.user
        f.save()
        request.user.current_session = form.instance
        request.user.save()
        messages.add_message(request,
                             messages.SUCCESS,
                             success_message)
    else:
        messages.add_message(request, messages.ERROR, f'Ops! {form.errors}')


def submit_new_session_form(request):
    success_message = NEW_SESSION_MESSAGE

    form = SessionForm(request.POST)
    if form.is_valid():
        f = form.save(commit=False)
        f.save()
        max_number_of_judgments = form.cleaned_data['max_number_of_judgments']
        strategy = form.cleaned_data['strategy']
        show_full_document_content = form.cleaned_data['show_full_document_content']
        session = Session.objects.create(
            username=request.user,
            topic=form.instance,
            max_number_of_judgments=max_number_of_judgments,
            strategy=strategy,
            show_full_document_content=show_full_document_content
        )
        messages.add_message(request,
                             messages.SUCCESS,
                             success_message)
        request.user.current_session = session
        request.user.save()


def activate_session_submit_form(request):
    session_id = request.POST.get("activate_sessionid")
    is_shared_session = request.POST.get("is_shared_session", False)
    is_shared_session = is_shared_session == "true"

    try:
        if is_shared_session:
            shared_session_obj = SharedSession.objects.get(
                uuid=session_id,
                shared_with=request.user,
            )
            session = shared_session_obj.refers_to
        else:
            session = Session.objects.get(username=request.user,
                                          uuid=session_id)
    except (SharedSession.DoesNotExist, Session.DoesNotExist):
        message = 'Ops! your session can not be found.'
        messages.add_message(request,
                             messages.ERROR,
                             message)

        return False

    request.user.current_session = session
    request.user.save()

    message = 'Your session has been activated. ' \
              'Choose a retrieval method to start judging.'
    messages.add_message(request,
                         messages.SUCCESS,
                         message)
    return True


def share_session_submit_form(request):
    try:
        session_id = request.POST.get("share_sessionid")
        share_with_user_pk = request.POST.get("share-shared_with")
        disallow_search = request.POST.get("share-disallow_search", False)
        disallow_CAL = request.POST.get("share-disallow_CAL", False)
        if disallow_search == "on":
            disallow_search = True
        if disallow_CAL == "on":
            disallow_CAL = True

        session_obj = Session.objects.get(username=request.user,
                                          uuid=session_id)
        shared_with_user = User.objects.get(pk=share_with_user_pk)

        if 'scal' in session_obj.strategy:
            # Cant share a session of this type
            message = 'Ops! You can not share a session with strategy `{}`.'.format(session_obj.get_strategy_display())
            messages.add_message(request,
                                 messages.ERROR,
                                 message)

            return

    except KeyError:
        message = 'Ops! An error has occurred.'
        messages.add_message(request,
                             messages.ERROR,
                             message)
        return
    except Session.DoesNotExist:
        message = 'Ops! something wrong happened. Your session can not be found.'
        messages.add_message(request,
                             messages.ERROR,
                             message)
        return
    except User.DoesNotExist:
        message = 'Ops! something wrong happened. User can not be found.'
        messages.add_message(request,
                             messages.ERROR,
                             message)
        return

    # Check if already shared
    exists = SharedSession.objects.filter(refers_to=session_obj,
                                          creator=request.user,
                                          shared_with=shared_with_user).exists()
    if exists:
        message = 'Ops! session is already shared with user {}.'.format(
            shared_with_user.username)
        messages.add_message(request,
                             messages.ERROR,
                             message)
        return

    # Create new SharedSession
    # post_init in signals.py will take care of updating
    # is_shared field in refers_to session
    shared_session_obj = SharedSession.objects.create(
        refers_to=session_obj,
        creator=request.user,
        shared_with=shared_with_user,
        disallow_search=disallow_search,
        disallow_CAL=disallow_CAL
    )

    message = "Your session '{}' has been shared with {}.".format(
        shared_session_obj.refers_to.topic.title,
        shared_session_obj.shared_with.username,
    )
    messages.add_message(request,
                         messages.SUCCESS,
                         message)

    return


def revoke_shared_session_submit_form(request):
    try:
        session_id = request.POST.get("revoke_sessionid")
        shared_session_obj = SharedSession.objects.get(
            creator=request.user,
            uuid=session_id
        )

        # Delete SharedSession instance
        # post_delete in signals.py will take care of updating
        # current_session of shared_with user
        shared_session_obj.delete()

        message = 'Shared session has been revoked from {}.'.format(
            shared_session_obj.shared_with.username)
        messages.add_message(request,
                             messages.SUCCESS,
                             message)
        return
    except SharedSession.DoesNotExist:
        message = 'Ops! something wrong happened. Shared session can not be found.'
        messages.add_message(request,
                             messages.ERROR,
                             message)
        return

    return


def delete_session_submit_form(request):
    session_id = request.POST.get("delete_sessionid")
    session = Session.objects.filter(username=request.user,
                                     uuid=session_id)

    if session.exists():

        if request.user.current_session and str(request.user.current_session.uuid) == session_id:
            request.user.current_session = None
            request.user.save()

        session = session.first()
        session_title = session.topic.title
        session.delete()
        try:
            CALFunctions.delete_session(session_id)
        except CALError:
            pass
        message = 'Session "{}" has been deleted.'.format(session_title)
        messages.add_message(request,
                             messages.SUCCESS,
                             message)

    else:
        message = 'Ops! session can not be found.'
        messages.add_message(request,
                             messages.ERROR,
                             message)
