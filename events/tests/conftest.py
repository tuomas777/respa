import pytest
from resources.tests.conftest import (space_resource_type, resource_in_unit, terms_of_use, test_unit, user,
                                      user_api_client)
from resources.tests.test_reservation_api import reservation
from events.models import Event, EventParticipant


@pytest.fixture()
def event(resource_in_unit, reservation, user):
    event = Event.objects.create(
        reservation=reservation,
        name='test event',
        number_of_participants=10,
    )

    EventParticipant.objects.create(
        event=event,
        first_name='Patrick',
        last_name='Participant',
        email='papa@albert.fi',
    )

    EventParticipant.objects.create(
        event=event,
        user=user
    )

    return event
