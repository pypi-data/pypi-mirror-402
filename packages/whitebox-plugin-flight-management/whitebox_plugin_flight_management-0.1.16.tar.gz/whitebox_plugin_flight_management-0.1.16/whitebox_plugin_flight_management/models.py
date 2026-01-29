from pathlib import Path

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone

from whitebox import settings
from whitebox.templatetags.whitebox import tagged_url, tagged_media


class TimestampBasedLifecycleQuerySet(models.QuerySet):
    def active(self):
        return self.filter(ended_at__isnull=True)

    def current(self):
        return self.active().first()

    async def acurrent(self):
        return await self.active().afirst()


class FlightSession(models.Model):
    name = models.CharField(max_length=128)

    # Flight plan data
    # Each location is a dict with: {name: str, icao: str, coordinates: [str, str]}
    takeoff_location = models.JSONField(default=dict, blank=True)
    arrival_location = models.JSONField(default=dict, blank=True)
    # Waypoints is a list of dicts with: {id: str, name: str, icao: str, coordinates: [str, str]}
    waypoints = models.JSONField(default=list, blank=True)

    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)

    objects = TimestampBasedLifecycleQuerySet.as_manager()

    @property
    def is_active(self):
        return self.ended_at is None


class FlightSessionRecordingStatus(models.IntegerChoices):
    CREATED = 10
    RECORDING = 20
    PROCESSING = 30
    READY = 50


class FlightSessionRecording(models.Model):
    STATUSES = FlightSessionRecordingStatus

    flight_session = models.ForeignKey(
        FlightSession,
        on_delete=models.CASCADE,
        related_name="recordings",
    )
    provided_by_ct = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
    )
    provided_by_id = models.IntegerField(null=True)
    provided_by = GenericForeignKey("provided_by_ct", "provided_by_id")

    file = models.FileField()
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    status = models.IntegerField(
        choices=FlightSessionRecordingStatus.choices,
        default=FlightSessionRecordingStatus.CREATED,
    )

    def get_provider(self):
        # We do not want to fetch `self.provided_by` here to allow higher
        # portability between sync and async code, hence we're getting the
        # model name through the dance below
        if not self.provided_by_ct_id or not self.provided_by_id:
            return None

        provided_by_ct = ContentType.objects.get_for_id(self.provided_by_ct_id)
        provided_by = provided_by_ct.model_class()
        return provided_by._meta.model_name

    def get_file_url(self):
        path = self.file.path

        if (
            path.startswith("http://")
            or path.startswith("https://")
            or path.startswith("ftp://")
        ):
            return path

        # In case of absolute paths, we first need to find it within the media
        # root folder
        if path.startswith("/"):
            path = Path(path).relative_to(settings.MEDIA_ROOT)

        return tagged_media(path)


class KeyMoment(models.Model):
    flight_session = models.ForeignKey(
        FlightSession,
        on_delete=models.CASCADE,
        related_name="key_moments",
    )

    name = models.CharField(max_length=128)

    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)

    objects = TimestampBasedLifecycleQuerySet.as_manager()

    class Meta:
        ordering = ["started_at"]

    @property
    def is_active(self):
        return self.ended_at is None
