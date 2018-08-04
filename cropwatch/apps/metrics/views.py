import time
from datetime import datetime
from smtplib import SMTPRecipientsRefused

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import password_reset, password_reset_confirm
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.utils.timezone import activate
from django_celery_results.models import TaskResult
from rest_framework.authtoken.models import Token

from cropwatch.apps.metrics.forms import *
from cropwatch.apps.metrics.models import *
from cropwatch.settings import DEFAULT_FROM_EMAIL


def status():
    stat = '{ "status": "OK" }'
    return HttpResponse(stat, content_type='application/json')


@login_required
def base(request, form_class=ioTankForm):
    object_list = []
    bot_forms = {}
    account_settings = AccountSettings.objects.get(user=request.user)
    activate(account_settings.timezone)
    if not ioTank.objects.filter(owner=request.user):
        bots = None
    else:
        bots = ioTank.objects.filter(owner=request.user)
        for bot in bots:
            form = form_class(request.POST or None, instance=bot)
            bot_forms[bot] = form
    return render(request, 'metrics.html',
                  {'cal_json': object_list, 'bots': bots, 'tz': account_settings.timezone, 'bot_forms': bot_forms})


@login_required
def iotank_edit(request, uuid=None, form_class=ioTankForm, ):
    bot = ioTank.objects.get(id=uuid)
    if request.method == "POST":
        if request.POST["action"] == "Save":
            bot_form = form_class(request.POST, instance=bot)
            if bot_form.is_valid():
                form = bot_form.save(commit=False)
                form.save()
                return HttpResponseRedirect('/devices/')
        else:
            return HttpResponseRedirect('/devices/')
    else:
        return HttpResponseRedirect('/devices/')
    return HttpResponseRedirect('/devices/')


@login_required
def notice(request):
    last_month = datetime.today() - timedelta(days=15)
    notices = Notice.objects.filter(owner=request.user).filter(timestamp__gte=last_month).order_by('-timestamp')
    final = {}
    settings = AccountSettings.objects.get(user=request.user)
    activate(settings.timezone)
    for notice in notices:
        qs = TaskResult.objects.get(task_id=notice.taskid)
        final[notice] = qs
    return render(request, 'notice.html', {'final': final, 'settings': settings})


@login_required
def flot_ajax(request, start, end, uuid):
    data = ""
    # check if the incoming values are integers,
    try:
        int(start) and int(end)
        # are they 13 digit integers, (are they timestamps)
        if len(start) == 13 and len(end) == 13:
            t1 = []
            t2 = []
            h = []
            uv = []
            l = []
            # does the user have an iotank?
            if not ioTank.objects.filter(owner=request.user):
                bots = None
            else:
                bots = ioTank.objects.get(owner=request.user, id=uuid)
                # Z for UTC %z for localtz
                start = time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime(int(start) / 1000.))
                end = time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime(int(end) / 1000.))
                readings = SensorReading.objects.filter(bot=bots, timestamp__range=(start, end)).order_by('timestamp')
                for i in readings:
                    if bots.u == 'F':
                        i.t1 = 9.0 / 5.0 * int(i.t1) + 32
                        i.t2 = 9.0 / 5.0 * int(i.t2) + 32
                    t1_list = []
                    t2_list = []
                    h_list = []
                    uv_list = []
                    l_list = []

                    unixtime = int(time.mktime(i.timestamp.timetuple()) * 1000)

                    t1_list.append(unixtime)
                    t1_list.append(float(i.t1))
                    t1.append(t1_list)

                    t2_list.append(unixtime)
                    t2_list.append(int(i.t2))
                    t2.append(t2_list)

                    h_list.append(unixtime)
                    h_list.append(int(i.h))
                    h.append(h_list)

                    uv_list.append(unixtime)
                    uv_list.append(float(i.uv))
                    uv.append(uv_list)

                    l_list.append(unixtime)
                    l_list.append(float(i.l))
                    l.append(l_list)

            data = '{"data":{"t1":' + str(t1) + ',"t2":' + str(t2) + ',"h":' + str(h) + ',"uv":' + str(
                uv) + ',"l":' + str(l) + '}}'
    except ValueError:
        return HttpResponse(start + end, content_type='application/json')
    return HttpResponse(data, content_type='application/json')


# List all devices
@login_required
def devices(request, form_class=ioTankForm, ):
    account_settings = AccountSettings.objects.get(user=request.user)
    activate(account_settings.timezone)
    bot_forms = {}
    if not ioTank.objects.filter(owner=request.user):
        messages.error(request, "You need to add an ioTank", extra_tags='safe')
    else:
        bots = ioTank.objects.filter(owner=request.user)
        for bot in bots:
            form = form_class(request.POST or None, instance=bot)
            bot.token = Token.objects.get(user=bot.bot_user)
            bot_forms[bot] = form
    return render(request, "devices.html", {'bot_forms': bot_forms})


# Add new ioTank
@login_required
def bot_add(request):
    newio = ioTank(owner=request.user)
    user = User.objects.create_user(str(newio)[:30])
    newio.bot_user_id = user.id
    newio.save()
    Token.objects.get_or_create(user=user)
    return HttpResponseRedirect('/devices/')


# Delete ioTank and all sensor data for said unit.
@login_required
def bot_delete(request, uuid=None):
    bot = ioTank.objects.get(id=uuid)
    bot.bot_user.delete()
    return HttpResponseRedirect('/devices/')


# Regen Token
@login_required
def bot_regen(request, uuid=None):
    bot = ioTank.objects.get(id=uuid)
    token = Token.objects.get(user=bot.bot_user)
    token.delete()
    Token.objects.get_or_create(user=bot.bot_user)
    return HttpResponseRedirect('/devices/')


def reset(request):
    # Wrap the built-in password reset view and pass it the arguments
    # like the template name, email template name, subject template name
    # and the url to redirect after the password reset is initiated.
    if request.user.is_authenticated():
        return HttpResponseRedirect('/metrics/')
    else:
        return password_reset(request, template_name='reset.html',
                              email_template_name='reset_email.html',
                              subject_template_name='reset_subject.txt',
                              post_reset_redirect=reverse('resetsent'))


# This view handles password reset confirmation links. See urls.py file for the mapping.
# This view is not used here because the password reset emails with confirmation links
# cannot be sent from this application.
def reset_confirm(request, uidb64=None, token=None):
    # Wrap the built-in reset confirmation view and pass to it all the captured parameters like uidb64, token
    # and template name, url to redirect after password reset is confirmed.
    if request.user.is_authenticated():
        return HttpResponseRedirect('/metrics/')
    else:
        return password_reset_confirm(request, template_name='reset_confirm.html',
                                      uidb64=uidb64, token=token, post_reset_redirect=reverse('success'))


# This view renders a page with success message.
def success(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/metrics/')
    else:
        return render(request, "success.html")


# This view renders a page with success message.
def resetsent(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/metrics/')
    else:
        return render(request, "resetsent.html")


@login_required
def settings(request):
    errors = "NONE"
    setting = AccountSettings.objects.get(user=request.user)
    user = User.objects.get(username=request.user)
    if request.method == 'POST':
        upf = UserProfileForm(request.POST, instance=setting)
        emailf = EmailForm(request.POST, instance=user)
        if upf.is_valid() and emailf.is_valid():
            try:
                emailf.save(commit=False)
                upf.save()
                emailf.save()
            except ValidationError as e:
                errors = str(e.message)
                upf = UserProfileForm(instance=setting)
                emailf = EmailForm(instance=user)
        else:
            upf = UserProfileForm(instance=setting)
            emailf = EmailForm(instance=user)
    else:
        upf = UserProfileForm(instance=setting)
        emailf = EmailForm(instance=user)
    return render(request, 'settings.html', {'userprofileform': upf, 'email_form': emailf, 'errors': errors})


def register(request):
    errors = "NONE"
    if request.user.is_authenticated():
        return HttpResponseRedirect('/metrics/')
    else:
        if request.method == 'POST':
            uf = UserForm(request.POST, prefix='user')
            upf = AccountSettingsForm(request.POST, prefix='userprofile')
            print(uf.errors)
            print(upf.errors)
            if uf.is_valid() and upf.is_valid():
                # this is a cheap way to verify e-mails are unique on signup.
                # We can't reasonably edit the django user model now
                try:
                    user = uf.save(commit=False)
                    try:
                        send_mail(
                            'ObjectSyndicate.com registration.',
                            'Your registration is complete. Your username is ' + str(user) + '.',
                            DEFAULT_FROM_EMAIL,
                            [uf.cleaned_data['email']],
                            fail_silently=False,
                        )
                    except SMTPRecipientsRefused:
                        #
                        errors = "EMAILFAIL"
                        uf = UserForm(prefix='user')
                        upf = AccountSettingsForm(prefix='userprofile')
                        return render(request, 'register.html',
                                      {'userform': uf, 'userprofileform': upf, 'errors': errors})
                    try:
                        userprofile = upf.save(commit=False)
                        user = uf.save()
                        userprofile.user = user
                        userprofile.tier = '1'
                        userprofile.save()
                        user = authenticate(username=uf.cleaned_data['username'],
                                            password=uf.cleaned_data['password'],
                                            )
                        login(request, user)
                        return HttpResponseRedirect('/metrics/')
                    except ValidationError as e:
                        #
                        errors = str(e.message)
                        uf = UserForm(prefix='user')
                        upf = AccountSettingsForm(prefix='userprofile')
                except ValidationError as e:
                    #
                    errors = str(e.message)
                    uf = UserForm(prefix='user')
                    upf = AccountSettingsForm(prefix='userprofile')
            else:
                uf = UserForm(prefix='user')
                upf = AccountSettingsForm(prefix='userprofile')
        else:
            uf = UserForm(prefix='user')
            upf = AccountSettingsForm(prefix='userprofile')
    return render(request, 'register.html', {'userform': uf, 'userprofileform': upf, 'errors': errors})
