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
from django.db.models import Q
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

PUBLISHED_STATUSES = ["Open", "Closed"]


# ── Session helpers ──────────────────────────────────────────────────────────

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


# ── Member 2: Event availability helpers ────────────────────────────────────

def _published_events():
    return Event.objects.filter(status__in=PUBLISHED_STATUSES)


def _add_availability(event):
    registered_count = event.registration_set.count()
    seats_left = max(event.max_participants - registered_count, 0)

    event.registered_count = registered_count
    event.seats_left_count = seats_left
    event.can_register = event.status == "Open" and seats_left > 0

    if event.status != "Open":
        event.availability_label = "Closed"
        event.availability_class = "closed"
    elif seats_left <= 0:
        event.availability_label = "Full"
        event.availability_class = "full"
    elif seats_left <= 5:
        seat_word = "seat" if seats_left == 1 else "seats"
        event.availability_label = f"{seats_left} {seat_word} left"
        event.availability_class = "limited"
    else:
        event.availability_label = "Open"
        event.availability_class = "open"

    return event


def _prepare_events(events):
    return [_add_availability(event) for event in events]


# ── Public event pages ───────────────────────────────────────────────────────

def home(request):
    latest_events = _prepare_events(
        _published_events().order_by("-created_at")[:6]
    )
    trending_events = _prepare_events(
        _published_events().order_by("event_date", "event_time")[:6]
    )
    return render(request, "home.html", {
        "latest_events": latest_events,
        "trending_events": trending_events,
        "categories": Event.CATEGORY_CHOICES,
        "current_user": get_current_user(request),
    })


def event_list(request):
    query = request.GET.get("q", "").strip()
    category_filter = request.GET.get("category", "").strip()
    sort_by = request.GET.get("sort", "latest").strip()

    if sort_by not in ["latest", "date", "seats"]:
        sort_by = "latest"

    events_qs = _published_events()

    if query:
        events_qs = events_qs.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(category__icontains=query)
            | Q(venue__icontains=query)
        )

    if category_filter:
        events_qs = events_qs.filter(category=category_filter)

    if sort_by == "date":
        events_qs = events_qs.order_by("event_date", "event_time")
    else:
        events_qs = events_qs.order_by("-created_at")

    events = _prepare_events(events_qs)

    if sort_by == "seats":
        events = sorted(events, key=lambda e: e.seats_left_count, reverse=True)

    return render(request, "events/event_list.html", {
        "events": events,
        "query": query,
        "category_filter": category_filter,
        "sort_by": sort_by,
        "categories": Event.CATEGORY_CHOICES,
        "results_count": len(events),
        "current_user": get_current_user(request),
    })


def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event = _add_availability(event)
    current_user = get_current_user(request)

    # Check if already registered
    already_registered = False
    if current_user:
        already_registered = Registration.objects.filter(
            user=current_user, event=event
        ).exists()

    return render(request, "events/event_detail.html", {
        "event": event,
        "current_user": current_user,
        "already_registered": already_registered,
    })


# ── Register event ───────────────────────────────────────────────────────────

@user_login_required
def register_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    current_user = get_current_user(request)

    # Already registered
    if Registration.objects.filter(user=current_user, event=event).exists():
        messages.info(request, f'You are already registered for "{event.title}".')
        return redirect('event_detail', event_id=event_id)

    # Check availability
    if event.status != "Open":
        messages.error(request, 'Registration is closed for this event.')
        return redirect('event_detail', event_id=event_id)

    if event.is_full():
        messages.error(request, 'This event is full.')
        return redirect('event_detail', event_id=event_id)

    # Register
    Registration.objects.create(user=current_user, event=event)
    messages.success(request, f'You have successfully registered for "{event.title}"!')
    return redirect('my_events')


# ── Auth views ───────────────────────────────────────────────────────────────

def register_view(request):
    if get_current_user(request):
        return redirect('profile')

    if request.method == 'POST':
        form = RegisterForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            # CHANGE 1: After signup, redirect to login instead of auto-login
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('login')
    else:
        form = RegisterForm()

    return render(request, 'auth/register.html', {'form': form})


def login_view(request):
    if get_current_user(request):
        return redirect('home')

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
                    return redirect(next_url or 'home')
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

            messages.success(request, 'A temporary password has been sent to your registered email address.')
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
        else:
            active_tab = 'profile'
            old_picture_name = user.profile_picture.name if user.profile_picture else None
            old_picture_storage = user.profile_picture.storage if user.profile_picture else None

            form = ProfileUpdateForm(request.POST, request.FILES, instance=user)
            password_form = PasswordUpdateForm(current_user=user)

            if form.is_valid():
                remove_picture = form.cleaned_data.get('remove_profile_picture')
                new_picture_uploaded = bool(request.FILES.get('profile_picture'))
                updated_user = form.save(commit=False)

                if remove_picture:
                    updated_user.profile_picture = None

                updated_user.save()

                if old_picture_name and old_picture_storage:
                    current_picture_name = (
                        updated_user.profile_picture.name
                        if updated_user.profile_picture else None
                    )
                    if remove_picture or (new_picture_uploaded and old_picture_name != current_picture_name):
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
        'current_user': user,
    })


@user_login_required
def my_events_view(request):
    user = get_current_user(request)
    registrations = (
        Registration.objects.select_related('event')
        .filter(user=user)
        .order_by('-registered_at')
    )
    # Add availability info to each event
    for reg in registrations:
        _add_availability(reg.event)

    return render(request, 'events/my_events.html', {
        'registrations': registrations,
        'current_user': user,
    })


# ── Admin auth ───────────────────────────────────────────────────────────────

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
def admin_event_monitoring_view(request):
    query           = request.GET.get('q', '').strip()
    category_filter = request.GET.get('category', '').strip()
    status_filter   = request.GET.get('status', '').strip()

    events_qs = Event.objects.all().order_by('event_date', 'event_time')

    if query:
        events_qs = events_qs.filter(
            Q(title__icontains=query) | Q(venue__icontains=query)
        )
    if category_filter:
        events_qs = events_qs.filter(category=category_filter)
    if status_filter:
        events_qs = events_qs.filter(status=status_filter)

    all_events      = Event.objects.all()
    total_events    = all_events.count()
    open_events     = all_events.filter(status='Open').count()
    total_registered = Registration.objects.count()
    full_events     = sum(1 for e in all_events if e.is_full())

    return render(request, 'admin_event_monitoring.html', {
        'events':          events_qs,
        'query':           query,
        'category_filter': category_filter,
        'status_filter':   status_filter,
        'categories':      Event.CATEGORY_CHOICES,
        'total_events':    total_events,
        'open_events':     open_events,
        'total_registered': total_registered,
        'full_events':     full_events,
    })


def test(request):
    return redirect('login')
