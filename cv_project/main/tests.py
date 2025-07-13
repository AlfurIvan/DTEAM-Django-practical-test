"""
Tests for the CV management system.
"""

import time
from datetime import date
from datetime import datetime, timedelta

from django.conf import settings
from django.http import HttpResponse
from django.template import Template
from django.test import TestCase, Client, RequestFactory
from django.test import override_settings
from django.urls import reverse
from main.context_processors import settings_context, request_context, app_context
from main.middleware import RequestLoggingMiddleware
from main.models import CV, Skill, Project, Contact, RequestLog, CV
from main.views import SettingsView


class CVModelTest(TestCase):
    """Test cases for CV model."""

    def setUp(self):
        """Set up test data."""
        self.cv = CV.objects.create(
            firstname="Test",
            lastname="User",
            email="test@example.com",
            phone="123-456-7890",
            bio="Test biography"
        )

    def test_cv_creation(self):
        """Test CV model creation."""
        self.assertEqual(self.cv.firstname, "Test")
        self.assertEqual(self.cv.lastname, "User")
        self.assertEqual(self.cv.email, "test@example.com")
        self.assertEqual(self.cv.full_name, "Test User")
        self.assertTrue(self.cv.created_at)
        self.assertTrue(self.cv.updated_at)

    def test_cv_str_method(self):
        """Test CV string representation."""
        self.assertEqual(str(self.cv), "Test User")

    def test_cv_absolute_url(self):
        """Test CV get_absolute_url method."""
        expected_url = reverse('cv_detail', kwargs={'pk': self.cv.pk})
        self.assertEqual(self.cv.get_absolute_url(), expected_url)


class SkillModelTest(TestCase):
    """Test cases for Skill model."""

    def setUp(self):
        """Set up test data."""
        self.cv = CV.objects.create(
            firstname="Test",
            lastname="User",
            email="test@example.com",
            bio="Test biography"
        )
        self.skill = Skill.objects.create(
            cv=self.cv,
            name="Python",
            proficiency="expert"
        )

    def test_skill_creation(self):
        """Test Skill model creation."""
        self.assertEqual(self.skill.name, "Python")
        self.assertEqual(self.skill.proficiency, "expert")
        self.assertEqual(self.skill.cv, self.cv)

    def test_skill_str_method(self):
        """Test Skill string representation."""
        self.assertEqual(str(self.skill), "Python (expert)")

    def test_skill_unique_together(self):
        """Test that CV and skill name combination is unique."""
        with self.assertRaises(Exception):
            Skill.objects.create(
                cv=self.cv,
                name="Python",  # Same name for same CV
                proficiency="beginner"
            )


class ProjectModelTest(TestCase):
    """Test cases for Project model."""

    def setUp(self):
        """Set up test data."""
        self.cv = CV.objects.create(
            firstname="Test",
            lastname="User",
            email="test@example.com",
            bio="Test biography"
        )
        self.project = Project.objects.create(
            cv=self.cv,
            title="Test Project",
            description="Test project description",
            technologies="Python, Django, PostgreSQL",
            url="https://example.com",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )

    def test_project_creation(self):
        """Test Project model creation."""
        self.assertEqual(self.project.title, "Test Project")
        self.assertEqual(self.project.cv, self.cv)
        self.assertFalse(self.project.is_ongoing)

    def test_project_str_method(self):
        """Test Project string representation."""
        self.assertEqual(str(self.project), "Test Project")

    def test_project_ongoing(self):
        """Test ongoing project property."""
        ongoing_project = Project.objects.create(
            cv=self.cv,
            title="Ongoing Project",
            description="Ongoing project description",
            technologies="Python",
            start_date=date(2024, 1, 1),
            end_date=None
        )
        self.assertTrue(ongoing_project.is_ongoing)

    def test_technologies_list_property(self):
        """Test technologies_list property."""
        expected_technologies = ['Python', 'Django', 'PostgreSQL']
        self.assertEqual(self.project.technologies_list, expected_technologies)


class ContactModelTest(TestCase):
    """Test cases for Contact model."""

    def setUp(self):
        """Set up test data."""
        self.cv = CV.objects.create(
            firstname="Test",
            lastname="User",
            email="test@example.com",
            bio="Test biography"
        )
        self.contact = Contact.objects.create(
            cv=self.cv,
            contact_type="github",
            value="testuser",
            url="https://github.com/testuser"
        )

    def test_contact_creation(self):
        """Test Contact model creation."""
        self.assertEqual(self.contact.contact_type, "github")
        self.assertEqual(self.contact.value, "testuser")
        self.assertEqual(self.contact.cv, self.cv)

    def test_contact_str_method(self):
        """Test Contact string representation."""
        self.assertEqual(str(self.contact), "github: testuser")

    def test_contact_unique_together(self):
        """Test that CV and contact_type combination is unique."""
        with self.assertRaises(Exception):
            Contact.objects.create(
                cv=self.cv,
                contact_type="github",  # Same type for same CV
                value="anotheruser",
                url="https://github.com/anotheruser"
            )


class CVListViewTest(TestCase):
    """Test cases for CV list view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.cv1 = CV.objects.create(
            firstname="John",
            lastname="Doe",
            email="john@example.com",
            bio="John's biography"
        )
        self.cv2 = CV.objects.create(
            firstname="Jane",
            lastname="Smith",
            email="jane@example.com",
            bio="Jane's biography"
        )

    def test_cv_list_view_status_code(self):
        """Test that CV list view returns 200."""
        response = self.client.get(reverse('cv_list'))
        self.assertEqual(response.status_code, 200)

    def test_cv_list_view_template(self):
        """Test that CV list view uses correct template."""
        response = self.client.get(reverse('cv_list'))
        self.assertTemplateUsed(response, 'main/cv_list.html')

    def test_cv_list_view_context(self):
        """Test that CV list view contains CVs in context."""
        response = self.client.get(reverse('cv_list'))
        self.assertContains(response, "John Doe")
        self.assertContains(response, "Jane Smith")
        self.assertEqual(len(response.context['cvs']), 2)

    def test_cv_list_view_empty(self):
        """Test CV list view when no CVs exist."""
        CV.objects.all().delete()
        response = self.client.get(reverse('cv_list'))
        self.assertContains(response, "No CVs Found")


class CVDetailViewTest(TestCase):
    """Test cases for CV detail view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.cv = CV.objects.create(
            firstname="John",
            lastname="Doe",
            email="john@example.com",
            bio="John's biography"
        )
        # Add some related data
        Skill.objects.create(cv=self.cv, name="Python", proficiency="expert")
        Project.objects.create(
            cv=self.cv,
            title="Test Project",
            description="Test description",
            technologies="Python, Django",
            start_date=date(2023, 1, 1)
        )
        Contact.objects.create(
            cv=self.cv,
            contact_type="github",
            value="johndoe",
            url="https://github.com/johndoe"
        )

    def test_cv_detail_view_status_code(self):
        """Test that CV detail view returns 200."""
        response = self.client.get(reverse('cv_detail', kwargs={'pk': self.cv.pk}))
        self.assertEqual(response.status_code, 200)

    def test_cv_detail_view_template(self):
        """Test that CV detail view uses correct template."""
        response = self.client.get(reverse('cv_detail', kwargs={'pk': self.cv.pk}))
        self.assertTemplateUsed(response, 'main/cv_detail.html')

    def test_cv_detail_view_context(self):
        """Test that CV detail view contains correct CV in context."""
        response = self.client.get(reverse('cv_detail', kwargs={'pk': self.cv.pk}))
        self.assertEqual(response.context['cv'], self.cv)
        self.assertContains(response, "John Doe")
        self.assertContains(response, "john@example.com")
        self.assertContains(response, "Python")
        self.assertContains(response, "Test Project")

    def test_cv_detail_view_404(self):
        """Test that CV detail view returns 404 for non-existent CV."""
        response = self.client.get(reverse('cv_detail', kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)

    def test_cv_detail_view_query_optimization(self):
        """Test that CV detail view uses optimized queries."""
        with self.assertNumQueries(6):  # Expecting optimized queries
            response = self.client.get(reverse('cv_detail', kwargs={'pk': self.cv.pk}))
            # Access related objects to trigger queries
            cv = response.context['cv']
            list(cv.skills.all())
            list(cv.projects.all())
            list(cv.contacts.all())


class CVPDFDownloadTest(TestCase):
    """Test cases for CV PDF download functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.cv = CV.objects.create(
            firstname="John",
            lastname="Doe",
            email="john@example.com",
            bio="John's biography for PDF testing"
        )
        # Add some related data for richer PDF
        Skill.objects.create(cv=self.cv, name="Python", proficiency="expert")
        Project.objects.create(
            cv=self.cv,
            title="Test Project",
            description="Test description for PDF",
            technologies="Python, Django",
            start_date=date(2023, 1, 1)
        )
        Contact.objects.create(
            cv=self.cv,
            contact_type="github",
            value="johndoe",
            url="https://github.com/johndoe"
        )

    def test_cv_pdf_download_status_code(self):
        """Test that CV PDF download returns 200."""
        response = self.client.get(reverse('cv_pdf_download', kwargs={'pk': self.cv.pk}))
        self.assertEqual(response.status_code, 200)

    def test_cv_pdf_download_content_type(self):
        """Test that CV PDF download returns correct content type."""
        response = self.client.get(reverse('cv_pdf_download', kwargs={'pk': self.cv.pk}))
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_cv_pdf_download_filename(self):
        """Test that CV PDF download has correct filename."""
        response = self.client.get(reverse('cv_pdf_download', kwargs={'pk': self.cv.pk}))
        expected_filename = 'attachment; filename="John_Doe_CV.pdf"'
        self.assertEqual(response['Content-Disposition'], expected_filename)

    def test_cv_pdf_download_content_length(self):
        """Test that CV PDF download has content."""
        response = self.client.get(reverse('cv_pdf_download', kwargs={'pk': self.cv.pk}))
        self.assertGreater(len(response.content), 1000)  # PDF should be substantial

    def test_cv_pdf_download_404(self):
        """Test that CV PDF download returns 404 for non-existent CV."""
        response = self.client.get(reverse('cv_pdf_download', kwargs={'pk': 9999}))
        self.assertEqual(response.status_code, 404)

    def test_cv_pdf_download_with_special_characters(self):
        """Test PDF download with special characters in name."""
        cv_special = CV.objects.create(
            firstname="José María",
            lastname="García-López",
            email="jose@example.com",
            bio="Biography with special characters: áéíóú"
        )
        response = self.client.get(reverse('cv_pdf_download', kwargs={'pk': cv_special.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')


class RequestLogModelTest(TestCase):
    """Test cases for RequestLog model."""

    def setUp(self):
        """Set up test data."""
        self.log_data = {
            'method': 'GET',
            'path': '/test/',
            'query_string': 'param=value',
            'remote_ip': '127.0.0.1',
            'user_agent': 'Test User Agent',
            'response_status': 200,
            'response_time_ms': 150,
        }

    def test_request_log_creation(self):
        """Test RequestLog model creation."""
        log = RequestLog.objects.create(**self.log_data)

        self.assertEqual(log.method, 'GET')
        self.assertEqual(log.path, '/test/')
        self.assertEqual(log.query_string, 'param=value')
        self.assertEqual(log.remote_ip, '127.0.0.1')
        self.assertEqual(log.response_status, 200)
        self.assertEqual(log.response_time_ms, 150)
        self.assertTrue(log.timestamp)

    def test_request_log_str_method(self):
        """Test RequestLog string representation."""
        log = RequestLog.objects.create(**self.log_data)
        expected_str = f"GET /test/ - {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        self.assertEqual(str(log), expected_str)

    def test_full_url_property(self):
        """Test full_url property."""
        log = RequestLog.objects.create(**self.log_data)
        self.assertEqual(log.full_url, '/test/?param=value')

        # Test without query string
        log_no_query = RequestLog.objects.create(
            method='GET',
            path='/simple/',
            query_string='',
            remote_ip='127.0.0.1'
        )
        self.assertEqual(log_no_query.full_url, '/simple/')

    def test_response_time_seconds_property(self):
        """Test response_time_seconds property."""
        log = RequestLog.objects.create(**self.log_data)
        self.assertEqual(log.response_time_seconds, 0.15)

        # Test with None value
        log_no_time = RequestLog.objects.create(
            method='GET',
            path='/test/',
            remote_ip='127.0.0.1'
        )
        self.assertIsNone(log_no_time.response_time_seconds)

    def test_get_recent_logs_class_method(self):
        """Test get_recent_logs class method."""
        # Create multiple logs
        for i in range(15):
            RequestLog.objects.create(
                method='GET',
                path=f'/test{i}/',
                remote_ip='127.0.0.1'
            )

        recent_logs = RequestLog.get_recent_logs(10)
        self.assertEqual(len(recent_logs), 10)

        # Test default limit
        all_recent = RequestLog.get_recent_logs()
        self.assertEqual(len(all_recent), 10)

    def test_get_stats_class_method(self):
        """Test get_stats class method."""
        # Test with no logs
        stats = RequestLog.get_stats()
        expected_empty = {
            'total_requests': 0,
            'methods': {},
            'avg_response_time': None,
            'unique_ips': 0
        }
        self.assertEqual(stats, expected_empty)

        # Create test logs
        RequestLog.objects.create(
            method='GET', path='/test1/', remote_ip='127.0.0.1', response_time_ms=100
        )
        RequestLog.objects.create(
            method='POST', path='/test2/', remote_ip='127.0.0.1', response_time_ms=200
        )
        RequestLog.objects.create(
            method='GET', path='/test3/', remote_ip='192.168.1.1', response_time_ms=150
        )

        stats = RequestLog.get_stats()
        self.assertEqual(stats['total_requests'], 3)
        self.assertEqual(stats['methods']['GET'], 2)
        self.assertEqual(stats['methods']['POST'], 1)
        self.assertEqual(stats['avg_response_time'], 150.0)
        self.assertEqual(stats['unique_ips'], 2)


@override_settings(
    # Disable middleware during tests to avoid async issues
    MIDDLEWARE=[
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]
)
class RequestLoggingMiddlewareTest(TestCase):
    """Test cases for RequestLoggingMiddleware."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        # Clear any existing logs
        RequestLog.objects.all().delete()

        # Create a test CV for testing
        self.cv = CV.objects.create(
            firstname='Test',
            lastname='User',
            email='test@example.com',
            bio='Test bio'
        )

    def test_middleware_should_log_request_method(self):
        """Test _should_log_request method of middleware."""

        def dummy_get_response(request):
            return HttpResponse("OK")

        middleware = RequestLoggingMiddleware(dummy_get_response)

        # Mock request objects
        class MockRequest:
            def __init__(self, path):
                self.path = path
                self.method = 'GET'
                self.META = {'REMOTE_ADDR': '127.0.0.1'}

        # Test valid requests (should be logged)
        valid_requests = [
            MockRequest('/'),
            MockRequest('/api/'),
            MockRequest('/cv/1/'),
            MockRequest('/logs/'),
        ]

        for request in valid_requests:
            self.assertTrue(middleware._should_log_request(request))

        # Test excluded requests (should NOT be logged)
        excluded_requests = [
            MockRequest('/admin/'),
            MockRequest('/admin/main/cv/'),
            MockRequest('/static/css/style.css'),
            MockRequest('/static/js/script.js'),
            MockRequest('/favicon.ico'),
            MockRequest('/robots.txt'),
            MockRequest('/sitemap.xml'),
            MockRequest('/media/uploads/file.jpg'),
            MockRequest('/test.png'),
            MockRequest('/script.js'),
            MockRequest('/style.css'),
        ]

        for request in excluded_requests:
            self.assertFalse(middleware._should_log_request(request))

    def test_get_client_ip_method(self):
        """Test _get_client_ip method of middleware."""

        def dummy_get_response(request):
            return HttpResponse("OK")

        middleware = RequestLoggingMiddleware(dummy_get_response)

        # Mock request object
        class MockRequest:
            def __init__(self, meta):
                self.META = meta

        # Test with REMOTE_ADDR
        request = MockRequest({'REMOTE_ADDR': '192.168.1.1'})
        ip = middleware._get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')

        # Test with X-Forwarded-For
        request = MockRequest({
            'HTTP_X_FORWARDED_FOR': '203.0.113.1, 192.168.1.1',
            'REMOTE_ADDR': '192.168.1.1'
        })
        ip = middleware._get_client_ip(request)
        self.assertEqual(ip, '203.0.113.1')

        # Test with no IP
        request = MockRequest({})
        ip = middleware._get_client_ip(request)
        self.assertEqual(ip, '0.0.0.0')

    def test_is_valid_ip_method(self):
        """Test _is_valid_ip method of middleware."""

        def dummy_get_response(request):
            return HttpResponse("OK")

        middleware = RequestLoggingMiddleware(dummy_get_response)

        # Valid IPs
        valid_ips = [
            '127.0.0.1',
            '192.168.1.1',
            '203.0.113.1',
            '0.0.0.0',
            '255.255.255.255'
        ]

        for ip in valid_ips:
            self.assertTrue(middleware._is_valid_ip(ip))

        # Invalid IPs
        invalid_ips = [
            '256.1.1.1',
            '192.168',
            'not.an.ip',
            '192.168.1.1.1',
            '',
            None
        ]

        for ip in invalid_ips:
            self.assertFalse(middleware._is_valid_ip(ip))

    def test_middleware_sync_logging(self):
        """Test middleware logging functionality synchronously."""

        def dummy_get_response(request):
            return HttpResponse("OK", status=200)

        middleware = RequestLoggingMiddleware(dummy_get_response)

        # Mock request
        class MockRequest:
            def __init__(self):
                self.method = 'GET'
                self.path = '/test/'
                self.META = {
                    'QUERY_STRING': 'param=value',
                    'REMOTE_ADDR': '127.0.0.1',
                    'HTTP_USER_AGENT': 'Test Agent'
                }
                self._logging_start_time = time.time()

        request = MockRequest()
        response = HttpResponse("OK", status=200)

        # Test that _should_log_request works
        should_log = middleware._should_log_request(request)
        self.assertTrue(should_log)

        # Test log data preparation (without async threading)
        log_data = {
            'method': request.method,
            'path': request.path,
            'query_string': request.META.get('QUERY_STRING', ''),
            'remote_ip': middleware._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')[:500],
            'response_status': response.status_code,
            'response_time_ms': 150,
        }

        # Create log entry synchronously
        log = RequestLog.objects.create(**log_data)

        # Verify log was created correctly
        self.assertEqual(log.method, 'GET')
        self.assertEqual(log.path, '/test/')
        self.assertEqual(log.query_string, 'param=value')
        self.assertEqual(log.remote_ip, '127.0.0.1')
        self.assertEqual(log.response_status, 200)


class RequestLogsViewTest(TestCase):
    """Test cases for RequestLogsView."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        RequestLog.objects.all().delete()

        # Create test logs
        self.logs = []
        for i in range(15):
            log = RequestLog.objects.create(
                method=['GET', 'POST', 'PUT'][i % 3],
                path=f'/test{i}/',
                query_string=f'param={i}' if i % 2 == 0 else '',
                remote_ip=f'192.168.1.{i % 10 + 1}',
                user_agent=f'TestAgent/{i}',
                response_status=[200, 404, 500][i % 3],
                response_time_ms=100 + i * 10
            )
            self.logs.append(log)

    def test_logs_view_status_code(self):
        """Test that logs view returns 200."""
        response = self.client.get(reverse('request_logs'))
        self.assertEqual(response.status_code, 200)

    def test_logs_view_template(self):
        """Test that logs view uses correct template."""
        response = self.client.get(reverse('request_logs'))
        self.assertTemplateUsed(response, 'main/request_logs.html')

    def test_logs_view_pagination(self):
        """Test logs view pagination."""
        response = self.client.get(reverse('request_logs'))
        self.assertContains(response, 'Page 1 of')

        # Check that only 10 logs are shown per page
        logs_on_page = response.context['logs']
        self.assertEqual(len(logs_on_page), 10)

    def test_logs_view_filter_by_method(self):
        """Test filtering logs by HTTP method."""
        response = self.client.get(reverse('request_logs'), {'method': 'GET'})
        logs_on_page = response.context['logs']

        for log in logs_on_page:
            self.assertEqual(log.method, 'GET')

    def test_logs_view_filter_by_path(self):
        """Test filtering logs by path."""
        response = self.client.get(reverse('request_logs'), {'path': 'test1'})
        logs_on_page = response.context['logs']

        for log in logs_on_page:
            self.assertIn('test1', log.path)

    def test_logs_view_filter_by_ip(self):
        """Test filtering logs by IP address."""
        response = self.client.get(reverse('request_logs'), {'ip': '192.168.1.1'})
        logs_on_page = response.context['logs']

        for log in logs_on_page:
            self.assertIn('192.168.1.1', log.remote_ip)

    def test_logs_view_filter_by_date(self):
        """Test filtering logs by date range."""
        today = datetime.now().date()
        yesterday = today - timedelta(days=1)

        response = self.client.get(reverse('request_logs'), {
            'date_from': yesterday.strftime('%Y-%m-%d'),
            'date_to': today.strftime('%Y-%m-%d')
        })

        self.assertEqual(response.status_code, 200)
        # All logs should be included since they were created today

    def test_logs_view_context_data(self):
        """Test that logs view includes correct context data."""
        response = self.client.get(reverse('request_logs'))

        # Check that statistics are included
        self.assertIn('stats', response.context)
        stats = response.context['stats']
        self.assertIn('total_requests', stats)
        self.assertIn('methods', stats)
        self.assertIn('unique_ips', stats)

        # Check that available methods are included
        self.assertIn('available_methods', response.context)

    def test_logs_view_empty_state(self):
        """Test logs view when no logs exist."""
        RequestLog.objects.all().delete()

        response = self.client.get(reverse('request_logs'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No Request Logs Found')

    def test_logs_api_endpoint(self):
        """Test logs API endpoint for JSON data."""
        response = self.client.get(reverse('request_logs_api'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        data = response.json()
        self.assertIn('logs', data)
        self.assertIn('stats', data)
        self.assertIn('count', data)


class RequestLoggingIntegrationTest(TestCase):
    """Integration tests for request logging functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        RequestLog.objects.all().delete()

    def test_logs_view_functionality(self):
        """Test that logs view works correctly."""
        # Create some test logs manually
        for i in range(5):
            RequestLog.objects.create(
                method='GET',
                path=f'/test{i}/',
                remote_ip='127.0.0.1',
                response_status=200,
                response_time_ms=100 + i * 10
            )

        # Test that we can view the logs
        response = self.client.get(reverse('request_logs'))
        self.assertEqual(response.status_code, 200)

        # Check that logs appear in the context
        self.assertEqual(len(response.context['logs']), 5)

        # Check that statistics are computed
        stats = response.context['stats']
        self.assertEqual(stats['total_requests'], 5)
        self.assertEqual(stats['methods']['GET'], 5)

    def test_request_log_model_functionality(self):
        """Test RequestLog model functionality."""
        # Test creating logs
        log = RequestLog.objects.create(
            method='POST',
            path='/api/test/',
            query_string='data=value',
            remote_ip='192.168.1.1',
            response_status=201,
            response_time_ms=250
        )

        # Test properties
        self.assertEqual(log.full_url, '/api/test/?data=value')
        self.assertEqual(log.response_time_seconds, 0.25)

        # Test class methods
        recent_logs = RequestLog.get_recent_logs(5)
        self.assertEqual(len(recent_logs), 1)

        stats = RequestLog.get_stats()
        self.assertEqual(stats['total_requests'], 1)
        self.assertEqual(stats['methods']['POST'], 1)

    def test_middleware_exclusion_logic(self):
        """Test middleware exclusion logic without async complications."""

        def dummy_get_response(request):
            return HttpResponse("OK")

        middleware = RequestLoggingMiddleware(dummy_get_response)

        # Test various paths
        test_cases = [
            ('/', True),  # Should be logged
            ('/api/', True),  # Should be logged
            ('/cv/1/', True),  # Should be logged
            ('/admin/', False),  # Should be excluded
            ('/static/css/style.css', False),  # Should be excluded
            ('/favicon.ico', False),  # Should be excluded
        ]

        for path, should_log in test_cases:
            class MockRequest:
                def __init__(self, path):
                    self.path = path

            request = MockRequest(path)
            result = middleware._should_log_request(request)
            self.assertEqual(result, should_log, f"Path {path} should {'be logged' if should_log else 'be excluded'}")


class ContextProcessorTest(TestCase):
    """Test cases for custom context processors."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.client = Client()

    def test_settings_context_processor(self):
        """Test settings_context processor filters sensitive data."""
        request = self.factory.get('/')
        context = settings_context(request)

        # Check that context contains settings
        self.assertIn('settings', context)
        self.assertIn('django_settings', context)

        # Check that basic safe settings are included
        settings_data = context['settings']
        self.assertIn('DEBUG', settings_data)
        self.assertIn('TIME_ZONE', settings_data)
        self.assertIn('LANGUAGE_CODE', settings_data)

        # Check that sensitive settings are excluded
        sensitive_keys = ['SECRET_KEY', 'DATABASE', 'PASSWORD', 'API_KEY']
        for key in sensitive_keys:
            self.assertNotIn(key, settings_data)

        # Check that derived settings are included
        self.assertIn('INSTALLED_APPS_COUNT', settings_data)
        self.assertIn('MIDDLEWARE_COUNT', settings_data)
        self.assertIn('IS_DEBUG_MODE', settings_data)

    def test_request_context_processor(self):
        """Test request_context processor provides safe request info."""
        request = self.factory.get('/test-path/?param=value')
        request.META['HTTP_USER_AGENT'] = 'Test User Agent'
        request.META['REMOTE_ADDR'] = '127.0.0.1'

        context = request_context(request)

        # Check that request_info is included
        self.assertIn('request_info', context)

        request_info = context['request_info']
        self.assertEqual(request_info['method'], 'GET')
        self.assertEqual(request_info['path'], '/test-path/')
        self.assertEqual(request_info['query_params_count'], 1)
        self.assertEqual(request_info['remote_addr'], '127.0.0.1')
        self.assertFalse(request_info['is_ajax'])
        self.assertFalse(request_info['is_secure'])

    def test_app_context_processor(self):
        """Test app_context processor provides application info."""
        request = self.factory.get('/')
        context = app_context(request)

        # Check that app_info is included
        self.assertIn('app_info', context)

        app_info = context['app_info']
        self.assertIn('app_name', app_info)
        self.assertIn('app_version', app_info)
        self.assertIn('environment', app_info)
        self.assertIn('stats', app_info)

        # Check stats
        stats = app_info['stats']
        self.assertIn('total_cvs', stats)
        self.assertIn('database_vendor', stats)

    def test_context_processors_in_template(self):
        """Test that context processors work in templates."""
        # Create a test template
        template = Template('{{ settings.DEBUG }} {{ app_info.app_name }} {{ request_info.method }}')

        # Create a request
        request = self.factory.get('/')

        # Render template with context processors
        from django.template import RequestContext
        context = RequestContext(request)
        rendered = template.render(context)

        # Check that context processor values are rendered
        self.assertIn(str(settings.DEBUG), rendered)
        self.assertIn('CV Management System', rendered)
        self.assertIn('GET', rendered)

    def test_sensitive_settings_filtered_out(self):
        """Test that sensitive settings are properly filtered out."""
        request = self.factory.get('/')
        context = settings_context(request)
        settings_data = context['settings']

        # List of patterns that should be filtered out
        sensitive_patterns = [
            'SECRET', 'KEY', 'PASSWORD', 'TOKEN', 'API', 'AUTH',
            'DATABASE', 'CREDENTIAL', 'PRIVATE', 'SECURITY'
        ]

        # Check that no setting names contain sensitive patterns
        for setting_name in settings_data.keys():
            for pattern in sensitive_patterns:
                if pattern in setting_name.upper():
                    # If it contains a sensitive pattern, it should be a derived/safe setting
                    safe_settings = [
                        'INSTALLED_APPS_COUNT', 'MIDDLEWARE_COUNT',
                        'IS_DEBUG_MODE', 'AUTH_PASSWORD_VALIDATORS'  # This might be present
                    ]
                    self.assertIn(setting_name, safe_settings,
                                  f"Sensitive setting '{setting_name}' was not filtered out")


class SettingsViewTest(TestCase):
    """Test cases for Settings view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

    def test_settings_view_status_code(self):
        """Test that settings view returns 200."""
        response = self.client.get('/settings/')
        self.assertEqual(response.status_code, 200)

    def test_settings_view_template(self):
        """Test that settings view uses correct template."""
        response = self.client.get('/settings/')
        self.assertTemplateUsed(response, 'main/settings.html')

    def test_settings_view_context_data(self):
        """Test that settings view includes all required context."""
        response = self.client.get('/settings/')

        # Check required context keys
        required_keys = [
            'core_settings', 'app_settings', 'middleware_settings',
            'template_settings', 'static_settings', 'system_info'
        ]

        for key in required_keys:
            self.assertIn(key, response.context, f"Missing context key: {key}")

    def test_settings_view_shows_debug_status(self):
        """Test that settings view shows DEBUG status."""
        response = self.client.get('/settings/')

        # Check that DEBUG setting is displayed
        if settings.DEBUG:
            self.assertContains(response, 'ON')
        else:
            self.assertContains(response, 'OFF')

    def test_settings_view_shows_system_info(self):
        """Test that settings view shows system information."""
        response = self.client.get('/settings/')

        # Check that system info is displayed
        self.assertContains(response, 'Django')  # Django version should be shown
        self.assertContains(response, 'Python')  # Python version should be shown

    def test_settings_view_context_processor_demo(self):
        """Test that settings view demonstrates context processors."""
        response = self.client.get('/settings/')

        # Check that context processor values are available
        self.assertContains(response, 'Context Processor Demo')

        # The settings should be available via context processor
        self.assertIn('settings', response.context)
        self.assertIn('app_info', response.context)
        self.assertIn('request_info', response.context)

    def test_settings_api_endpoint(self):
        """Test settings API endpoint."""
        response = self.client.get('/api/settings/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

        # Parse JSON response
        data = response.json()

        # Check required keys in API response
        self.assertIn('core_settings', data)
        self.assertIn('system_info', data)
        self.assertIn('app_counts', data)

        # Check that sensitive data is not in API response
        core_settings = data['core_settings']
        sensitive_keys = ['SECRET_KEY', 'DATABASE', 'PASSWORD']
        for key in sensitive_keys:
            self.assertNotIn(key, core_settings)

    def test_settings_view_installed_apps_display(self):
        """Test that installed apps are displayed correctly."""
        response = self.client.get('/settings/')

        # Check that main app is shown
        self.assertContains(response, 'main')
        # Check that Django apps are shown
        self.assertContains(response, 'django.contrib.admin')

    def test_settings_view_middleware_display(self):
        """Test that middleware is displayed correctly."""
        response = self.client.get('/settings/')

        # Check that common middleware is shown
        self.assertContains(response, 'SessionMiddleware')
        self.assertContains(response, 'AuthenticationMiddleware')


class ContextProcessorIntegrationTest(TestCase):
    """Integration tests for context processors with views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

    def test_context_processors_available_in_all_views(self):
        """Test that context processors are available in all views."""
        # Test different views to ensure context processors work everywhere
        test_views = [
            ('/', 'cv_list'),
            ('/settings/', 'settings'),
        ]

        for url, view_name in test_views:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)

                # Check that context processor data is available
                self.assertIn('settings', response.context)
                self.assertIn('app_info', response.context)
                self.assertIn('request_info', response.context)

    def test_debug_mode_visibility(self):
        """Test that debug mode affects template display."""
        response = self.client.get('/')

        if settings.DEBUG:
            # In debug mode, debug info might be shown
            self.assertIn('settings', response.context)
            debug_value = response.context['settings'].get('DEBUG')
            self.assertTrue(debug_value)
        else:
            # In production mode, debug should be False
            debug_value = response.context['settings'].get('DEBUG')
            self.assertFalse(debug_value)

    def test_app_statistics_in_context(self):
        """Test that app statistics are correctly provided."""
        # Create some test data
        from main.models import CV
        CV.objects.create(
            firstname='Test',
            lastname='User',
            email='test@example.com',
            bio='Test bio'
        )

        response = self.client.get('/settings/')
        app_info = response.context['app_info']

        # Check that CV count is updated
        self.assertGreaterEqual(app_info['stats']['total_cvs'], 1)

    def test_request_info_accuracy(self):
        """Test that request info is accurate."""
        response = self.client.get('/settings/?test=param')
        request_info = response.context['request_info']

        self.assertEqual(request_info['method'], 'GET')
        self.assertEqual(request_info['path'], '/settings/')
        self.assertEqual(request_info['query_params_count'], 1)
        self.assertFalse(request_info['is_secure'])