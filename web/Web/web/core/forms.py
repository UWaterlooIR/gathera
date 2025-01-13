from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Column, Row, Field, Div
from django import forms
from django.db.models import Q
from web.core.models import Session, SharedSession
from web.topic.models import Topic
from web.users.models import User
from dal import autocomplete


class SessionPredefinedTopicForm(forms.ModelForm):
    """
    Form for creating Task with pre-defined topic

    """
    submit_name = 'submit-session-predefine-topic-form'
    prefix = "predefined"

    class Meta:
        model = Session
        exclude = ["username", "setting", "timespent", "last_activity"]
        help_texts = {
            'max_number_of_judgments': '(Optional) Set max number of judgments.',
            'strategy': "Discovery's strategy of retrieval.",
        }

    strategy = forms.ChoiceField(choices=Session.STRATEGY_CHOICES,
                                 label="Discovery's strategy",
                                 required=True)
    max_number_of_judgments = forms.IntegerField(required=False,
                                                 label="Effort",
                                                 help_text=Meta.help_texts.get(
                                                     'max_number_of_judgments'))
    show_debugging_content = forms.BooleanField(required=False,
                                                label="Debugging mode",
                                                )

    integrated_cal = forms.BooleanField(required=False, label="Use Integrated CAL")

    nudge_to_cal = forms.BooleanField(required=False, label="Nudge to CAL")

    disable_search = forms.BooleanField(required=False, label="Disable search")

    def __init__(self, *args, **kwargs):
        super(SessionPredefinedTopicForm, self).__init__(*args, **kwargs)
        self.fields['topic'].queryset = Topic.objects.filter(~Q(number=None)).order_by('number')
        self.helper = FormHelper(self)

        self.helper.layout = Layout(
            'topic',
            Row(
                Column('max_number_of_judgments', css_class='form-group col-md-6 mb-0'),
                Column('strategy', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('disable_search', css_class='form-group col-md-4 mb-0'),
                Column('show_debugging_content', css_class='form-group col-md-4 mb-0',
                       css_id="predefined-show_debugging_content"),
            ),
            Row(
                Column('integrated_cal', css_class='form-group col-md-4 mb-0'),
                Column('nudge_to_cal', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Div(
                Field('show_full_document_content'),
                css_class='d-none',
                css_id="predefined-show_full_document_content"
            ),
            StrictButton(u'Create session',
                         name=self.submit_name,
                         type="submit",
                         css_class='btn btn-outline-secondary')
        )

    def clean_max_number_of_judgments(self):
        data = self.cleaned_data['max_number_of_judgments']
        if not data:
            data = 0
        return data


class SessionForm(forms.ModelForm):
    """
    Form for creating Session

    """
    submit_name = 'submit-session-form'
    prefix = "topic"

    class Meta:
        model = Topic
        exclude = ["number", "display_description", "narrative"]

    max_number_of_judgments = forms.IntegerField(required=False,
                                                 label="Effort",
                                                 help_text=SessionPredefinedTopicForm.Meta.help_texts.get('max_number_of_judgments'))
    strategy = forms.ChoiceField(choices=Session.STRATEGY_CHOICES,
                                 label="Discovery's strategy",
                                 required=True,
                                 help_text=SessionPredefinedTopicForm.Meta.help_texts.get('strategy'))
    show_full_document_content = forms.BooleanField(required=False)
    show_debugging_content = forms.BooleanField(required=False,
                                                label="Debugging mode",
                                                )
    judgments_file = forms.FileField(required=False, label='Optional seed judgments (csv file)')

    integrated_cal = forms.BooleanField(required=False, label="Use Integrated CAL")

    nudge_to_cal = forms.BooleanField(required=False, label="Nudge to CAL")

    disable_search = forms.BooleanField(required=False, label="Disable search")

    def __init__(self, *args, **kwargs):
        super(SessionForm, self).__init__(*args, **kwargs)
        self.fields['description'].widget.attrs['rows'] = 4
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('title', css_class='form-group col-md-4 mb-0'),
                Column('seed_query', css_class='form-group col-md-8 mb-0'),
                css_class='form-row'
            ),
            'description',
            Row(
                Column('max_number_of_judgments', css_class='form-group col-md-6 mb-0'),
                Column('strategy', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(
                Column('disable_search', css_class='form-group col-md-4 mb-0'),
                Column('show_debugging_content', css_class='form-group col-md-4 mb-0',css_id="predefined-show_debugging_content"),
            ),
            Row(
                Column('integrated_cal', css_class='form-group col-md-4 mb-0'),
                Column('nudge_to_cal', css_class='form-group col-md-4 mb-0'),
                css_class='form-row'
            ),
            Div(
                Field('show_full_document_content'),
                css_class='d-none',
                css_id="topic-show_full_document_content"
            ),
            'judgments_file',
            StrictButton(u'Create session',
                         name=self.submit_name,
                         type="submit",
                         css_class='btn btn-outline-secondary')
            # Alternative to StrictButton
            # Submit(self.submit_name, u'Create topic and start judging',
            #       css_class='btn')
        )

    def clean_max_number_of_judgments(self):
        data = self.cleaned_data['max_number_of_judgments']
        if not data:
            data = 0
        return data


class ShareSessionForm(forms.ModelForm):
    """
    Form for sharing a session

    """
    submit_name = 'submit-share-session-form'
    prefix = "share"

    class Meta:
        model = SharedSession
        exclude = ["refers_to", "creator"]

    disallow_search = forms.BooleanField(required=False,
                                         label="Hide search from user")
    disallow_CAL = forms.BooleanField(required=False,
                                      label="Hide Discovery from user")

    def __init__(self, user, *args, **kwargs):
        super(ShareSessionForm, self).__init__(*args, **kwargs)
        self.fields['shared_with'] = forms.ModelChoiceField(
            label="Share with",
            queryset=User.objects.filter(~Q(pk=user.pk)),
            widget=autocomplete.ModelSelect2(url='users:user-autocomplete',
                                             attrs={
                                                 'data-placeholder': "username",
                                                 'data-minimum-input-length': 1,
                                             },
                                             )
        )
        self.helper = FormHelper(self)
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'shared_with',
            'disallow_search',
            'disallow_CAL'
        )



class PreTaskQuestionnaireForm(forms.Form):
    """
    Form for pre-task questionnaire

    """
    submit_name = 'submit-pre-task-questionnaire-form'
    prefix = "pre-task"

    topic_familiarity_choices = (
        ('', '-----------'),
        (1, 'Not at all'),
        (2, 'A little'),
        (3, 'Moderately'),
        (4, 'Very'),
        (5, 'Extremely'),
    )

    topic_familiarity = forms.ChoiceField(choices= topic_familiarity_choices,
                                            label="How familiar are you with the subject of the "
                                                  "topic given above?",
                                            required=True)
    topic_hardness = forms.ChoiceField(choices= topic_familiarity_choices,
                                            label="How difficult do you think it will be to find "
                                                  "relevant documents for this topic?",
                                            required=True)
    general_feedback = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}), label="Do you have any feedback you would like "
                                                        "to provide on this topic?",
        required=False)

    def __init__(self, *args, **kwargs):
        super(PreTaskQuestionnaireForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            'topic_familiarity',
            'topic_hardness',
            'general_feedback',
            StrictButton(u'Submit',
                         name=self.submit_name,
                         type="submit",
                         css_class='btn btn-outline-secondary')
        )


class PostTaskQuestionnaireForm(forms.Form):
    """
    Form for post-task questionnaire

    """
    submit_name = 'submit-post-task-questionnaire-form'
    prefix = "post-task"

    topic_choices = (
        ('', '-----------'),
        (1, 'Not at all'),
        (2, 'A little'),
        (3, 'Moderately'),
        (4, 'Very'),
        (5, 'Extremely'),
    )

    mood_choices = (
        ('', '-----------'),
        (1, 'Frustrated'),
        (2, 'Anxious'),
        (3, 'Neutral'),
        (4, 'Happy'),
        (5, 'Excited'),
    )


    topic_difficulty = forms.ChoiceField(
        choices= topic_choices,
        label="How difficult was it to find relevant documents for this topic?",
        required=True
    )
    confidence = forms.ChoiceField(
        choices= topic_choices,
        label="How confident are you in your judgments of the documents you have judged?",
        required=True
    )
    mood = forms.ChoiceField(
        choices= mood_choices,
        label="How was your mood during the task?",
        required=True,
    )
    general_feedback = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        label="Do you have any feedback/issues you would like to provide on this task?",
        required=False
    )

    def __init__(self, *args, **kwargs):
        super(PostTaskQuestionnaireForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            'topic_difficulty',
            'confidence',
            'mood',
            'general_feedback',
            StrictButton(u'Submit',
                         name=self.submit_name,
                         type="submit",
                         css_class='btn btn-outline-secondary')
        )

class PostExperimentQuestionnaireForm(forms.Form):

    submit_name = 'submit-post-experiment-questionnaire-form'
    prefix = "post-experiment"

    topic_choices = (
        ('', '-----------'),
        (1, 'Not at all'),
        (2, 'A little'),
        (3, 'Moderately'),
        (4, 'Very'),
        (5, 'Extremely'),
    )

    mood_choices = (
        ('', '-----------'),
        (1, 'Frustrated'),
        (2, 'Anxious'),
        (3, 'Neutral'),
        (4, 'Happy'),
        (5, 'Excited'),
    )

    experience_choices = (
        ('', '-----------'),
        (1, 'Very dissatisfied'),
        (2, 'Dissatisfied'),
        (3, 'Unsure'),
        (4, 'Satisfied'),
        (5, 'Very satisfied'),
    )

    study_difficulty = forms.ChoiceField(
        choices= topic_choices,
        label="How would you rate the overall difficulty of the study?",
        required=True
    )
    experience = forms.ChoiceField(
        choices= experience_choices,
        label="How was your overall experience?",
        required=True
    )
    mood = forms.ChoiceField(
        choices= mood_choices,
        label="How was your overall mood during the study?",
        required=True
    )
    general_feedback = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        label="Do you have any feedback/issues you would like to provide after finishing the "
              "study?",
        required=False
    )

    likeness = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        label="What did you like about the study?",
        required=True
    )

    dislike = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        label="What did you dislike about the study?",
        required=True
    )

    system = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        label="Which feature was the most useful in finding documents? Explain.",
        required=True
    )


    def __init__(self, *args, **kwargs):
        super(PostExperimentQuestionnaireForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            'study_difficulty',
            'experience',
            'mood',
            'general_feedback',
            'likeness',
            'dislike',
            'system',
            StrictButton(u'Submit',
                         name=self.submit_name,
                         type="submit",
                         css_class='btn btn-outline-secondary')
        )
