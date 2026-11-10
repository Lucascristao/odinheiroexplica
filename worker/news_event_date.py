"""Check explicit dates in the passage selected as proof of the central event.

This does not infer support from an article timestamp or replace semantic review.
It catches a positive model verdict that contradicts the very passage it cites.
"""
from datetime import date, timedelta
import re
import unicodedata


MONTHS = {name: index for index, name in enumerate((
    'janeiro', 'fevereiro', 'marco', 'abril', 'maio', 'junho', 'julho',
    'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'), 1)}
WEEKDAYS = {'segunda': 0, 'terca': 1, 'quarta': 2, 'quinta': 3,
            'sexta': 4, 'sabado': 5, 'domingo': 6}


def validate_event_date(quote, news_day, publication_day=None):
    if not news_day or not quote:
        return
    target = date.fromisoformat(news_day)
    anchor = date.fromisoformat((publication_day or news_day)[:10])
    text = ''.join(c for c in unicodedata.normalize('NFKD', quote.casefold())
                   if not unicodedata.combining(c))
    text = text.replace('\u2011', '-').replace('\u2013', '-')
    found = []
    for match in re.finditer(r'\b(20\d{2})-(\d{2})-(\d{2})\b', text):
        found.append(date(*map(int, match.groups())))
    for match in re.finditer(r'\b(\d{1,2})/(\d{1,2})/(20\d{2})\b', text):
        day, month, year = map(int, match.groups())
        found.append(date(year, month, day))
    for match in re.finditer(r'\b(\d{1,2}) de (' + '|'.join(MONTHS) + r')(?: de (20\d{2}))?\b', text):
        day, month, year = match.groups()
        found.append(date(int(year or anchor.year), MONTHS[month], int(day)))
    weekday = '|'.join(WEEKDAYS)
    for match in re.finditer(r'\b(?:nesta|nessa|na|neste|nesse|no)\s+(' + weekday + r')(?:-feira)?(?:\s*,\s*(\d{1,2})\b)?', text):
        name, day = match.groups()
        if day:
            found.append(date(anchor.year, anchor.month, int(day)))
        else:
            found.append(anchor - timedelta(days=(anchor.weekday() - WEEKDAYS[name]) % 7))
    if re.search(r'\bontem\b', text):
        found.append(anchor - timedelta(days=1))
    # Several dates can appear in the same passage (e.g. today's release and an
    # older reference period). Semantic review still decides which is the event.
    if found and target not in found:
        raise ValueError('Event date evidence contradicts edition date: ' +
                         ', '.join(sorted({day.isoformat() for day in found})))
