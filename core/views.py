# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _
from django.views.generic import View
from django.http import HttpResponse, Http404
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import mail_admins

from core.models import Flight, valid_flight_code, get_flight_data, USA_STATES, get_at

from pymessenger.bot import Bot
from pymessenger.user_profile import UserProfileApi
from datetime import datetime, date, timedelta
import json
import traceback


class BotView(View):
    bot = Bot(settings.ACCESS_TOKEN)
    graph = UserProfileApi(settings.ACCESS_TOKEN)

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(BotView, self).dispatch(request, *args, **kwargs)

    def get(self, request, URL_TOKEN, *args, **kwargs):
        if URL_TOKEN != settings.URL_TOKEN:
            raise Http404

        if request.GET.get("hub.verify_token") == settings.VERIFY_TOKEN:
            return HttpResponse(request.GET.get("hub.challenge"))
        return HttpResponse(_(u'Invalid verification token'))

    def post(self, request, URL_TOKEN, *args, **kwargs):
        if URL_TOKEN != settings.URL_TOKEN:
            raise Http404

        try:
            output = json.loads(request.body.decode("utf-8"))
            for event in output['entry']:
                for message in event.get('messaging', []):
                    if (message.get('message') or message.get('postback')) and not message.get('message', {}).get('is_echo'):
                        send_id = message.get('sender', {}).get('id')
                        if send_id:
                            try:
                                if message.get('message', {}).get('nlp', {}).get('entities', {}).get('greetings', [])[0].get('confidence', 0) >= 0.9:
                                    Flight.objects.filter(send_id=send_id, status__in=('I', 'W', 'C', 'A', 'H', )).update(status='R')
                            except: pass

                            if 'cancel' in message.get('message', {}).get('text', ''):
                                Flight.objects.filter(send_id=send_id, status__in=('I', 'W', 'C', 'A', 'H', )).update(status='R')
                                send_message = _(u'Canceled flight record! Would you like to add another?')
                                self.bot.send_text_message(send_id, send_message)
                                return HttpResponse("Success")

                            # Get or create Flight
                            try:
                                flight = Flight.objects.filter(send_id=send_id, status__in=('I', 'W', 'C', 'A', )).latest('created_at')
                                created = False
                            except Flight.DoesNotExist:
                                user_info = self.graph.get(send_id)
                                send_name = u'%s %s' % (user_info.get('first_name'), user_info.get('last_name'), )
                                flight = Flight.objects.create(send_id=send_id, send_name=send_name, status='I')
                                created = True

                            # First steep
                            if created:
                                send_message = _(u'Hi! You’re coming to the US? That’s great. And you shouldn’t worry about a thing. Especially getting stuck at immigration. Just let me know your flight number, departure date, and who you want to notify if you get stuck.')
                                buttons = [
                                    {
                                        "type": "postback",
                                        "title": _(u"Add flight info"),
                                        "payload": "NEW_FLIGHT"
                                    },
                                    {
                                        "type": "postback",
                                        "title": _(u"Tell me more"),
                                        "payload": "TELL_ME_MORE"
                                    },
                                ]
                                self.bot.send_button_message(send_id, send_message, buttons)
                                return HttpResponse("Success")

                            # Get code, origin, destination
                            if not flight.code:
                                if message.get('postback', {}).get('payload') == 'NEW_FLIGHT' or message.get('message', {}).get('text', '').lower() in (u"add flight", u"new flight", u"i understand", u"ok. i understand!", u"ok", u"ok."):
                                    # Add flight info
                                    send_message = _(u"Let's do this. Can you tell me your flight number?")
                                    self.bot.send_text_message(send_id, send_message)
                                    return HttpResponse("Success")
                                elif message.get('postback', {}).get('payload') == 'TELL_ME_MORE' or message.get('message', {}).get('text', '').lower() == u"tell me more":
                                    send_message = _(u"President Trump's Muslim Ban and its subsequent versions have gotten people worried about getting stuck at the US border while their loved ones don't know what happened to them. We think there are better things to worry about. We'll keep track of your flight and if you can't contact us for 3h after landing we'll contact your loved ones to tell them you're most likely stuck at the border.")
                                    buttons = [
                                        {
                                            "type": "postback",
                                            "title": _(u"Ok. I understand!"),
                                            "payload": "NEW_FLIGHT"
                                        },
                                    ]
                                    self.bot.send_button_message(send_id, send_message, buttons)
                                    return HttpResponse("Success")
                                else:
                                    if message.get('message', {}).get('text', ''):
                                        code = valid_flight_code(message.get('message', {}).get('text', ''))
                                        if code and code != 'INVALID':
                                            data_full = get_flight_data(code)
                                            origin = data_full.get('origin', {}).get('friendlyLocation', '')
                                            for state in USA_STATES:
                                                if state in origin:
                                                    send_message = _(u'Sorry, I can only keep track of international flights. Would you like to add a different flight?')
                                                    self.bot.send_text_message(send_id, send_message)
                                                    return HttpResponse("Success")

                                            destination = data_full.get('destination', {}).get('friendlyLocation', '')
                                            for state in USA_STATES:
                                                if state in destination:
                                                    flight.code = code
                                                    flight.get_origin_and_destination()

                                                    send_message = _(u'Oh, you’re coming from %s? Lovely place. And when is your departure date?') % flight.origin
                                                    self.bot.send_text_message(send_id, send_message)
                                                    return HttpResponse("Success")

                                            send_message = _(u'Sorry, you can’t add the flight that the destination is not the US.')
                                            self.bot.send_text_message(send_id, send_message)
                                            return HttpResponse("Success")
                                        else:
                                            send_message = _(u'I don’t understand. So what’s your flight number?')
                                            self.bot.send_text_message(send_id, send_message)
                                            return HttpResponse("Success")


                            # Get at
                            if not flight.at:
                                if message.get('message', {}).get('text', '') or message.get('postback', {}).get('payload'):
                                    text = message.get('message', {}).get('text',  message.get('postback', {}).get('payload', ''))
                                    at = get_at(text)
                                    if at:
                                        if type(at) == list:
                                            send_message = _(u'Can you clarify that date?')
                                            buttons = []
                                            for dt in at:
                                                buttons.append({
                                                    "type": "postback",
                                                    "title": dt.strftime("%B %dth"),
                                                    "payload": dt.strftime("%Y/%m/%d")
                                                })
                                            self.bot.send_button_message(send_id, send_message, buttons)
                                            return HttpResponse("Success")
                                        else:
                                            flight.at = at
                                            flight.save()
                                            send_message = _(u'Great. Now who do you want to notify if you get stuck? Just type their emails.')
                                            self.bot.send_text_message(send_id, send_message)
                                            return HttpResponse("Success")
                                    else:
                                        send_message = _(u'Sorry, that’s a little confusing. Enter MM/DD, please. Try again, or type "cancel" to add another flight.')
                                        self.bot.send_text_message(send_id, send_message)
                                        return HttpResponse("Success")

                            # Get notify_emails
                            if not flight.notify_emails:
                                if message.get('message', {}).get('text', '') or message.get('postback', {}).get('payload'):
                                    nlp = message.get('message', {}).get('nlp', {}).get('entities', {})
                                    if nlp.get('email'):
                                        emails = list(set([email.get('value') for email in nlp.get('email')]))
                                        send_message = _(u'Please confirm these are the correct addresses? %s' % u", ".join(emails))
                                        buttons = [
                                            {
                                                "type": "postback",
                                                "title": "Yes",
                                                "payload": u",".join(emails)
                                            },
                                            {
                                                "type": "postback",
                                                "title": _(u"No"),
                                                "payload": "AT_NO"
                                            },
                                        ]
                                        self.bot.send_button_message(send_id, send_message, buttons)
                                        return HttpResponse("Success")

                                    elif '@' in message.get('message', {}).get('text', message.get('postback', {}).get('payload', '')):
                                        flight.notify_emails = message.get('message', {}).get('text', message.get('postback', {}).get('payload', ''))
                                        flight.status = 'W'
                                        flight.save()

                                        send_message = _(u'Got it. Here’s how this will work: if I haven’t heard from you for 3 hours after you landed, I’ll let your people know you’re probably stuck at the border and might need their help.')
                                        self.bot.send_text_message(send_id, send_message)
                                        send_message = _(u'You can check back any time for tips on what to expect and do. But most of all, enjoy your trip to the US!')
                                        self.bot.send_text_message(send_id, send_message)
                                        return HttpResponse("Success")

                                    else:
                                        send_message = _(u'Sorry, i don’t understand. Who do you want to notify if you get stuck? Just type their emails. Try again, or type "cancel" to add another flight.')
                                        self.bot.send_text_message(send_id, send_message)
                                        return HttpResponse("Success")

                            # Callback
                            if message.get('postback', {}).get('payload') == 'IM_THROUGH' or message.get('message', {}).get('text', '').lower() == u"i’m through":
                                flight.status = 'O'
                                flight.save()
                                send_message = _(u'Oh, great! Enjoy your trip!')
                                self.bot.send_text_message(send_id, send_message)
                                return HttpResponse("Success")
                            elif message.get('postback', {}).get('payload') == 'HELP' or message.get('message', {}).get('text', '').lower() == u"help!":

                                send_message = _(u'Well, that’s what I’m here for. How can I help you?')
                                buttons = [
                                    {
                                        "type": "postback",
                                        "title": _(u"I’m in secondary screening",),
                                        "payload": u"SECONDARY_SCREENING",
                                    },
                                    {
                                        "type": "postback",
                                        "title": _(u"I’m nervous"),
                                        "payload": "NERVOUS",
                                    },
                                    {
                                        "type": "postback",
                                        "title": _(u"The line is too long"),
                                        "payload": "TOO_LONG",
                                    },
                                ]
                                self.bot.send_button_message(send_id, send_message, buttons)
                                return HttpResponse("Success")
                            elif message.get('postback', {}).get('payload') == 'SECONDARY_SCREENING' or message.get('message', {}).get('text', '').lower() == u"i’m in secondary screening":
                                send_message = _(u'OK. Secondary screening is perfectly normal. If you want to know more about your legal rights, here’s a great article: http://www.cnn.com/2017/02/16/us/border-legal-rights-faq-trnd/index.html. And I’m still set to send those emails to let your loved ones know where you are %s from now.' % flight.display_time_to_help() )
                                buttons = [
                                    {
                                        "type": "postback",
                                        "title": _("Ok!",),
                                        "payload": u"IM_THROUGH",
                                    },
                                    {
                                        "type": "postback",
                                        "title": _(u"Please send emails now"),
                                        "payload": "SEND_EMAILS",
                                    },
                                ]
                                self.bot.send_button_message(send_id, send_message, buttons)
                                return HttpResponse("Success")

                            elif message.get('postback', {}).get('payload') == 'NERVOUS' or message.get('message', {}).get('text', '').lower() == u"i’m nervous":
                                send_message = _(u'Just remember border patrol agents are just making sure all your paperwork is right and that you’re safe to enter the country. It’s inconvenient, but it will be over soon.')
                                self.bot.send_text_message(send_id, send_message)
                                return HttpResponse("Success")

                            elif message.get('postback', {}).get('payload') == 'TOO_LONG' or message.get('message', {}).get('text', '').lower() == u"the line is too long":
                                send_message = _(u'That one I can’t help you with. I’m not very patient either.')
                                self.bot.send_text_message(send_id, send_message)
                                return HttpResponse("Success")

                            elif message.get('postback', {}).get('payload') == 'SEND_EMAILS' or message.get('message', {}).get('text', '').lower() == u"please send emails now":
                                flight.status = 'H'
                                flight.save()
                                send_message = _(u'Ok, I’m sending emails to (%s) right now. Hopefully you’ll get things straightened out in no time.' % flight.notify_emails)
                                self.bot.send_text_message(send_id, send_message)
                                return HttpResponse("Success")

                            # Add/Remove email
                            else:
                                nlp = message.get('message', {}).get('nlp', {}).get('entities', {})
                                if nlp.get('email'):
                                    new_emails = [email.get('value') for email in nlp.get('email')]
                                    if 'add' in message.get('message', {}).get('text', '').lower():
                                        emails = list(set(flight.notify_emails.split(',')+new_emails))
                                        flight.notify_emails = u','.join(emails)
                                        flight.status = 'W'
                                        flight.save()
                                        send_message = _(u'%s successfully added.' % u', '.join(new_emails))
                                        self.bot.send_text_message(send_id, send_message)
                                        return HttpResponse("Success")

                                    elif 'remove' in message.get('message', {}).get('text', '').lower():
                                        emails = flight.notify_emails.split(',')
                                        emails = list(set([email for email in emails if not email in new_emails]))
                                        flight.notify_emails = u','.join(emails)
                                        flight.status = 'W'
                                        flight.save()
                                        send_message = _(u'%s successfully removed.' % u', '.join(new_emails))
                                        self.bot.send_text_message(send_id, send_message)
                                        return HttpResponse("Success")
                                else:
                                    send_message = _(u'Sorry, i don’t understand. If you want to remove or add some email, just type me ask. Eg: Remove me@bordermate.com. Or Add me@bordermate.com. Or type "cancel" to add another flight.')
                                    self.bot.send_text_message(send_id, send_message)
                                    return HttpResponse("Success")

        except:
            subject = "Bordermate failure"
            message = traceback.format_exc()
            mail_admins(subject, message)
            send_message = _(u"I’m sorry. I have a bug and i needed call my parents.")
            self.bot.send_text_message(send_id, send_message)
        return HttpResponse("Success")