from django.shortcuts import render, redirect, get_object_or_404
from .models import Event
from .forms import EventForm

def admin_event_list_view(request):
    events = Event.objects.all().order_by('-created_at')
    return render(request, 'admin_event_list.html', {'events': events})


def add_event_view(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)

        if form.is_valid():
            form.save()
            return redirect('admin_event_list')
    else:
        form = EventForm()

    return render(request, 'event_form.html', {'form': form, 'title': 'Add New Event'})


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


def delete_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.delete()
    return redirect('admin_event_list')

def admin_dashboard_view(request):
    return render(request, 'admin_dashboard.html')

def admin_event_monitoring_view(request):
    selected_category = request.GET.get('category')

    events = [
        {
            'name': 'Event A',
            'date': '23-24 Jun 2026',
            'time': '9.30am-2.00pm',
            'registered': 80,
            'category': 'workshop',
            'category_name': 'Workshop',
            'status': 'Open'
        },
        {
            'name': 'Event B',
            'date': '21 Aug 2026',
            'time': '9.00am-12.00pm',
            'registered': 40,
            'category': 'seminar',
            'category_name': 'Seminar',
            'status': 'Open'
        },
        {
            'name': 'Event C',
            'date': '18-20 Sep 2026',
            'time': '7.00pm-10.00pm',
            'registered': 120,
            'category': 'social',
            'category_name': 'Social',
            'status': 'Full'
        },
        {
            'name': 'Event D',
            'date': '21 Aug 2026',
            'time': '10.00am-4.00pm',
            'registered': 40,
            'category': 'sports-fitness',
            'category_name': 'Sports & Fitness',
            'status': 'Open'
        },
        {
            'name': 'Event E',
            'date': '18-20 Sep 2026',
            'time': '10.00am-2.00pm',
            'registered': 150,
            'category': 'technology-innovation',
            'category_name': 'Technology & Innovation',
            'status': 'Full'
        },
        {
            'name': 'Event F',
            'date': '10 Oct 2026',
            'time': '3.00pm-6.00pm',
            'registered': 60,
            'category': 'arts',
            'category_name': 'Arts',
            'status': 'Open'
        },
    ]

    categories = [
        {'code': 'workshop', 'name': 'Workshop'},
        {'code': 'seminar', 'name': 'Seminar'},
        {'code': 'social', 'name': 'Social'},
        {'code': 'sports-fitness', 'name': 'Sports & Fitness'},
        {'code': 'technology-innovation', 'name': 'Technology & Innovation'},
        {'code': 'arts', 'name': 'Arts'},
    ]

    if selected_category:
        events = [
            event for event in events
            if event['category'] == selected_category
        ]

    return render(request, 'admin_event_monitoring.html', {
        'events': events,
        'categories': categories,
        'selected_category': selected_category
    })

def home(request):
    return render(request, 'home.html')

def test(request):
    return render(request, 'test.html')
    