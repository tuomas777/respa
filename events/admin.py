from django.contrib import admin
from resources.models import Reservation
from .models import Event, EventParticipant

# Register your models here.


class EventParticipantTabularInline(admin.StackedInline):
    exclude = ('id',)
    model = EventParticipant


class EventAdmin(admin.ModelAdmin):
    exclude = ('id',)
    raw_id_fields = ('reservation',)
    inlines = [EventParticipantTabularInline]

admin.site.register(Event, EventAdmin)


class EventStackedInline(admin.StackedInline):
    model = Event
    verbose_name_plural = 'Event'
    verbose_name = ''
    fields = ('name',)
    inline_classes = ('collapse open',)


class EventReservationAdmin(admin.ModelAdmin):
    inlines = [EventStackedInline]


admin.site.unregister(Reservation)
admin.site.register(Reservation, EventReservationAdmin)
