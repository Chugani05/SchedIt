from django import forms

from .models import Appointment


class AddAppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = (
            'date',
            'slot',
        )
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def save(self, *args, **kwargs):
        appointment = super().save(commit=False)
        appointment.user = self.user
        appointment = super().save(*args, **kwargs)
        return appointment
