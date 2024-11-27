from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from .forms import AddAppointmentForm
from .models import Appointment
from .utils import check_owner


@login_required
def appointment_list(request: HttpRequest) -> HttpResponse:
    appointments = Appointment.objects.filter(user=request.user)
    return render(request, 'appointments/appointment_list.html', dict(appointments=appointments))


@login_required
@check_owner
def appointment_detail(request: HttpRequest, appointment_pk: int) -> HttpResponse:
    appointment = Appointment.objects.get(pk=appointment_pk)
    return render(request, 'appointments/appointment_detail.html', dict(appointment=appointment))


@login_required
def add_appointment(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        if (form := AddAppointmentForm(request.user, request.POST)).is_valid():
            appointment = form.save()
            return redirect('appointments:appointment-list')
    else:
        form = AddAppointmentForm(request.user)
    return render(request, 'appointments/add_appointment.html', dict(form=form))
