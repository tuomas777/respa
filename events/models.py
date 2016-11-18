from django.db import models
from django.utils.translation import ugettext_lazy as _
from resources.models import Equipment, Reservation
from resources.models.base import AutoIdentifiedModel, ModifiableModel
from users.models import User


class Event(models.Model):
    reservation = models.OneToOneField(Reservation, verbose_name=_('Reservation'), related_name='event')
    name = models.CharField(verbose_name=_('Name'), max_length=255)
    number_of_participants = models.PositiveSmallIntegerField(verbose_name=_('Number of participants'), blank=True,
                                                              null=True)

    class Meta:
        verbose_name = _('Event')
        verbose_name_plural = _('Events')

    def __str__(self):
        return '%s (%s -> %s)' % (self.name, self.reservation.begin, self.reservation.end)


class EventParticipant(models.Model):
    event = models.ForeignKey(Event, verbose_name=_('Event'), related_name='participants')
    user = models.ForeignKey(User, verbose_name=_('User'), related_name='event_participants', blank=True, null=True)
    first_name = models.CharField(max_length=30, verbose_name=_('First name'), blank=True)
    last_name = models.CharField(max_length=30, verbose_name=_('Last name'), blank=True)
    email = models.EmailField(verbose_name=_('Email'))

    class Meta:
        verbose_name = _('Event participant')
        verbose_name_plural = _('Event participants')

    def __str__(self):
        return '%s in %s' % (self.email, self.event.name)

    def save(self, *args, **kwargs):
        if self.user:
            for field in ('first_name', 'last_name', 'email'):
                setattr(self, field, getattr(self.user, field))
        return super().save(*args, **kwargs)
