# -*- coding: utf-8 -*-
from django.conf.urls import url, include

from core import views


urlpatterns = [
    url(r'^bordermate/(?P<URL_TOKEN>.*)/$', views.BotView.as_view()),
]