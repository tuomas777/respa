import pytest
from resources.tests.test_reservation_api import reservation_data, day_and_period
from events.models import Event, EventParticipant


@pytest.mark.django_db
def test_get_event_data(event, user_api_client):
    response = user_api_client.get('/v1/reservation/%s/' % event.reservation.id, format='json')
    assert response.status_code == 200


@pytest.mark.django_db
def test_post_event(reservation_data, user_api_client, user):
    reservation_data['event'] = {
        'name': 'posted event',
        'number_of_participants': 20,
        'participants': [
            {
                'first_name': 'John',
                'last_name': 'Rambo',
                'email': 'john@ram.bo',
            },
            {
                'user': user.uuid,
            }
        ]
    }
    response = user_api_client.post('/v1/reservation/', reservation_data, format='json')
    assert response.status_code == 201

    assert Event.objects.count() == 1
    assert EventParticipant.objects.count() == 2
