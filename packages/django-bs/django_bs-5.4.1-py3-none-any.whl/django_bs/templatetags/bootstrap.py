import warnings
from urllib.parse import parse_qs
from urllib.parse import urlencode
from urllib.parse import urlparse
from urllib.parse import urlunparse

from django import template
from django.contrib.messages import constants as message_constants

MESSAGE_LEVEL_CLASSES = {
    message_constants.DEBUG: 'alert alert-warning',
    message_constants.INFO: 'alert alert-info',
    message_constants.SUCCESS: 'alert alert-success',
    message_constants.WARNING: 'alert alert-warning',
    message_constants.ERROR: 'alert alert-danger',
}

register = template.Library()


@register.filter
def bootstrap_message_classes(message):
    classes = []
    classes.append(MESSAGE_LEVEL_CLASSES[message.level])
    classes.append(message.extra_tags or '')
    return ' '.join(classes)


@register.simple_tag
def bootstrap_url_replace_param(url, key, value):
    p = urlparse(url)
    params = parse_qs(p.query)

    if value is None:
        del params[key]
    else:
        params[key] = value

    return urlunparse([
        p.scheme,
        p.netloc,
        p.path,
        p.params,
        urlencode(params, doseq=True),
        p.fragment,
    ])


@register.inclusion_tag('bs/field.html')
def bootstrap_field(
    boundfield,
    *,
    addon_before=None,
    addon_after=None,
    show_label=True,
    wrapper_class='mb-3',
    form_group_class=None,
):
    widget = boundfield.field.widget
    is_check = getattr(widget, 'input_type', None) in ['checkbox', 'radio']
    has_options = getattr(widget, 'option_template_name', None)
    label_classes = set()
    if not show_label:
        label_classes.add('visually-hidden')
    if boundfield.field.required:
        label_classes.add(getattr(boundfield.form, 'required_css_class', ''))
    if form_group_class:
        warnings.warn(
            'form_group_class is deprecated. Use `wrapper_class` instead.',
            DeprecationWarning,
            stacklevel=2,
        )
    return {
        'field': boundfield,
        'check': is_check and not has_options,
        'fieldset': getattr(widget, 'use_fieldset', is_check and has_options),
        'addon_before': addon_before,
        'addon_after': addon_after,
        'label_classes': ' '.join(label_classes),
        'form_group_class': form_group_class,
        'wrapper_class': form_group_class or wrapper_class,
    }


@register.inclusion_tag('bs/form.html')
def bootstrap_form(form):
    return {
        'form': form,
    }


@register.inclusion_tag('bs/messages.html', takes_context=True)
def bootstrap_messages(context):
    return context


@register.inclusion_tag('django/forms/widgets/attrs.html', takes_context=True)
def bootstrap_attrs(context, **kwargs):
    attrs = {**context['widget']['attrs']}
    for key, value in kwargs.items():
        attrs[key] = f'{value} {attrs.get(key, "")}'.strip()
    return {'widget': {'attrs': attrs}}


@register.inclusion_tag('bs/pagination.html', takes_context=True)
def bootstrap_pagination(
    context,
    page,
    pages_to_show=11,
    url=None,
    size=None,
    parameter_name='page',
):
    first = max(1, page.number - pages_to_show // 2)
    last = min(page.paginator.num_pages, first + pages_to_show)
    first = max(1, last - pages_to_show)

    return {
        'page': page,
        'pages_shown': range(first, last + 1),
        'has_previous': first > 1,
        'has_next': last < page.paginator.num_pages,
        'url': url or context['request'].get_full_path(),
        'size': size,
        'parameter_name': parameter_name,
    }
