import pandas as pd

from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from django.utils.dateparse import parse_date, parse_time

from .models import User, Event, Registration
from .forms import EventExcelUploadForm


admin.site.register(User)
admin.site.register(Registration)


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "event_date",
        "event_time",
        "venue",
        "max_participants",
        "status",
        "is_highlighted",
    )

    list_filter = ("category", "status", "is_highlighted")
    search_fields = ("title", "description", "venue")

    change_list_template = "events/change_list.html"

    def get_urls(self):
        urls = super().get_urls()

        custom_urls = [
            path(
                "upload-excel/",
                self.admin_site.admin_view(self.upload_excel),
                name="core_event_upload_excel",
            ),
        ]

        return custom_urls + urls

    def upload_excel(self, request):
        if request.method == "POST":
            form = EventExcelUploadForm(request.POST, request.FILES)

            if form.is_valid():
                excel_file = request.FILES["excel_file"]

                try:
                    df = pd.read_excel(excel_file)

                    required_columns = [
                        "title",
                        "description",
                        "category",
                        "event_date",
                        "event_time",
                        "venue",
                        "max_participants",
                        "status",
                        "is_highlighted",
                        "event_image",
                    ]

                    missing_columns = [
                        col for col in required_columns if col not in df.columns
                    ]

                    if missing_columns:
                        messages.error(
                            request,
                            f"Missing Excel columns: {', '.join(missing_columns)}",
                        )
                        return redirect(".")

                    valid_categories = [
                        "Workshop",
                        "Seminar",
                        "Social",
                        "Sports",
                        "Technology",
                        "Arts",
                    ]

                    valid_statuses = ["Open", "Closed"]

                    created_count = 0
                    skipped_rows = []

                    for index, row in df.iterrows():
                        try:
                            title = str(row["title"]).strip()
                            description = str(row["description"]).strip()
                            category = str(row["category"]).strip()
                            venue = str(row["venue"]).strip()
                            status = str(row["status"]).strip()

                            if category not in valid_categories:
                                raise ValueError(
                                    f"Invalid category '{category}'. "
                                    f"Use one of: {', '.join(valid_categories)}"
                                )

                            if status not in valid_statuses:
                                raise ValueError(
                                    f"Invalid status '{status}'. Use Open or Closed."
                                )

                            event_date_value = row["event_date"]

                            if hasattr(event_date_value, "date"):
                                event_date = event_date_value.date()
                            else:
                                event_date = parse_date(str(event_date_value))

                            if event_date is None:
                                raise ValueError("Invalid event_date format")

                            event_time_value = row["event_time"]

                            if hasattr(event_time_value, "time"):
                                event_time = event_time_value.time()
                            else:
                                event_time = parse_time(str(event_time_value))

                            if event_time is None:
                                raise ValueError("Invalid event_time format")

                            max_participants = int(row["max_participants"])

                            highlighted_value = str(row["is_highlighted"]).strip().lower()
                            is_highlighted = highlighted_value in [
                                "true",
                                "1",
                                "yes",
                                "y",
                            ]

                            event_image = str(row["event_image"]).strip()

                            Event.objects.create(
                                title=title,
                                description=description,
                                category=category,
                                event_date=event_date,
                                event_time=event_time,
                                venue=venue,
                                max_participants=max_participants,
                                status=status,
                                is_highlighted=is_highlighted,
                                event_image=event_image,
                            )

                            created_count += 1

                        except Exception as error:
                            skipped_rows.append(
                                f"Row {index + 2}: {str(error)}"
                            )

                    if created_count:
                        messages.success(
                            request,
                            f"{created_count} events imported successfully.",
                        )

                    if skipped_rows:
                        messages.warning(
                            request,
                            "Some rows were skipped: " + " | ".join(skipped_rows[:10]),
                        )

                    return redirect("../")

                except Exception as error:
                    messages.error(request, f"Excel import failed: {str(error)}")
                    return redirect(".")

        else:
            form = EventExcelUploadForm()

        return render(
            request,
            "events/upload_excel.html",
            {
                "form": form,
                "title": "Upload Events from Excel",
            },
        )