"""
Custom context processors for the CV management system.
Create this file as main/context_processors.py
"""

from django.conf import settings
import re


def settings_context(request):
    """
    Context processor that injects filtered Django settings into all templates.

    Filters out sensitive settings like SECRET_KEY, database passwords, API keys, etc.
    Makes settings available in templates as {{ settings.DEBUG }}, {{ settings.TIME_ZONE }}, etc.
    """

    # List of sensitive setting patterns to exclude
    SENSITIVE_PATTERNS = [
        r'.*SECRET.*',
        r'.*KEY.*',
        r'.*PASSWORD.*',
        r'.*TOKEN.*',
        r'.*API.*',
        r'.*CREDENTIAL.*',
        r'.*AUTH.*',
        r'.*PASS.*',
        r'.*PRIVATE.*',
        r'.*SECURITY.*',
        r'.*ENCRYPT.*',
        r'.*HASH.*',
        r'.*SALT.*',
        r'.*DATABASE.*',  # Exclude entire database config for safety
        r'.*EMAIL_HOST.*',  # Email credentials
        r'.*STRIPE.*',
        r'.*PAYPAL.*',
        r'.*AWS.*',
        r'.*GOOGLE.*',
        r'.*FACEBOOK.*',
        r'.*TWITTER.*',
        r'.*GITHUB.*',
        r'.*OAUTH.*',
        r'.*SENTRY.*',
        r'.*CACHE.*',  # Cache backend might contain sensitive info
    ]

    # Compile regex patterns for efficiency
    sensitive_regexes = [re.compile(pattern, re.IGNORECASE) for pattern in SENSITIVE_PATTERNS]

    def is_sensitive_setting(setting_name):
        """Check if a setting name matches any sensitive pattern."""
        return any(regex.match(setting_name) for regex in sensitive_regexes)

    def safe_value(value):
        """
        Return a safe representation of the value.
        Convert complex objects to readable strings.
        """
        if isinstance(value, (list, tuple)):
            return list(value) if len(value) < 50 else f"List with {len(value)} items"
        elif isinstance(value, dict):
            return dict(value) if len(value) < 20 else f"Dict with {len(value)} keys"
        elif isinstance(value, str) and len(value) > 200:
            return f"{value[:200]}... (truncated)"
        else:
            return value

    # Get all Django settings
    filtered_settings = {}

    for setting_name in dir(settings):
        # Skip private attributes and methods
        if setting_name.startswith('_'):
            continue

        # Skip if it's a sensitive setting
        if is_sensitive_setting(setting_name):
            continue

        try:
            setting_value = getattr(settings, setting_name)
            # Skip callable objects (methods, functions)
            if callable(setting_value):
                continue

            filtered_settings[setting_name] = safe_value(setting_value)

        except Exception:
            # Skip settings that can't be accessed
            continue

    # Add some computed/derived settings that might be useful
    derived_settings = {
        'INSTALLED_APPS_COUNT': len(getattr(settings, 'INSTALLED_APPS', [])),
        'MIDDLEWARE_COUNT': len(getattr(settings, 'MIDDLEWARE', [])),
        'IS_DEBUG_MODE': getattr(settings, 'DEBUG', False),
        'TIMEZONE_INFO': {
            'timezone': getattr(settings, 'TIME_ZONE', 'UTC'),
            'use_tz': getattr(settings, 'USE_TZ', True),
        },
        'LANGUAGE_INFO': {
            'language_code': getattr(settings, 'LANGUAGE_CODE', 'en-us'),
            'use_i18n': getattr(settings, 'USE_I18N', True),
        },
        'STATIC_INFO': {
            'static_url': getattr(settings, 'STATIC_URL', '/static/'),
            'staticfiles_dirs_count': len(getattr(settings, 'STATICFILES_DIRS', [])),
        }
    }

    # Merge derived settings
    filtered_settings.update(derived_settings)

    return {
        'settings': filtered_settings,
        'django_settings': filtered_settings,  # Alternative name for clarity
    }


def request_context(request):
    """
    Context processor that adds useful request information to templates.
    Provides info about the current request without sensitive data.
    """

    # Get safe request information
    request_info = {
        'method': request.method,
        'path': request.path,
        'is_ajax': request.headers.get('X-Requested-With') == 'XMLHttpRequest',
        'is_secure': request.is_secure(),
        'user_agent': request.META.get('HTTP_USER_AGENT', '')[:100],  # Truncated for safety
        'remote_addr': request.META.get('REMOTE_ADDR', 'Unknown'),
        'query_params_count': len(request.GET),
        'is_mobile': 'Mobile' in request.META.get('HTTP_USER_AGENT', ''),
    }

    return {
        'request_info': request_info,
    }


def app_context(request):
    """
    Context processor that adds application-specific context.
    Useful for showing app version, environment info, etc.
    """

    from main.models import CV, RequestLog
    from django.db import connection

    try:
        # Get some app statistics
        app_stats = {
            'total_cvs': CV.objects.count(),
            'total_request_logs': RequestLog.objects.count() if RequestLog.objects.exists() else 0,
            'database_vendor': connection.vendor,
        }
    except Exception:
        # Fallback if database isn't available
        app_stats = {
            'total_cvs': 0,
            'total_request_logs': 0,
            'database_vendor': 'unknown',
        }

    app_info = {
        'app_name': 'CV Management System',
        'app_version': '1.0.0',  # You can make this dynamic
        'environment': 'Development' if getattr(settings, 'DEBUG', False) else 'Production',
        'stats': app_stats,
    }

    return {
        'app_info': app_info,
    }