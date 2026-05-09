import os
import secrets
import string

from django.utils import timezone
from zoneinfo import ZoneInfo
from functools import wraps
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    AdminLoginForm,
    EventForm,
    ForgotPasswordForm,
    LoginForm,
    PasswordUpdateForm,
    ProfileUpdateForm,
    RegisterForm,
    password_matches,
)
from .models import Event, Registration, User


USER_SESSION_ID = 'user_id'
USER_SESSION_NAME = 'user_full_name'
ADMIN_SESSION_KEY = 'admin_logged_in'


def get_current_user(request):
    user_id = request.session.get(USER_SESSION_ID)
    if not user_id:
        return None
    try:
        return User.objects.get(id=user_id)
    except User.DoesNotExist:
        request.session.flush()
        return None


def user_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not get_current_user(request):
            messages.warning(request, 'Please login to continue.')
            return redirect('login')
        return view_func(request, *args, **kwargs)

    return wrapper


def admin_login_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get(ADMIN_SESSION_KEY):
            messages.warning(request, 'Please login as admin to continue.')
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)

    return wrapper


def home(request):
    return render(request, 'home.html')


def register_view(request):
    if get_current_user(request):
        return redirect('profile')

    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            request.session.flush()
            request.session[USER_SESSION_ID] = user.id
            request.session[USER_SESSION_NAME] = user.full_name
            messages.success(request, 'Registration successful. You are now logged in.')
            return redirect('profile')
    else:
        form = RegisterForm()

    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if get_current_user(request):
        return redirect('profile')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user = User.objects.get(email__iexact=email)
            except User.DoesNotExist:
                form.add_error(None, 'Invalid email or password.')
            else:
                if password_matches(password, user.password):
                    request.session.flush()
                    request.session[USER_SESSION_ID] = user.id
                    request.session[USER_SESSION_NAME] = user.full_name

                    if user.must_change_password:
                        messages.warning(request, 'Please change your temporary password.')
                        return redirect('profile')

                    messages.success(request, f'Welcome back, {user.full_name}.')
                    next_url = request.GET.get('next')
                    return redirect(next_url or 'profile')
                form.add_error(None, 'Invalid email or password.')
    else:
        form = LoginForm()

    return render(request, 'auth/login.html', {'form': form})


def logout_view(request):
    request.session.pop(USER_SESSION_ID, None)
    request.session.pop(USER_SESSION_NAME, None)
    messages.info(request, 'You have been logged out.')
    return redirect('login')


def generate_temporary_password(length=10):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            user = User.objects.get(email__iexact=email)

            temporary_password = generate_temporary_password()

            user.password = make_password(temporary_password)
            user.must_change_password = True
            user.save(update_fields=['password', 'must_change_password'])

            malaysia_time = timezone.now().astimezone(ZoneInfo('Asia/Kuala_Lumpur'))
            reset_time = malaysia_time.strftime('%d %b %Y, %I:%M %p')

            send_mail(
                subject='CampusEventHub Temporary Password',
                message=(
                    f'Hello {user.full_name},\n\n'
                    f'Your temporary password is: {temporary_password}\n\n'
                    f'Reset requested at: {reset_time} Malaysia Time\n\n'
                    f'Please login using this temporary password and change your password immediately.'
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            messages.success(
                request,
                'A temporary password has been sent to your registered email address.'
            )
            return redirect('login')

    else:
        form = ForgotPasswordForm()

    return render(request, 'auth/forgot_password.html', {'form': form})


@user_login_required
def profile_view(request):
    user = get_current_user(request)

    registrations = (
        Registration.objects.select_related('event')
        .filter(user=user)
        .order_by('-registered_at')
    )

    active_tab = 'password' if user.must_change_password else 'profile'

    if request.method == 'POST':
        form_type = request.POST.get('form_type', 'profile')

        # -----------------------------
        # Update Password Form Submit
        # -----------------------------
        if form_type == 'password':
            active_tab = 'password'

            form = ProfileUpdateForm(instance=user)
            password_form = PasswordUpdateForm(request.POST, current_user=user)

            if password_form.is_valid():
                password_form.save()

                user.must_change_password = False
                user.save(update_fields=['must_change_password'])

                messages.success(request, 'Password updated successfully.')
                return redirect('profile')

        # -----------------------------
        # Update Profile Form Submit
        # -----------------------------
        else:
            active_tab = 'profile'

            old_picture_name = user.profile_picture.name if user.profile_picture else None
            old_picture_storage = user.profile_picture.storage if user.profile_picture else None

            form = ProfileUpdateForm(
                request.POST,
                request.FILES,
                instance=user,
            )

            password_form = PasswordUpdateForm(current_user=user)

            if form.is_valid():
                remove_picture = form.cleaned_data.get('remove_profile_picture')
                new_picture_uploaded = bool(request.FILES.get('profile_picture'))

                updated_user = form.save(commit=False)

                if remove_picture:
                    updated_user.profile_picture = None

                updated_user.save()

                # Delete old image file when removed or replaced
                if old_picture_name and old_picture_storage:
                    current_picture_name = (
                        updated_user.profile_picture.name
                        if updated_user.profile_picture
                        else None
                    )

                    if remove_picture or (
                        new_picture_uploaded and old_picture_name != current_picture_name
                    ):
                        old_picture_storage.delete(old_picture_name)

                request.session[USER_SESSION_NAME] = updated_user.full_name
                messages.success(request, 'Profile updated successfully.')
                return redirect('profile')

    else:
        form = ProfileUpdateForm(instance=user)
        password_form = PasswordUpdateForm(current_user=user)

    return render(request, 'user/profile.html', {
        'form': form,
        'password_form': password_form,
        'profile_user': user,
        'registrations': registrations,
        'active_tab': active_tab,
    })

def admin_login_view(request):
    if request.session.get(ADMIN_SESSION_KEY):
        return redirect('admin_dashboard')

    if request.method == 'POST':
        form = AdminLoginForm(request.POST)
        if form.is_valid():
            request.session.flush()
            request.session[ADMIN_SESSION_KEY] = True
            request.session['admin_email'] = settings.CUSTOM_ADMIN_EMAIL
            messages.success(request, 'Admin login successful.')
            return redirect('admin_dashboard')
    else:
        form = AdminLoginForm()

    return render(request, 'auth/admin_login.html', {
        'form': form,
        'admin_email': settings.CUSTOM_ADMIN_EMAIL,
        'admin_password': settings.CUSTOM_ADMIN_PASSWORD,
    })


def admin_logout_view(request):
    request.session.pop(ADMIN_SESSION_KEY, None)
    request.session.pop('admin_email', None)
    messages.info(request, 'Admin has been logged out.')
    return redirect('admin_login')


# Admin/event views are kept in this existing core app so other members can merge safely.
@admin_login_required
def admin_event_list_view(request):
    events = Event.objects.all().order_by('-created_at')
    return render(request, 'admin_event_list.html', {'events': events})


@admin_login_required
def add_event_view(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return redirect('admin_event_list')
    else:
        form = EventForm()

    return render(request, 'event_form.html', {'form': form, 'title': 'Add New Event'})


@admin_login_required
def edit_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)

        if form.is_valid():
            form.save()
            return redirect('admin_event_list')
    else:
        form = EventForm(instance=event)

    return render(request, 'event_form.html', {'form': form, 'title': 'Edit Event'})


@admin_login_required
def delete_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    return redirect('admin_event_list')


@admin_login_required
def admin_dashboard_view(request):
    events = Event.objects.all().order_by('-created_at')[:5]
    all_events = Event.objects.all()
    total_events = all_events.count()
    open_events = all_events.filter(status='Open').count()
    total_registered = Registration.objects.count()
    full_events = sum(1 for event in all_events if event.is_full())

    return render(request, 'admin_dashboard.html', {
        'events': events,
        'total_events': total_events,
        'open_events': open_events,
        'total_registered': total_registered,
        'full_events': full_events,
    })


@admin_login_required
def admin_event_monitoring_view(request):
    events = Event.objects.all().order_by('event_date', 'event_time')
    return render(request, 'admin_event_monitoring.html', {'events': events})


@user_login_required
def my_events_view(request):
    user = get_current_user(request)
    registrations = (
        Registration.objects.select_related('event')
        .filter(user=user)
        .order_by('-registered_at')
    )
    return render(request, 'events/my_events.html', {'registrations': registrations})


def test(request):
    return redirect('login')
