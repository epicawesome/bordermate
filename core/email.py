# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Template, Context

from threading import Thread


def send_email_thread(subject='', from_email=settings.DEFAULT_FROM_EMAIL, to=[], params={}, template='', mimetype='text/html; charset=UTF-8', headers={}):
    def _send_email_thread(subject='', from_email=settings.DEFAULT_FROM_EMAIL, to=[], params={}, template='', mimetype='text/html; charset=UTF-8', headers={}):
        try:
            template_content = get_template(template)
            html_content = template_content.render(params)
        except:
            try:
                template_content = Template(template)
                html_content = template_content.render(Context(params))
            except: print('Erro!')

        text_content = subject
        msg = EmailMultiAlternatives(subject, text_content, from_email, to, headers=headers)
        msg.attach_alternative(html_content, mimetype)
        msg.send()

    th=Thread(target=_send_email_thread, args=(subject, from_email, to, params, template, mimetype, headers))
    th.start()