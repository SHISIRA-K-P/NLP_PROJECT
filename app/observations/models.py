from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class EmergencyAuthority(models.Model):
    class AuthorityType(models.TextChoices):
        DISASTER_MANAGEMENT = 'disaster_management', 'Disaster Management'
        DISTRICT_ADMINISTRATION = 'district_administration', 'District Administration'
        POLICE = 'police', 'Police'
        FIRE_RESCUE = 'fire_rescue', 'Fire and Rescue'
        OTHER = 'other', 'Other'

    authority_name = models.CharField(max_length=200)
    authority_type = models.CharField(
        max_length=32,
        choices=AuthorityType.choices,
        default=AuthorityType.OTHER,
    )
    location_id = models.PositiveIntegerField(db_index=True)
    district = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone_number = models.CharField(max_length=32, blank=True)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(
        default=False,
        help_text='Enable only after checking this contact against an official source.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['authority_name', 'id']
        db_table = 'EmergencyAuthority'

    def __str__(self):
        return f'{self.authority_name} (location {self.location_id})'


class LandslideObservation(models.Model):
    class VegetationCover(models.TextChoices):
        LOW = 'Low', 'Low'
        MEDIUM = 'Medium', 'Medium'
        HIGH = 'High', 'High'

    class LandslideStatus(models.TextChoices):
        YES = 'Yes', 'Yes'
        NO = 'No', 'No'

    location_id = models.IntegerField(validators=[MinValueValidator(1)])
    max_temp_c = models.FloatField()
    humidity_pct = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    wind_speed_kmh = models.FloatField(validators=[MinValueValidator(0)])
    rainfall_mm = models.FloatField(validators=[MinValueValidator(0)])
    slope_angle_deg = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(90)]
    )
    vegetation_cover = models.CharField(
        max_length=6,
        choices=VegetationCover.choices,
    )
    landslide_observed = models.CharField(
        max_length=3,
        choices=LandslideStatus.choices,
        blank=True,
        null=True,
    )
    landslide_prediction = models.CharField(
        max_length=3,
        choices=LandslideStatus.choices,
        blank=True,
        null=True,
    )
    landslide_probability = models.FloatField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f'Observation {self.pk} - location {self.location_id}'


# class LandslideResponseAlert(models.Model):
#     class Status(models.TextChoices):
#         PROCESSING = 'processing', 'Processing'
#         PENDING_APPROVAL = 'pending_approval', 'Pending Approval'
#         APPROVED = 'approved', 'Approved'
#         SENT = 'sent', 'Sent'
#         PARTIALLY_SENT = 'partially_sent', 'Partially Sent'
#         FAILED = 'failed', 'Failed'

#     observation = models.OneToOneField(
#         LandslideObservation,
#         on_delete=models.CASCADE,
#         related_name='response_alert',
#     )
#     status = models.CharField(
#         max_length=24,
#         choices=Status.choices,
#         default=Status.PROCESSING,
#         db_index=True,
#     )
#     recommendation = models.TextField()
#     source_documents = models.JSONField(default=list, blank=True)
#     workflow_error = models.TextField(blank=True)
#     approved_by = models.ForeignKey(
#         settings.AUTH_USER_MODEL,
#         null=True,
#         blank=True,
#         on_delete=models.SET_NULL,
#         related_name='approved_landslide_alerts',
#     )
#     approved_at = models.DateTimeField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         ordering = ['-created_at']
#         permissions = [
#             (
#                 'approve_landslideresponsealert',
#                 'Can approve landslide response alerts',
#             )
#         ]

#     def __str__(self):
#         return f'Alert for observation {self.observation_id} ({self.status})'


# class LandslideAlertEmailAttempt(models.Model):
#     class Status(models.TextChoices):
#         PENDING = 'pending', 'Pending'
#         SENT = 'sent', 'Sent'
#         FAILED = 'failed', 'Failed'

#     alert = models.ForeignKey(
#         LandslideResponseAlert,
#         on_delete=models.CASCADE,
#         related_name='email_attempts',
#     )
#     authority = models.ForeignKey(
#         EmergencyAuthority,
#         null=True,
#         blank=True,
#         on_delete=models.SET_NULL,
#         related_name='email_attempts',
#     )
#     recipient_email = models.EmailField()
#     status = models.CharField(
#         max_length=12,
#         choices=Status.choices,
#         default=Status.PENDING,
#         db_index=True,
#     )
#     error_message = models.TextField(blank=True)
#     attempted_at = models.DateTimeField(auto_now_add=True)
#     completed_at = models.DateTimeField(null=True, blank=True)

#     class Meta:
#         ordering = ['attempted_at', 'id']

#     def __str__(self):
#         return f'Email attempt for alert {self.alert_id} ({self.status})'


# class LandslideWorkflowEvent(models.Model):
#     alert = models.ForeignKey(
#         LandslideResponseAlert,
#         on_delete=models.CASCADE,
#         related_name='workflow_events',
#     )
#     event_type = models.CharField(max_length=64, db_index=True)
#     status = models.CharField(max_length=24)
#     details = models.JSONField(default=dict, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True, db_index=True)

#     class Meta:
#         ordering = ['created_at', 'id']

#     def __str__(self):
#         return f'{self.event_type} for alert {self.alert_id}'
