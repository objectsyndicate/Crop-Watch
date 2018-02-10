from cropwatch.apps.metrics.models import *

try:
    import StringIO
except ImportError:
    import io as StringIO
from django.forms import ModelForm
from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget
from django import forms
from datetime import timedelta

class ioTankForm(forms.ModelForm):
    class Meta:
        model = ioTank
        fields = [
            'name', 'm', 'x', 'm2', 'x2', 'mh', 'xh', 'u', 'night_start', 'night_end', 'night_max_light',
            'day_min_light'
        ]


class BaseModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        try:
            uuid = kwargs.pop('uuid')
            kwargs.setdefault('auto_id', str(uuid) + '_%s')
            kwargs.setdefault('label_suffix', '')
        except:
            kwargs.setdefault('label_suffix', '')

        super().__init__(*args, **kwargs)


class EmailForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['email']

    def save(self, commit=True):
        user = super(EmailForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]

        previous = User.objects.get(id=user.id).email

        if User.objects.filter(email=user.email).exists() and self.cleaned_data["email"] != previous:
            raise forms.ValidationError("EMAILDUP")
        if commit:
            user.save()
        return user


class UserForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        exclude = ['user', 'is_superuser', 'is_staff', 'is_active', 'date_joined', 'first_name', 'last_name',
                   'last_login', 'groups', 'user_permissions']
        password = forms.CharField(widget=forms.PasswordInput)
        widgets = {
            'password': forms.PasswordInput(),
        }

    def save(self, commit=True):
        user = super(UserForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.email = self.cleaned_data["email"]
        if User.objects.filter(email=user.email).exists():
            raise forms.ValidationError("EMAILDUP")
        if commit:
            user.save()
        return user


from timezone_field import TimeZoneFormField


class AccountSettingsForm(forms.ModelForm):
    captcha = ReCaptchaField(widget=ReCaptchaWidget())

    class Meta:
        model = AccountSettings
        exclude = ['user', 'tier', 'habitats_display', 'phone_number', 'notify_future_feedings',
                   'notify_iotank_emergency', 'notify_email', 'notify_sms', 'sms_daily', 'email_daily',
                   'kilowatt_hour_cost']

    def save(self, commit=True):
        m = super(AccountSettingsForm, self).save(commit=False)
        if self.cleaned_data["toc"] is False:
            raise forms.ValidationError("TOC")
        if commit:
            m.save()
        return m


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = AccountSettings
        exclude = ['user', 'tier', 'habitats_display', 'sms_daily', 'email_daily']


class SignupForm(forms.Form):
    toc = forms.BooleanField(label='Do you agree to our terms of service?')
    timezone = TimeZoneFormField()

    def signup(self, request, user):
        social_account = request.session.get('socialaccount_sociallogin')
        account = social_account.pop('account')
        user.username = "fb" + account['uid']
        user.save()
        settings = AccountSettings()
        settings.user = user
        settings.tier = '1'
        settings.timezone = self.cleaned_data['timezone']
        settings.toc = self.cleaned_data['toc']
        settings.sms_daily = '0'
        settings.email_daily = '1'
        settings.save()
        Upgrade.objects.create(user=user, start_date=date.today(), expire_date=timedelta(days=365 * 99) + date.today(),
                               tier='1')
