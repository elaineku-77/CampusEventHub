from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from .models import Event
from .forms import EventForm


PUBLISHED_STATUSES = ["Open", "Closed"]


def _published_events():
    """
    Member 2 helper:
    Show events that are visible to users.
    If your team later adds Draft/Hidden statuses, this keeps user pages clean.
    """
    return Event.objects.filter(status__in=PUBLISHED_STATUSES)


def _add_availability(event):
    """
    Adds display-only values to each event object.
    No database migration needed.
    """
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



# -----Member 2: User event pages (Kirthika)-----

def home(request):
    latest_events = _prepare_events(
        _published_events().order_by("-created_at")[:6]
    )

    trending_events = _prepare_events(
        _published_events().order_by("event_date", "event_time")[:6]
    )

    return render(
        request,
        "home.html",
        {
            "latest_events": latest_events,
            "trending_events": trending_events,
            "categories": Event.CATEGORY_CHOICES,
        },
    )


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
        events = sorted(events, key=lambda event: event.seats_left_count, reverse=True)

    return render(
        request,
        "events/event_list.html",
        {
            "events": events,
            "query": query,
            "category_filter": category_filter,
            "sort_by": sort_by,
            "categories": Event.CATEGORY_CHOICES,
            "results_count": len(events),
        },
    )


def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event = _add_availability(event)

    return render(
        request,
        "events/event_detail.html",
        {
            "event": event,
        },
    )


# -----Existing admin/event CRUD (Elainee)-----

def admin_event_list_view(request):
    events = Event.objects.all().order_by("-created_at")
    return render(request, "admin_event_list.html", {"events": events})


def add_event_view(request):
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect("admin_event_list")
    else:
        form = EventForm()

    return render(request, "event_form.html", {"form": form, "title": "Add New Event"})


def edit_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            return redirect("admin_event_list")
    else:
        form = EventForm(instance=event)

    return render(request, "event_form.html", {"form": form, "title": "Edit Event"})


def delete_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    return redirect("admin_event_list")


def admin_dashboard_view(request):
    return render(request, "admin_dashboard.html")


def admin_event_monitoring_view(request):
    return render(request, "admin_event_monitoring.html")


def test(request):
    return render(request, "test.html")