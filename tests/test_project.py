import datetime

import pytest
from django.conf import settings
from django.db.utils import IntegrityError
from faker import Faker
from model_bakery import baker, seq
from pytest_django.asserts import assertContains, assertRedirects

from appointments.models import Appointment
from slots.models import Slot

# ==============================================================================
# FIXTURES
# ==============================================================================


@pytest.fixture
def user(django_user_model):
    return baker.make(django_user_model, _fill_optional=True)


@pytest.fixture
def appointment():
    return baker.make(Appointment, _fill_optional=True)


@pytest.fixture
def slot():
    return baker.make(Slot, _fill_optional=True)


@pytest.fixture
def fake():
    return Faker()


@pytest.fixture
def login_data(fake):
    return {
        'username': fake.user_name(),
        'password': fake.password(),
    }


@pytest.fixture
def signup_data(fake):
    return {
        'username': fake.user_name(),
        'password': fake.password(),
        'first_name': fake.first_name(),
        'last_name': fake.last_name(),
        'email': fake.email(),
    }


# ==============================================================================
# TESTS
# ==============================================================================


def test_required_apps_are_installed():
    PROPER_APPS = ('appointments', 'slots', 'accounts')

    custom_apps = [app for app in settings.INSTALLED_APPS if not app.startswith('django')]
    for app in PROPER_APPS:
        app_config = f'{app}.apps.{app.title()}Config'
        assert (
            app_config in custom_apps
        ), f'La aplicación <{app}> no está "creada/instalada" en el proyecto.'
    assert len(custom_apps) >= len(
        PROPER_APPS
    ), 'El número de aplicaciones propias definidas en el proyecto no es correcto.'


@pytest.mark.django_db
def test_slot_model_has_proper_fields(slot):
    PROPER_FIELDS = ('start_at', 'end_at')
    for field in PROPER_FIELDS:
        assert getattr(slot, field) is not None, f'El campo <{field}> no está en el modelo Slot.'


@pytest.mark.django_db
def test_slot_model_has_unique_restrictions():
    with pytest.raises(IntegrityError):
        baker.make(Slot, start_at=datetime.time(0, 0), end_at=datetime.time(0, 0), _quantity=2)


@pytest.mark.django_db
def test_appointment_model_has_proper_fields(appointment):
    PROPER_FIELDS = ('user', 'date', 'slot')
    for field in PROPER_FIELDS:
        assert (
            getattr(appointment, field) is not None
        ), f'El campo <{field}> no está en el modelo Appointment.'


@pytest.mark.django_db
def test_appointment_model_has_unique_restrictions(slot):
    with pytest.raises(IntegrityError):
        baker.make(Appointment, slot=slot, _quantity=2)  # same date/same slot


@pytest.mark.django_db
def test_get_login_works(client):
    response = client.get('/login/')
    assert response.status_code == 200


@pytest.mark.django_db
def test_post_login_works(client, login_data, django_user_model):
    REDIRECT_URL = '/appointments/'

    django_user_model.objects.create_user(
        username=login_data['username'], password=login_data['password']
    )
    response = client.post(
        '/login/',
        dict(username=login_data['username'], password=login_data['password'], next=REDIRECT_URL),
    )
    assertRedirects(response, REDIRECT_URL)


@pytest.mark.django_db
def test_post_login_fails(client, login_data, django_user_model):
    django_user_model.objects.create_user(
        username=login_data['username'], password=login_data['password']
    )
    response = client.post(
        '/login/', dict(username=login_data['username'], password=login_data['password'] + 'pytest')
    )
    assert response.status_code == 200
    assertContains(response, 'username')
    assertContains(response, 'password')


@pytest.mark.django_db
def test_logout(client, user):
    client.force_login(user)
    client.get('/logout/')
    # https://stackoverflow.com/a/6013115
    assert '_auth_user_id' not in client.session, 'El usuario sigue logeado tras hacer "logout".'


@pytest.mark.django_db
def test_get_signup_works(client, signup_data):
    response = client.get('/signup/')
    assert response.status_code == 200
    for field in signup_data.keys():
        assertContains(response, field)


@pytest.mark.django_db
def test_post_signup_fails_when_no_username_provided(client, signup_data):
    payload = signup_data.copy()
    payload.pop('username')
    response = client.post('/signup/', payload)
    assert response.status_code == 200
    assertContains(response, 'error')
    for field in signup_data.keys():
        assertContains(response, field)


@pytest.mark.django_db
def test_post_signup_fails_when_no_password_provided(client, signup_data):
    payload = signup_data.copy()
    payload.pop('password')
    response = client.post('/signup/', payload)
    assert response.status_code == 200
    assertContains(response, 'error')
    for field in signup_data.keys():
        assertContains(response, field)


@pytest.mark.django_db
def test_post_signup_fails_when_user_already_exists(client, user, signup_data):
    payload = signup_data.copy()
    payload['username'] = user.username
    response = client.post('/signup/', payload)
    assert response.status_code == 200
    assertContains(response, 'error')
    for field in signup_data.keys():
        assertContains(response, field)


@pytest.mark.django_db
def test_post_signup_works(client, signup_data):
    REDIRECT_URL = '/appointments/'

    response = client.post('/signup/', signup_data)
    assertRedirects(response, REDIRECT_URL)


@pytest.mark.django_db
def test_root_url_redirects_to_appointment_list(client, user):
    REDIRECT_URL = '/appointments/'

    response = client.get('/', follow=True)
    assertRedirects(response, f'/login/?next={REDIRECT_URL}')
    client.force_login(user)
    response = client.get('/')
    assertRedirects(response, REDIRECT_URL)


@pytest.mark.django_db
def test_slot_str():
    slot = Slot(start_at=datetime.time(7, 15), end_at=datetime.time(10, 20))
    assert str(slot) == '07:15 - 10:20'


@pytest.mark.django_db
def test_appointment_str(user):
    slot = Slot(start_at=datetime.time(7, 15), end_at=datetime.time(10, 20))
    appointment = Appointment(user=user, date=datetime.date(2024, 11, 14), slot=slot)
    assert str(appointment) == '2024-11-14 (07:15 - 10:20)'


@pytest.mark.django_db
def test_appointment_list(client, user):
    NUM_APPOINTMENTS = 10

    client.force_login(user)
    appointments = baker.make(
        Appointment,
        user=user,
        date=seq(datetime.date.today(), datetime.timedelta(days=1)),
        _fill_optional=True,
        _quantity=NUM_APPOINTMENTS,
    )
    response = client.get('/appointments/')
    assert response.status_code == 200
    assert (
        'appointments' in response.context
    ), 'Se espera que las citas se pasen al contexto de la plantilla como "appointments".'
    assert (
        list(response.context['appointments']) == appointments
    ), 'El orden de las citas no es el correcto.'
    # Comprueba que las citas aparecen en HTML con el formato correcto
    for appointment in appointments:
        assertContains(response, str(appointment))


@pytest.mark.django_db
def test_appointment_detail(client, user):
    appointment = baker.make(Appointment, user=user)
    url = f'/appointments/{appointment.pk}/'
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertContains(response, f'Date: {appointment.date}')
    assertContains(response, f'Slot: {appointment.slot}')


@pytest.mark.django_db
def test_appointment_detail_is_forbidden_for_non_owner_user(client, django_user_model):
    user1 = baker.make(django_user_model, username='test1')
    user2 = baker.make(django_user_model, username='test2')
    appointment = baker.make(Appointment, user=user1)
    client.force_login(user2)
    url = f'/appointments/{appointment.pk}/'
    response = client.get(url)
    assert response.status_code == 403


@pytest.mark.django_db
def test_appointment_detail_has_link_to_all_appointments(client, user):
    appointment = baker.make(Appointment, user=user)
    url = f'/appointments/{appointment.pk}/'
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assertContains(response, 'href="/appointments/"')


@pytest.mark.django_db
def test_add_appointment_with_get_method(client, user):
    URL = '/appointments/add/'
    client.force_login(user)
    response = client.get(URL)
    assert response.status_code == 200
    assert (
        'form' in response.context
    ), 'Se espera que el formulario se pase al contexto de la plantilla como "form"'
    assert (
        'date' in response.context['form'].fields.keys()
    ), 'No se encuentra el campo "date" en el formulario'
    assert (
        'slot' in response.context['form'].fields.keys()
    ), 'No se encuentra el campo "slot" en el formulario'


@pytest.mark.django_db
def test_login_required(client):
    TEST_URLS = ['/appointments/', '/appointments/1/', '/appointments/add/']
    REDIRECT_URL = '/login/?next={url}'

    for test_url in TEST_URLS:
        response = client.get(test_url, follow=True)
        redirect_url = REDIRECT_URL.format(url=test_url)
        assertRedirects(response, redirect_url)


@pytest.mark.django_db
def test_models_are_available_on_admin(admin_client):
    MODELS = ('appointments.Appointment', 'slots.Slot')

    for model in MODELS:
        url_model_path = model.replace('.', '/').lower()
        url = f'/admin/{url_model_path}/'
        response = admin_client.get(url)
        assert response.status_code == 200, f'El modelo <{model}> no está habilitado en el admin.'
