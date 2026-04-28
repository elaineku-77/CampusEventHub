from django.db import models


class User(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class Event(models.Model):
    CATEGORY_CHOICES = [
        ('Workshop', 'Workshop'),
        ('Seminar', 'Seminar'),
        ('Social', 'Social'),
        ('Sports', 'Sports & Fitness'),
        ('Technology', 'Technology'),
        ('Arts', 'Arts'),
    ]

    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Closed', 'Closed'),
    ]

    title = models.CharField(max_length=150)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    event_date = models.DateField()
    event_time = models.TimeField()
    venue = models.CharField(max_length=150)
    max_participants = models.PositiveIntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Open')
    event_image = models.ImageField(upload_to='event_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def registration_count(self):
        return self.registration_set.count()

    def seats_left(self):
        return self.max_participants - self.registration_set.count()

    def is_full(self):
        return self.seats_left() <= 0

    def __str__(self):
        return self.title


class Registration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')

    def __str__(self):
        return f"{self.user.full_name} - {self.event.title}"