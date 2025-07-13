"""
Custom middleware for logging HTTP requests asynchronously.
Create this file as main/middleware.py
"""

import time
import threading
from django.utils.deprecation import MiddlewareMixin
from django.db import transaction
from .models import RequestLog


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware that logs HTTP requests asynchronously for audit purposes.

    Logs requests to the database without blocking the response.
    Excludes admin panel, static files, and other non-essential requests.
    """

    # Paths to exclude from logging
    EXCLUDED_PATHS = [
        '/admin/',
        '/static/',
        '/media/',
        '/favicon.ico',
        '/robots.txt',
        '/sitemap.xml',
    ]

    # File extensions to exclude
    EXCLUDED_EXTENSIONS = [
        '.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.ico',
        '.svg', '.woff', '.woff2', '.ttf', '.eot', '.map'
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def process_request(self, request):
        """
        Called at the beginning of each request.
        Store the start time for response time calculation.
        """
        request._logging_start_time = time.time()
        return None

    def process_response(self, request, response):
        """
        Called after the view has been processed.
        Log the request asynchronously if it should be logged.
        """
        # Check if this request should be logged
        if self._should_log_request(request):
            # Calculate response time
            start_time = getattr(request, '_logging_start_time', None)
            response_time_ms = None
            if start_time:
                response_time_ms = int((time.time() - start_time) * 1000)

            # Log the request asynchronously
            self._log_request_async(request, response, response_time_ms)

        return response

    def _should_log_request(self, request):
        """
        Determine if a request should be logged.

        Excludes:
        - Admin panel requests
        - Static files and media
        - Common web files (favicon, robots.txt, etc.)
        - Requests for assets with certain file extensions
        """
        path = request.path.lower()

        # Check excluded paths
        for excluded_path in self.EXCLUDED_PATHS:
            if path.startswith(excluded_path.lower()):
                return False

        # Check excluded file extensions
        for extension in self.EXCLUDED_EXTENSIONS:
            if path.endswith(extension):
                return False

        return True

    def _log_request_async(self, request, response, response_time_ms):
        """
        Log the request asynchronously in a separate thread.
        """
        # Prepare data for logging
        log_data = {
            'method': request.method,
            'path': request.path,
            'query_string': request.META.get('QUERY_STRING', ''),
            'remote_ip': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],  # Limit length
            'response_status': response.status_code,
            'response_time_ms': response_time_ms,
        }

        # Start async logging thread
        logging_thread = threading.Thread(
            target=self._create_log_entry,
            args=(log_data,),
            daemon=True  # Thread dies with the main process
        )
        logging_thread.start()

    def _create_log_entry(self, log_data):
        """
        Create the log entry in the database.
        This runs in a separate thread to avoid blocking the response.
        """
        try:
            # Use atomic transaction to ensure data consistency
            with transaction.atomic():
                RequestLog.objects.create(**log_data)
        except Exception as e:
            # Log the error but don't crash the application
            # In production, you might want to use proper logging
            print(f"Error creating request log: {e}")

    def _get_client_ip(self, request):
        """
        Get the client's IP address, handling proxies and load balancers.
        """
        # Check for IP in various headers (common proxy setups)
        ip_headers = [
            'HTTP_X_FORWARDED_FOR',
            'HTTP_X_REAL_IP',
            'HTTP_X_FORWARDED',
            'HTTP_X_CLUSTER_CLIENT_IP',
            'HTTP_FORWARDED_FOR',
            'HTTP_FORWARDED',
        ]

        for header in ip_headers:
            ip = request.META.get(header)
            if ip:
                # X-Forwarded-For can contain multiple IPs, take the first one
                ip = ip.split(',')[0].strip()
                if self._is_valid_ip(ip):
                    return ip

        # Fall back to REMOTE_ADDR
        return request.META.get('REMOTE_ADDR', '0.0.0.0')

    def _is_valid_ip(self, ip):
        """
        Basic IP validation to avoid logging invalid IPs.
        """
        try:
            parts = ip.split('.')
            if len(parts) != 4:
                return False
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except (ValueError, AttributeError):
            return False


class RequestLoggingCleanupMiddleware(MiddlewareMixin):
    """
    Optional middleware to periodically clean up old request logs.
    Add this after RequestLoggingMiddleware if you want automatic cleanup.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self._cleanup_counter = 0
        super().__init__(get_response)

    def process_response(self, request, response):
        """
        Occasionally clean up old logs (every 1000 requests).
        """
        self._cleanup_counter += 1

        # Run cleanup every 1000 requests
        if self._cleanup_counter >= 1000:
            self._cleanup_counter = 0
            self._cleanup_old_logs_async()

        return response

    def _cleanup_old_logs_async(self):
        """
        Clean up old request logs asynchronously.
        Keeps only the last 10,000 logs to prevent database bloat.
        """
        cleanup_thread = threading.Thread(
            target=self._perform_cleanup,
            daemon=True
        )
        cleanup_thread.start()

    def _perform_cleanup(self):
        """
        Perform the actual cleanup in a separate thread.
        """
        try:
            from django.db.models import Q
            from datetime import datetime, timedelta

            # Keep logs from the last 30 days or last 10,000 entries, whichever is more
            cutoff_date = datetime.now() - timedelta(days=30)

            # Get the ID of the 10,000th most recent log
            logs_to_keep = RequestLog.objects.values_list('id', flat=True)[:10000]
            if logs_to_keep:
                min_id_to_keep = min(logs_to_keep)

                # Delete logs that are both old AND beyond the 10,000 limit
                RequestLog.objects.filter(
                    Q(timestamp__lt=cutoff_date) & Q(id__lt=min_id_to_keep)
                ).delete()

        except Exception as e:
            print(f"Error during request log cleanup: {e}")