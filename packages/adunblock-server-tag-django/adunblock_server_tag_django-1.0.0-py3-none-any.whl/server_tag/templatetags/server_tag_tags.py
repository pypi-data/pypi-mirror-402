
import requests
from django import template
from django.core.cache import cache
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def server_tag(remote_url, cache_interval=300, render_script=None):
    cached_data = cache.get(remote_url)

    if cached_data:
        js_files = cached_data
    else:
        try:
            response = requests.get(remote_url)
            response.raise_for_status()
            data = response.json()
            # New format: API returns array directly instead of object with js property
            if isinstance(data, list):
                # New format: array directly
                js_files = {'js': data}
            elif isinstance(data, dict) and 'js' in data:
                # Old format: object with js property (backward compatibility)
                js_files = data
            else:
                js_files = {'js': []}
            cache.set(remote_url, js_files, cache_interval)
        except requests.exceptions.RequestException as e:
            print(f'Error fetching remote script: {e}')
            js_files = {'js': []}

    if render_script:
        return mark_safe(render_script(js_files))
    else:
        from django.utils.html import escape
        scripts = [f'<script src="{escape(src)}" async></script>' for src in js_files.get('js', [])]
        return mark_safe('\n'.join(scripts))

