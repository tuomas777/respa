from django.db import transaction
from rest_framework import serializers, viewsets
from resources.api.base import TranslatedModelSerializer
from resources.api.reservation import ReservationSerializer, ReservationViewSet
from users.models import User
from .models import Event, EventParticipant


class EventParticipantSerializer(TranslatedModelSerializer):
    user = serializers.SlugRelatedField(slug_field='uuid', queryset=User.objects.all(), required=False)

    class Meta:
        model = EventParticipant
        fields = ('first_name', 'last_name', 'email', 'user')

    def to_internal_value(self, data):
        if 'user' in data:
            data['email'] = 'temp-value-to-bypass-field-required-check@foo.bar'
        return super().to_internal_value(data)


class EventParticipantViewSet(viewsets.ModelViewSet):
    serializer_class = EventParticipantSerializer
    queryset = EventParticipant.objects.all()


class EventSerializer(TranslatedModelSerializer):
    participants = EventParticipantSerializer(many=True, required=False)

    class Meta:
        model = Event
        fields = ('name', 'number_of_participants', 'participants')


class EventReservationSerializer(ReservationSerializer):
    event = EventSerializer()

    class Meta(ReservationSerializer.Meta):
        fields = ReservationSerializer.Meta.fields + ['event']

    def validate(self, data):
        event_data = data.pop('event')
        validated_data = super().validate(data)
        validated_data['event'] = event_data
        return validated_data

    @staticmethod
    def _handle_event(instance, event_data):
        participants_data = event_data.pop('participants', [])

        event, created = Event.objects.update_or_create(
            reservation=instance,
            defaults=event_data
        )

        event.participants.all().delete()

        for participant_data in participants_data:
            EventParticipant.objects.create(
                event=event,
                **participant_data
            )

    @transaction.atomic()
    def create(self, validated_data):
        event_data = validated_data.pop('event')
        instance = super().create(validated_data)
        self._handle_event(instance, event_data)
        return instance

    @transaction.atomic()
    def update(self, instance, validated_data):
        event_data = validated_data.pop('event')
        instance = super().update(instance, validated_data)
        self._handle_event(instance, event_data)
        return instance


class EventReservationViewSet(ReservationViewSet):
    serializer_class = EventReservationSerializer
