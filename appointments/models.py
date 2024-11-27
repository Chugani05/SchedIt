from django.conf import settings
from django.db import models


class Appointment(models.Model):
    date = models.DateField()
    slot = models.ForeignKey('slots.Slot', on_delete=models.CASCADE, related_name='slot')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='echos'
    )

    class Meta:
        unique_together = [ 'date', 'slot' ]
        ordering = [ 'date', 'slot' ]
