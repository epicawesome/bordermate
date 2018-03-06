# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from datetime import date
from core.models import Flight


class Command(BaseCommand):

    def handle(self, *args, **options):
        for flight in Flight.objects.filter(status__in=('A', 'W'), at__lte=date.today()):
            flight.status_update()