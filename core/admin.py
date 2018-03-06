# -*- coding: utf-8 -*-
from django.contrib import admin
from django.utils.translation import ugettext as _

from core.models import Flight


@admin.register(Flight)
class FlightAdmin(admin.ModelAdmin):
    list_display = ('send_id', 'send_name', 'status', 'updated_at', 'created_at', )
    date_hierarchy = 'updated_at'


# Custom admin name
admin.site.site_title = u'Border Mate'
admin.site.site_header = u'Border Mate'
admin.site.index_title = u'Border Mate'