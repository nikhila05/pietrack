from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMultiAlternatives
from django.template import loader
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext, ugettext_lazy as _
from .tasks import celery_send_mail
from piebase.models import Project, Priority, Severity, Organization, User, TicketStatus, Role
from django.template.defaultfilters import slugify


class CreateProjectForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super(CreateProjectForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Project
        fields = ['name', 'description']

    def clean_name(self):
        name = self.cleaned_data['name']
        if (Project.objects.filter(name=name, organization=self.organization)):
            raise forms.ValidationError(
                'Project with this name already exists.')
        return name


class PriorityIssueForm(forms.ModelForm):

    class Meta:
        model = Priority
        fields = ['name', 'color']

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super(PriorityIssueForm, self).__init__(*args, **kwargs)
        self.projectObj = Project.objects.get(slug=self.project)

    def save(self, commit=True):
        instance = super(PriorityIssueForm, self).save(commit=False)
        instance.project = self.projectObj
        instance.slug = slugify(self.cleaned_data['name'])
        if commit:
            instance.save()
        return instance

    def clean_name(self):
        name = self.cleaned_data['name']
        if(Priority.objects.filter(slug=slugify(name), project=self.projectObj)):
            raise forms.ValidationError(
                'Priority with this name already exists')
        elif len(slugify(name)) == 0:
            raise forms.ValidationError("This field is required.")
        return name


class PriorityIssueFormEdit(forms.ModelForm):

    class Meta:
        model = Priority
        fields = ['name', 'color']

    def clean_name(self):
        name_slug = slugify(self.cleaned_data.get('name'))
        if(Priority.objects.filter(slug=name_slug, project=self.instance.project) and name_slug != self.instance.slug):
            raise forms.ValidationError(
                'Priority with this name already exists')
        elif len(name_slug) == 0:
            raise forms.ValidationError("This field is required.")
        return self.cleaned_data.get('name')

    def save(self, commit=True):
        instance = super(PriorityIssueFormEdit, self).save(commit=False)
        instance.slug = slugify(self.cleaned_data['name'])
        instance.name = self.cleaned_data['name']
        instance.color = self.cleaned_data['color']
        if commit:
            instance.save()
        return instance


class SeverityIssueForm(forms.ModelForm):

    class Meta:
        model = Severity
        fields = ['name', 'color']

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super(SeverityIssueForm, self).__init__(*args, **kwargs)
        self.projectObj = Project.objects.get(slug=self.project)

    def save(self, commit=True):
        instance = super(SeverityIssueForm, self).save(commit=False)
        instance.project = self.projectObj
        instance.slug = slugify(self.cleaned_data['name'])
        if commit:
            instance.save()
        return instance

    def clean_name(self):
        name = self.cleaned_data['name']
        if(Severity.objects.filter(slug=slugify(name), project=self.projectObj)):
            raise forms.ValidationError(
                'Severity with this name already exists')
        elif len(slugify(name)) == 0:
            raise forms.ValidationError("This field is required.")
        return name


class SeverityIssueFormEdit(forms.ModelForm):

    class Meta:
        model = Severity
        fields = ['name', 'color']

    def clean_name(self):
        name_slug = slugify(self.cleaned_data.get('name'))
        if(Severity.objects.filter(slug=name_slug, project=self.instance.project) and name_slug != self.instance.slug):
            raise forms.ValidationError(
                'Severity with this name already exists')
        elif len(name_slug) == 0:
            raise forms.ValidationError("This field is required.")
        return self.cleaned_data.get('name')

    def save(self, commit=True):
        instance = super(SeverityIssueFormEdit, self).save(commit=False)
        instance.slug = slugify(self.cleaned_data['name'])
        instance.name = self.cleaned_data['name']
        instance.color = self.cleaned_data['color']
        if commit:
            instance.save()
        return instance


class TicketStatusForm(forms.ModelForm):

    class Meta:
        model = TicketStatus
        fields = ['name', 'color']

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super(TicketStatusForm, self).__init__(*args, **kwargs)
        self.projectObj = Project.objects.get(slug=self.project)

    def save(self, commit=True):
        instance = super(TicketStatusForm, self).save(commit=False)
        instance.project = self.projectObj
        instance.slug = slugify(self.cleaned_data['name'])
        if commit:
            instance.save()
        return instance

    def clean_name(self):
        name = self.cleaned_data['name']
        if(TicketStatus.objects.filter(slug=slugify(name), project=self.projectObj)):
            raise forms.ValidationError(
                'Ticket Status with this name already exists')
        elif len(slugify(name)) == 0:
            raise forms.ValidationError("This field is required.")
        return name


class TicketStatusFormEdit(forms.ModelForm):

    class Meta:
        model = TicketStatus
        fields = ['name', 'color']

    def clean_name(self):
        name_slug = slugify(self.cleaned_data.get('name'))
        if(TicketStatus.objects.filter(slug=name_slug, project=self.instance.project) and name_slug != self.instance.slug):
            raise forms.ValidationError(
                'Ticket Status with this name already exists')
        elif len(name_slug) == 0:
            raise forms.ValidationError("This field is required.")
        return self.cleaned_data.get('name')

    def save(self, commit=True):
        instance = super(TicketStatusFormEdit, self).save(commit=False)
        instance.slug = slugify(self.cleaned_data['name'])
        instance.name = self.cleaned_data['name']
        instance.color = self.cleaned_data['color']
        if commit:
            instance.save()
        return instance


class CreateMemberForm(forms.Form):
    email = forms.EmailField()
    designation = forms.CharField()
    description = forms.Textarea()


class PasswordResetForm(forms.Form):
    email = forms.EmailField(label=_("Email"), max_length=254)

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email, html_email_template_name=None):
        """
        Sends a django.core.mail.EmailMultiAlternatives to `to_email`.
        """
        subject = loader.render_to_string(subject_template_name, context)
        subject = ''.join(subject.splitlines())
        body = loader.render_to_string(email_template_name, context)

        email_message = EmailMultiAlternatives(
            subject, body, from_email, [to_email])
        if html_email_template_name is not None:
            html_email = loader.render_to_string(
                html_email_template_name, context)
            email_message.attach_alternative(html_email, 'text/html')

        email_message.send()

    def get_users(self, email):
        """Given an email, return matching user(s) who should receive a reset.

        This allows subclasses to more easily customize the default policies
        that prevent inactive users and users with unusable passwords from
        resetting their password.

        """
        active_users = get_user_model()._default_manager.filter(
            email__iexact=email, is_active=True)
        return (u for u in active_users if u.has_usable_password())

    def save(self, domain_override=None,
             subject_template_name='registration/password_reset_subject.txt',
             email_template_name='registration/password_reset_email.html',
             use_https=False, token_generator=default_token_generator,
             from_email=None, request=None, html_email_template_name=None):
        """
        Generates a one-use only link for resetting password and sends to the
        user.
        """
        email = self.cleaned_data["email"]
        for user in self.get_users(email):
            if not domain_override:
                current_site = get_current_site(request)
                site_name = current_site.name
                domain = current_site.domain
            else:
                site_name = domain = domain_override
            context = {
                'email': user.email,
                'domain': domain,
                'site_name': site_name,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': token_generator.make_token(user),
                'protocol': 'https' if use_https else 'http',
            }

            celery_send_mail.delay(subject_template_name, email_template_name,
                                   context, from_email, user.email,
                                   html_email_template_name=html_email_template_name)


class RoleAddForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super(RoleAddForm, self).__init__(*args, **kwargs)
        self.projectObj = Project.objects.get(slug=self.project)

    class Meta:
        model = Role
        fields = ['name']

    def clean_name(self):
        name = self.cleaned_data['name']
        if(Role.objects.filter(slug=slugify(name), project=self.projectObj)):
            raise forms.ValidationError('Role with this name already exists')
        elif len(slugify(name)) == 0:
            raise forms.ValidationError("This field is required.")
        return name

    def save(self, commit=True):
        instance = super(RoleAddForm, self).save(commit=False)
        instance.project = self.projectObj
        instance.name = self.cleaned_data['name']
        instance.slug = slugify(self.cleaned_data['name'])

        if commit:
            instance.save()
        return instance


class RoleEditForm(forms.ModelForm):

    class Meta:
        model = Role
        fields = ['name']

    def clean_name(self):
        name = self.cleaned_data['name']
        if(Role.objects.filter(slug=slugify(name), project=self.instance.project) and  slugify(name)!= self.instance.slug):
            raise forms.ValidationError('Role with this name already exists')
        elif len(slugify(name)) == 0:
            raise forms.ValidationError("This field is required.")
        return name

    def save(self, commit=True):
        instance = super(RoleEditForm, self).save(commit=False)
        instance.name = self.cleaned_data['name']
        instance.slug = slugify(self.cleaned_data['name'])
        if commit:
            instance.save()
        return instance
