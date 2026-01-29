# Server Tag Django Package

A Django package to fetch and render scripts from a remote URL with template tag integration and caching support.

## Installation

Install the package via pip:

```bash
pip install adunblock-server-tag-django
```

Add the `server_tag` app to your `INSTALLED_APPS` in your Django `settings.py`:

```python
INSTALLED_APPS = [
    # ... other apps
    'server_tag',
]
```

Configure caching in your `settings.py` (recommended for production):

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# Or for development, use local memory cache:
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
```

## Usage

In your Django template, load the `server_tag_tags` and use the `server_tag` tag:

```html
{% load server_tag_tags %}

<!DOCTYPE html>
<html>
<head>
  <title>My Page</title>
  {% server_tag "https://your-remote-url.com/scripts" %}
</head>
<body>
  <h1>My Page</h1>
</body>
</html>
```

### Custom Rendering

You can provide a custom Python function to the `render_script` parameter to customize how script tags are rendered:

```python
# my_app/templatetags/custom_tags.py
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def custom_script_renderer(js_files):
    from django.utils.html import escape
    scripts = [f'<script src="{escape(src)}" defer></script>' for src in js_files.get('js', [])]
    return mark_safe('\n'.join(scripts))
```

```html
{% load server_tag_tags %}
{% load custom_tags %}

<!DOCTYPE html>
<html>
<head>
  <title>My Page</title>
  {% server_tag "https://your-remote-url.com/scripts" render_script=custom_script_renderer %}
</head>
<body>
  <h1>My Page</h1>
</body>
</html>
```

## Features

- **Template Tag Integration**: Easy-to-use Django template tag
- **HTTP Client**: Uses requests library for reliable HTTP operations
- **Caching**: Built-in Django cache integration with configurable TTL
- **Error Handling**: Graceful error handling with fallback to empty arrays
- **Security**: XSS protection with proper HTML escaping
- **Django Integration**: Proper Django app structure with apps.py

## Requirements

- Python 3.8 or higher
- Django 3.2 or higher
- requests 2.25.0 or higher