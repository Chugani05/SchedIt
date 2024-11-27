from django.db import models

class Slot(models.Model):
    start_at = models.TimeField()
    end_at = models.TimeField()

    class Meta:
        unique_together = [ 'start_at', 'end_at' ]
        ordering = [ 'start_at', 'end_at' ]

    def __str__(self):
        return f'{self.start_at} - {self.end_at}'