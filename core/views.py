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
    return render(request, 'admin_event_monitoring.html')

def home(request):
    return render(request, 'home.html')

def test(request):
    return render(request, 'test.html')
    