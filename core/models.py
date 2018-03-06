# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext as _
from django.db.models import signals
from django.dispatch import receiver
from django.db import models
from django.utils import timezone
from django.conf import settings

from .email import send_email_thread

from pymessenger.bot import Bot
from datetime import date, timedelta
import requests
import json


USA_STATES = ('Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
    'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho', 'Illinois',
    'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana', 'Maine', 'Maryland',
    'Massachusetts', 'Michigan', 'Minnesota', 'Mississippi', 'Missouri', 'Montana',
    'Nebraska', 'Nevada', 'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
    'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon', 'Pennsylvania',
    'Rhode Island', 'South Carolina', 'South Dakota', 'Tennessee', 'Texas', 'Utah',
    'Vermont', 'Virginia', 'Washington', 'West Virginia', 'Wisconsin', 'Wyoming',
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'ID', 'IL',
    'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT',
    'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI',
    'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', )

FLIGHT_CODE = {'JP': 'ADR', 'A3': 'AEE', 'EI': 'EIN', 'P5': 'RBP', 'SU': 'AFL',
    'AR': 'ARG', 'AM': 'AMX', 'VV': 'AEW', '8U': 'AAW', 'ZI': 'AAF', 'AH': 'DAH',
    'KC': 'KZR', 'UU': 'REU', 'BT': 'BTI', 'AB': 'BER', 'AC': 'ACA', 'CA': 'CCA',
    'UX': 'AEA', 'AF': 'AFR', 'AI': 'AIC', 'JM': 'AJM', 'JS': 'KOR', 'NX': 'AMU',
    'MD': 'MDG', 'KM': 'AMC', 'MK': 'MAU', '9U': 'MLD', 'SW': 'NMB', 'NZ': 'ANZ',
    'VK': 'VGN', 'PX': 'ANG', 'YW': 'ANE', 'AP': 'ADH', 'FJ': 'FJI', 'HM': 'SEY',
    'VT': 'VTA', 'TN': 'THT', 'TS': 'TSC', 'NF': 'AVN', 'UM': 'AZW', 'SB': 'ACI',
    '4Z': '4Z', 'AS': 'ASA', 'AZ': 'AZA', 'NH': 'ANA', 'AA': 'AAL', 'IZ': 'AIZ',
    'U8': 'RNV', 'OZ': 'AAR', '5Y': '5Y', 'KK': 'KKK', 'AU': 'AUT', 'OS': 'AUA',
    'AV': 'AVA', 'J2': 'AHY', 'JA': 'BON', 'PG': 'BKP', 'B2': 'BRU', 'LZ': 'LBY',
    'BG': 'BBC', 'NT': 'IBB', 'BV': 'BPA', 'KF': 'BLF', 'BD': 'BMA', 'BA': 'BAW',
    'SN': 'DAT', 'FB': 'LZB', '5C': 'ICL', 'W8': 'CJT', 'CV': 'CLX', 'BW': 'BWA',
    'V3': 'KRP', 'CX': 'CPA', 'XK': 'CCM', 'CI': 'CAL', 'CK': 'CK', 'MU': 'CES',
    'CZ': 'CSN', 'QI': 'CIM', 'C9': 'RUS', 'WX': 'BCY', 'MN': 'CAW', 'DE': 'CFG',
    'CO': 'COA', 'CS': 'CMI', 'CM': 'CMP', 'SS': 'CRL', 'OU': 'CTN', 'CU': 'CUB',
    'CY': 'CYP', 'OK': 'CSA', 'DL': 'DAL', 'D0': 'DHK', 'ES': 'DHX', 'D9': 'DNV',
    'KA': 'HDA', '2D': 'DBK', 'MS': 'MSR', 'LY': 'ELY', 'EK': 'UAE', 'OV': 'ELL',
    'ET': 'ETH', 'EY': 'ETD', 'YU': 'MMZ', 'EW': 'EWG', 'BR': 'EVA', 'FX': 'FDX',
    'AY': 'FIN', 'BE': 'BEE', 'FH': 'FHY', 'GA': 'GIA', 'A9': 'TGZ', 'GF': 'GFA',
    'HR': 'HHN', 'HU': 'CHH', 'HA': 'HAL', 'HX': 'CRK', 'UO': 'HKE', 'IB': 'IB',
    'FI': 'ICE', 'D6': 'ILN', 'IR': 'IRA', 'EP': 'IRC', '6H': 'ISR', 'JL': 'JAL',
    'JU': 'JAT', '9W': 'JAI', 'S2': 'S2', 'B6': 'JBU', 'R5': 'R5', 'KQ': 'KQA',
    'IT': 'KFR', 'Y9': 'IRK', 'KL': 'KLM', 'KE': 'KAL', 'KU': 'KAC', 'LR': 'LRC',
    'TM': 'LAM', 'LA': 'LAN', '4M': '4M', 'UC': 'LCO', 'LP': 'LPE', 'XL': 'XL',
    'NG': 'LDA', 'LN': 'LAA', 'LO': 'LOT', 'LT': 'LTU', 'LH': 'DLH', 'LH': 'GEC',
    'CL': 'CLH', 'LG': 'LGL', 'W5': 'IRM', 'MH': 'MAS', 'MA': 'MAH', 'TF': 'SCW',
    'M7': 'MAA', 'ME': 'MEA', 'IG': 'ISS', 'MX': 'MXA', 'OM': 'MGL', 'YM': 'MGX',
    'KZ': 'NCA', 'BJ': 'LBT', 'OA': 'OAL', 'WY': 'OAS', '8Q': 'OHY', 'PR': 'PAL',
    'PC': 'PGT', 'NI': 'PGA', 'PK': 'PIA', 'PU': 'PUA', 'PW': 'PRF', 'QF': 'QFA',
    'QR': 'QTR', 'FV': 'SDM', 'AT': 'RAM', 'BI': 'RBA', 'RJ': 'RJA', 'SA': 'SAA',
    'FA': 'SFR', 'SK': 'SAS', 'SP': 'SAT', 'SV': 'SVA', 'SC': 'CDG', 'FM': 'FM',
    'ZH': 'ZH', 'SQ': 'SIA', 'SQ': 'SIA', 'S7': 'SBI', '3U': '3U', 'MI': 'SLK',
    'ZY': 'SHY', 'JZ': 'SKX', 'XZ': 'EXY', 'JK': 'JKK', 'UL': 'ALK', 'SD': 'SUD',
    'XQ': 'SXS', 'PY': 'SLM', 'LX': 'SWR', 'RB': 'SYR', 'DT': 'DTA', 'TA': 'TAI',
    'T0': 'TPU', 'VR': 'TCV', 'PZ': 'LAP', 'JJ': 'TAM', 'EQ': 'TAE', 'TP': 'TAP',
    'RO': 'ROT', 'TG': 'THA', 'TK': 'THY', '3V': 'TAY', 'UN': 'TSO', 'GE': 'TNA',
    'X3': 'HLF', 'TU': 'TAR', 'PS': 'AUI', 'UA': 'UAL', '5X': 'UPS', 'US': 'USA',
    'UT': 'UTA', 'VN': 'VN', 'VS': 'VIR', 'XF': 'VLK', 'Y4': 'VOI', 'VI': 'VDA',
    'G3': 'GLO', 'KW': 'WAN', 'WHT': 'WHT', 'WF': 'WIF', 'MF': 'CXA', 'IY': 'IYE', }

FLIGHT_STATUS_CHOICES = (
    ('I', _(u'Init')),
    ('W', _(u'Waiting')),
    ('C', _(u'Canceled')),
    ('A', _(u'Arrived')),
    ('H', _(u'Help')),
    ('O', _(u'OK')),
    ('R', _(u'Removed')),
)

class Flight(models.Model):
    class Meta:
        verbose_name = _(u'Flight')
        verbose_name_plural = _(u'Flights')
        ordering = ('-updated_at', )

    send_id = models.CharField(_(u'Send id'), max_length=255)
    send_name = models.CharField(_(u'Send name'), max_length=255, blank=True, null=True)
    code = models.CharField(_(u'Code'), max_length=255, blank=True, null=True)
    origin = models.TextField(_(u'Origin'), blank=True, null=True)
    destination = models.TextField(_(u'Destination'), blank=True, null=True)

    at = models.DateField(_(u'At'), blank=True, null=True)
    notify_emails = models.TextField(_(u'Notify emails'), blank=True, null=True)

    status = models.CharField(_(u'Status'), max_length=1, choices=FLIGHT_STATUS_CHOICES, default='I')
    updated_at = models.DateTimeField(_(u'Updated at'), auto_now=True)
    created_at = models.DateTimeField(_(u'Created at'), auto_now_add=True)
    warnings = models.IntegerField(editable=False, default=0)

    def first_name(self):
        return self.send_name.strip().split(' ')[0]

    def display_time_to_help(self):
        help_at = (self.updated_at+timedelta(hours=3-self.warnings))-timezone.now()
        hours = int(help_at.total_seconds()/3600)
        if hours > 0:
            if hours == 1:
                return u'1 hour'
            else:
                return u'%s hours' % hours
        else:
            minutes = int(help_at.total_seconds()/60)
            if minutes == 1:
                return u'1 minute'
            else:
                return u'%s minutes' % minutes


    def send_help_email(self):
        send_email_thread(
            subject = _(u'%s is stuck at the US border' % self.send_name),
            to = self.notify_emails.split(','),
            params = {
                'flight': self,
            },
            template = 'email.html',
        )

    def get_origin_and_destination(self):
        data_full = get_flight_data(self.code)
        self.origin = data_full.get('origin', {}).get('friendlyLocation')
        self.destination = data_full.get('destination', {}).get('friendlyLocation')
        self.save()

    def status_update(self):
        if self.status == 'W' and self.at <= date.today():
            data_full = get_flight_data(self.code)
            if data_full.get('canceled') and self.status != 'C':
                self.status = 'C'
                self.save()
            elif data_full.get('gateArrivalTimes', {}).get('actual'):
                self.warnings = 1
                self.status = 'A'
                self.save()
                bot = Bot(settings.ACCESS_TOKEN)
                send_message = _(u'Hi there, just a friendly reminder that if I don’t hear from you in 2 hours I’ll email your loved ones to tell them you’re stuck at the border.')
                buttons = [
                    {
                        "type": "postback",
                        "title": _(u"I’m through"),
                        "payload": "IM_THROUGH"
                    },
                    {
                        "type": "postback",
                        "title": _(u"Help!"),
                        "payload": "HELP"
                    },
                ]
                bot.send_button_message(self.send_id, send_message, buttons)

        # Ainda não respondeu, manda até 3 alertas
        if self.status == 'A':
            if self.warnings < 3:
                hours = int((timezone.now()-self.updated_at).total_seconds()/3600)
                if hours == 1:
                    self.warnings += 1
                    self.save()

                    if self.warnings == 2:
                        bot = Bot(settings.ACCESS_TOKEN)
                        send_message = _(u'Sorry to keep bugging you, but if you don’t tell me you’re through immigration I’ll send out emails 1 hour from now.')
                        buttons = [
                            {
                                "type": "postback",
                                "title": _(u"I’m through"),
                                "payload": "IM_THROUGH"
                            },
                            {
                                "type": "postback",
                                "title": _(u"Help!"),
                                "payload": "HELP"
                            },
                        ]
                        bot.send_button_message(self.send_id, send_message, buttons)
                    elif self.warnings == 3:
                        bot = Bot(settings.ACCESS_TOKEN)
                        send_message = _(u'Alright, seems like you’re stuck, so I’ll just go ahead and email everyone you chose. I hope everything ends up alright. Good luck!')
                        bot.send_text_message(self.send_id, send_message)

                        # Depois de 3 alertas, entra em help
                        self.status = 'H'
                        self.save()

    def __str__(self):
        return u'%s' % self.send_id
@receiver(signals.pre_save, sender=Flight)
def status_flight_signals(sender, instance, raw, using, *args, **kwargs):
    if instance.status == 'H':
        instance.send_help_email()


def valid_flight_code(code):
    if len(code) < 3:
        return u'INVALID'

    if code[2].isdigit():
        digits = code[:2]
        if FLIGHT_CODE.get(digits):
            code = code.replace(digits, FLIGHT_CODE.get(digits))

    r = requests.get(u'https://flightaware.com/live/flight/%s' % code)
    data_code = r.url.split('/')[-1]
    if u"FlightAware couldn't find flight tracking data for" in r.text:
        data_code = u'INVALID'

    if data_code == u'INVALID':
        # Tentar pela busca
        r = requests.get(u'https://flightaware.com/ajax/ignoreall/omnisearch/disambiguation.rvt?searchterm=%s' % code)
        data_code = r.url.split('/')[-1]
        if not '/live/flight/' in r.url:
            data_code = u'INVALID'
    return data_code


def get_flight_data(code):
    r = requests.get(u'https://flightaware.com/live/flight/%s' % code)
    data_full = json.loads(r.text.split('<script>var trackpollBootstrap = ')[1].split(';</script>')[0])
    return data_full['flights'][list(data_full['flights'].keys())[0]]


def get_at(text):
    def next_weekday(d, weekday):
        days_ahead = weekday - d.weekday()
        if days_ahead <= 0: # Target day already happened this week
            days_ahead += 7
        return d + timedelta(days_ahead)

    if '/' in text:
        if len(text.split('/')) == 2:
            month, day = text.split('/')
            today = date.today()
            at = date(year=today.year, month=int(month), day=int(day))
            if at < today:
                at = date(year=today.year+1, month=int(month), day=int(day))

            if int(day) <= 12 and int(month) <= 12:
                at2 = date(year=today.year, month=int(day), day=int(month))
                if at2 < today:
                    at2 = date(year=today.year+1, month=int(day), day=int(month))
                return [at, at2, ]
            return at
        elif len(text.split('/')) == 3:
            year, month, day = text.split('/')
            return date(year=int(year), month=int(month), day=int(day))
    elif 'today' in text.lower():
        return date.today()
    elif 'tomorrow' in text.lower():
        return date.today()+timedelta(days=1)
    elif 'next' in text.lower():
        if 'monday' in text.lower():
            weekday = 0
        elif 'tuesday' in text.lower():
            weekday = 1
        elif 'wednesday' in text.lower():
            weekday = 2
        elif 'thursday' in text.lower():
            weekday = 3
        elif 'friday' in text.lower():
            weekday = 4
        elif 'saturday' in text.lower():
            weekday = 5
        elif 'sunday' in text.lower():
            weekday = 6
        return next_weekday(date.today(), weekday)
    elif text.isdigit():
        day = int(text)
        today = date.today()
        at = date(year=today.year, month=today.month, day=int(day))
        if at < today:
            if today.month < 12:
                at = date(year=today.year, month=today.month+1, day=int(day))
            else:
                at = date(year=today.year+1, month=1, day=int(day))
        return at
    return