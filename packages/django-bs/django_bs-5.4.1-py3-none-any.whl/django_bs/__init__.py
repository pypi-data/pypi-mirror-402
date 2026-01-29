"""Monkey patch ``BoundField.as_widget()``.

Django does not pass all the information we need from ``BoundField`` to
the widget rendering context. Other libraries work around this by
re-implementing the complete widget layer. I chose to monkey-patch
``BoundField`` instead.
"""

import logging

from django.forms.boundfield import BoundField
from django.utils.safestring import mark_safe

logger = logging.getLogger(__name__)

original = BoundField.as_widget


def patched(self, *args, **kwargs):
    html = original(self, *args, **kwargs)
    if self.errors:
        html = mark_safe(html.replace('class="', 'class="is-invalid '))
    return html


BoundField.as_widget = patched
logger.debug('BoundField.as_widget() has been patched by django-bs.')
