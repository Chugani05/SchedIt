from django.http import HttpResponseForbidden

from .models import Appointment


def check_owner(func):
    def wrapper(*args, **kwargs):
        appointment = Appointment.objects.get(pk=kwargs['appointment_pk'])
        if appointment.user != args[0].user:
            return HttpResponseForbidden('Forbidden')
        return func(*args, **kwargs)

    return wrapper
