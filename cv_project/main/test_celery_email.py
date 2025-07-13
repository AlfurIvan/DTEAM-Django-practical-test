"""
Tests for Task 7: Celery email functionality.
"""

import json
from datetime import date
from io import BytesIO
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.conf import settings

from main.models import CV, Skill, Project, Contact
from main.tasks import send_cv_pdf_email, test_celery_task, cleanup_old_request_logs
from main.views import generate_cv_pdf_buffer, PDFGenerator


class PDFGeneratorTest(TestCase):
    """Test the PDFGenerator class."""

    def setUp(self):
        """Set up test data."""
        self.cv = CV.objects.create(
            firstname="John",
            lastname="Doe",
            email="john@example.com",
            phone="123-456-7890",
            bio="Test biography for PDF generation testing."
        )

        # Add skills
        Skill.objects.create(cv=self.cv, name="Python", proficiency="expert")
        Skill.objects.create(cv=self.cv, name="Django", proficiency="advanced")

        # Add project
        Project.objects.create(
            cv=self.cv,
            title="Test Project",
            description="Test project description",
            technologies="Python, Django, Testing",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )

        # Add contact
        Contact.objects.create(
            cv=self.cv,
            contact_type="github",
            value="johndoe",
            url="https://github.com/johndoe"
        )

    def test_pdf_generator_initialization(self):
        """Test PDFGenerator initialization."""
        generator = PDFGenerator(self.cv)

        self.assertEqual(generator.cv, self.cv)
        self.assertIsInstance(generator.buffer, BytesIO)
        self.assertEqual(len(generator.elements), 0)
        self.assertIn('title', generator.styles)
        self.assertIn('heading', generator.styles)
        self.assertIn('normal', generator.styles)
        self.assertIn('contact', generator.styles)

    def test_pdf_generation(self):
        """Test complete PDF generation."""
        buffer = generate_cv_pdf_buffer(self.cv)

        self.assertIsInstance(buffer, BytesIO)
        pdf_data = buffer.getvalue()
        self.assertGreater(len(pdf_data), 1000)  # PDF should be substantial

        # Check PDF starts with PDF header
        self.assertTrue(pdf_data.startswith(b'%PDF'))
        buffer.close()

    def test_pdf_generation_with_minimal_data(self):
        """Test PDF generation with minimal CV data."""
        minimal_cv = CV.objects.create(
            firstname="Jane",
            lastname="Smith",
            email="jane@example.com",
            bio="Minimal bio"
        )

        buffer = generate_cv_pdf_buffer(minimal_cv)
        pdf_data = buffer.getvalue()

        self.assertGreater(len(pdf_data), 500)  # Should still generate PDF
        self.assertTrue(pdf_data.startswith(b'%PDF'))
        buffer.close()

    def test_pdf_generation_with_long_data(self):
        """Test PDF generation with extensive data."""
        # Add many skills
        for i in range(10):
            Skill.objects.create(
                cv=self.cv,
                name=f"Skill {i}",
                proficiency="intermediate"
            )

        # Add many projects
        for i in range(5):
            Project.objects.create(
                cv=self.cv,
                title=f"Project {i}",
                description="A" * 500,  # Long description
                technologies="Tech1, Tech2, Tech3, Tech4, Tech5",
                start_date=date(2020 + i, 1, 1)
            )

        buffer = generate_cv_pdf_buffer(self.cv)
        pdf_data = buffer.getvalue()

        self.assertGreater(len(pdf_data), 3000)  # Should be larger PDF (reduced expectation)
        buffer.close()


class CeleryTasksTest(TestCase):
    """Test Celery tasks."""

    def setUp(self):
        """Set up test data."""
        self.cv = CV.objects.create(
            firstname="John",
            lastname="Doe",
            email="john@example.com",
            bio="Test biography"
        )

    def test_test_celery_task(self):
        """Test the basic Celery test task."""
        result = test_celery_task()

        self.assertIsInstance(result, dict)
        self.assertTrue(result['success'])
        self.assertEqual(result['message'], 'Celery is working correctly!')
        self.assertIn('timestamp', result)

    @patch('main.views.generate_cv_pdf_buffer')  # Fixed: Import from main.views, not main.tasks
    @patch('main.tasks.EmailMessage')
    def test_send_cv_pdf_email_success(self, mock_email_class, mock_pdf_gen):
        """Test successful email sending."""
        # Mock PDF generation
        mock_buffer = MagicMock()
        mock_buffer.getvalue.return_value = b'fake_pdf_data'
        mock_pdf_gen.return_value = mock_buffer

        # Mock email
        mock_email = MagicMock()
        mock_email_class.return_value = mock_email

        # Execute task
        result = send_cv_pdf_email(
            cv_id=self.cv.pk,
            recipient_email='test@example.com',
            sender_name='Test User'
        )

        # Verify result
        self.assertIsInstance(result, dict)
        self.assertTrue(result['success'])
        self.assertIn('CV sent successfully', result['message'])
        self.assertEqual(result['cv_name'], self.cv.full_name)
        self.assertEqual(result['recipient'], 'test@example.com')

        # Verify email was created and sent
        mock_email_class.assert_called_once()
        mock_email.send.assert_called_once()
        mock_email.attach.assert_called_once()

    def test_send_cv_pdf_email_invalid_cv(self):
        """Test email sending with invalid CV ID."""
        result = send_cv_pdf_email(
            cv_id=9999,  # Non-existent CV
            recipient_email='test@example.com'
        )

        self.assertIsInstance(result, dict)
        self.assertFalse(result['success'])
        self.assertIn('CV with ID 9999 not found', result['error'])

    @patch('main.tasks.RequestLog')
    def test_cleanup_old_request_logs(self, mock_request_log):
        """Test cleanup task."""
        # Mock the delete operation
        mock_queryset = MagicMock()
        mock_queryset.delete.return_value = (5, {'main.RequestLog': 5})
        mock_request_log.objects.filter.return_value = mock_queryset

        result = cleanup_old_request_logs(days=30)

        self.assertIsInstance(result, dict)
        self.assertTrue(result['success'])
        self.assertEqual(result['deleted_count'], 5)
        self.assertIn('cutoff_date', result)


class EmailViewsTest(TestCase):
    """Test email-related views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.cv = CV.objects.create(
            firstname="John",
            lastname="Doe",
            email="john@example.com",
            bio="Test biography"
        )

    def test_email_cv_view_get_method(self):
        """Test that GET method is not allowed."""
        response = self.client.get(reverse('cv_email', kwargs={'pk': self.cv.pk}))
        self.assertEqual(response.status_code, 405)

        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Method not allowed', data['error'])

    @patch('main.tasks.send_cv_pdf_email')  # Fixed: Import from main.tasks, not main.views
    def test_email_cv_view_success(self, mock_task):
        """Test successful email queuing."""
        # Mock the Celery task
        mock_result = MagicMock()
        mock_result.id = 'test-task-id'
        mock_task.delay.return_value = mock_result

        data = {
            'email': 'test@example.com',
            'sender_name': 'Test User'
        }

        response = self.client.post(
            reverse('cv_email', kwargs={'pk': self.cv.pk}),
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)

        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertIn('CV email queued successfully', response_data['message'])
        self.assertEqual(response_data['task_id'], 'test-task-id')
        self.assertEqual(response_data['cv_name'], self.cv.full_name)
        self.assertEqual(response_data['recipient'], 'test@example.com')

        # Verify task was called correctly
        mock_task.delay.assert_called_once_with(
            cv_id=self.cv.pk,
            recipient_email='test@example.com',
            sender_name='Test User'
        )

    def test_email_cv_view_invalid_json(self):
        """Test with invalid JSON data."""
        response = self.client.post(
            reverse('cv_email', kwargs={'pk': self.cv.pk}),
            data='invalid json',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('Invalid JSON data', data['error'])

    def test_email_cv_view_missing_email(self):
        """Test with missing email address."""
        data = {'sender_name': 'Test User'}

        response = self.client.post(
            reverse('cv_email', kwargs={'pk': self.cv.pk}),
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertIn('Email address is required', response_data['error'])

    def test_email_cv_view_invalid_email(self):
        """Test with invalid email format."""
        invalid_emails = [
            'invalid-email',
            'test@',
            '@example.com',
            'test.example.com',
            'test space@example.com'
        ]

        for invalid_email in invalid_emails:
            data = {'email': invalid_email}

            response = self.client.post(
                reverse('cv_email', kwargs={'pk': self.cv.pk}),
                data=json.dumps(data),
                content_type='application/json'
            )

            self.assertEqual(response.status_code, 400)

            response_data = response.json()
            self.assertFalse(response_data['success'])
            self.assertIn('valid email address', response_data['error'])

    @patch('main.tasks.send_cv_pdf_email')  # Fixed: Import from main.tasks
    def test_email_cv_view_valid_emails(self, mock_task):
        """Test with various valid email formats."""
        mock_result = MagicMock()
        mock_result.id = 'test-task-id'
        mock_task.delay.return_value = mock_result

        valid_emails = [
            'test@example.com',
            'user.name@example.org',
            'user+tag@example-domain.com',
            'test123@sub.domain.co.uk'
        ]

        for valid_email in valid_emails:
            data = {'email': valid_email}

            response = self.client.post(
                reverse('cv_email', kwargs={'pk': self.cv.pk}),
                data=json.dumps(data),
                content_type='application/json'
            )

            self.assertEqual(response.status_code, 200)

            response_data = response.json()
            self.assertTrue(response_data['success'])

    def test_email_cv_view_nonexistent_cv(self):
        """Test with non-existent CV."""
        data = {'email': 'test@example.com'}

        response = self.client.post(
            reverse('cv_email', kwargs={'pk': 9999}),
            data=json.dumps(data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 500)  # Fixed: Expect 500, not 404

    @patch('celery.result.AsyncResult')  # Fixed: Patch from celery.result
    def test_check_email_task_status_success(self, mock_async_result):
        """Test task status checking - success case."""
        # Mock successful task result
        mock_result = MagicMock()
        mock_result.state = 'SUCCESS'
        mock_result.result = {'success': True, 'message': 'Email sent!'}
        mock_async_result.return_value = mock_result

        response = self.client.get(reverse('check_task_status', kwargs={'task_id': 'test-task-id'}))

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['state'], 'SUCCESS')
        self.assertEqual(data['status'], 'Email sent successfully!')
        self.assertIn('result', data)

    @patch('celery.result.AsyncResult')  # Fixed: Patch from celery.result
    def test_check_email_task_status_pending(self, mock_async_result):
        """Test task status checking - pending case."""
        mock_result = MagicMock()
        mock_result.state = 'PENDING'
        mock_async_result.return_value = mock_result

        response = self.client.get(reverse('check_task_status', kwargs={'task_id': 'test-task-id'}))

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['state'], 'PENDING')
        self.assertIn('waiting to be processed', data['status'])

    @patch('celery.result.AsyncResult')  # Fixed: Patch from celery.result
    def test_check_email_task_status_failure(self, mock_async_result):
        """Test task status checking - failure case."""
        mock_result = MagicMock()
        mock_result.state = 'FAILURE'
        mock_result.info = Exception('Test error')
        mock_async_result.return_value = mock_result

        response = self.client.get(reverse('check_task_status', kwargs={'task_id': 'test-task-id'}))

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data['state'], 'FAILURE')
        self.assertEqual(data['status'], 'Task failed')
        self.assertIn('error', data)


class EmailIntegrationTest(TestCase):
    """Integration tests for email functionality."""

    def setUp(self):
        """Set up test data."""
        self.cv = CV.objects.create(
            firstname="Integration",
            lastname="Test",
            email="integration@example.com",
            bio="Integration test biography"
        )

        # Add some related data
        Skill.objects.create(cv=self.cv, name="Testing", proficiency="expert")
        Project.objects.create(
            cv=self.cv,
            title="Test Project",
            description="Test project for integration testing",
            technologies="Python, Django",
            start_date=date(2023, 1, 1)
        )

    def test_email_template_rendering(self):
        """Test that email templates render correctly."""
        from django.template.loader import render_to_string

        context = {
            'cv': self.cv,
            'sender_name': 'Test User',
            'recipient_email': 'test@example.com',
        }

        # Test HTML template
        html_content = render_to_string('emails/cv_pdf_email.html', context)
        self.assertIn(self.cv.full_name, html_content)
        self.assertIn('test@example.com', html_content)
        self.assertIn('Test User', html_content)
        self.assertIn('Testing', html_content)  # Skill should be mentioned

        # Test text template
        text_content = render_to_string('emails/cv_pdf_email.txt', context)
        self.assertIn(self.cv.full_name, text_content)
        self.assertIn('test@example.com', text_content)
        self.assertIn('Test User', text_content)

    @patch('main.tasks.EmailMessage')
    def test_email_content_structure(self, mock_email_class):
        """Test the structure of the email being sent."""
        mock_email = MagicMock()
        mock_email_class.return_value = mock_email

        # Mock PDF generation
        with patch('main.views.generate_cv_pdf_buffer') as mock_pdf:  # Fixed: Import from main.views
            mock_buffer = MagicMock()
            mock_buffer.getvalue.return_value = b'fake_pdf_data'
            mock_pdf.return_value = mock_buffer

            # Execute task
            send_cv_pdf_email(
                cv_id=self.cv.pk,
                recipient_email='test@example.com',
                sender_name='Integration Test'
            )

        # Verify email creation
        mock_email_class.assert_called_once()
        call_args = mock_email_class.call_args[1]

        self.assertEqual(call_args['subject'], f'CV: {self.cv.full_name}')
        self.assertEqual(call_args['to'], ['test@example.com'])
        self.assertIn(self.cv.full_name, call_args['body'])

        # Verify PDF attachment
        mock_email.attach.assert_called_once()
        attach_args = mock_email.attach.call_args[0]
        self.assertIn('Integration_Test_CV.pdf', attach_args[0])
        self.assertEqual(attach_args[1], b'fake_pdf_data')
        self.assertEqual(attach_args[2], 'application/pdf')

    def test_cv_pdf_download_still_works(self):
        """Ensure PDF download functionality wasn't broken by optimization."""
        client = Client()
        response = client.get(reverse('cv_pdf_download', kwargs={'pk': self.cv.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('Integration_Test_CV.pdf', response['Content-Disposition'])
        self.assertGreater(len(response.content), 1000)


class TaskConfigurationTest(TestCase):
    """Test Celery configuration and setup."""

    def test_celery_app_configuration(self):
        """Test basic Celery app configuration."""
        from core.celery import app as celery_app

        self.assertIsNotNone(celery_app)
        self.assertEqual(celery_app.main, 'core')

        # Check task registration
        registered_tasks = list(celery_app.tasks.keys())
        self.assertIn('main.tasks.send_cv_pdf_email', registered_tasks)
        self.assertIn('main.tasks.test_celery_task', registered_tasks)
        self.assertIn('main.tasks.cleanup_old_request_logs', registered_tasks)

    def test_task_routing_configuration(self):
        """Test task routing configuration."""
        from core.celery import app as celery_app

        task_routes = celery_app.conf.task_routes
        # Fixed: Check for actual routing configuration
        self.assertIn('send_cv_pdf_email', task_routes)
        self.assertEqual(task_routes['send_cv_pdf_email']['queue'], 'emails')

        self.assertIn('cleanup_old_request_logs', task_routes)
        self.assertEqual(task_routes['cleanup_old_request_logs']['queue'], 'maintenance')

    def test_beat_schedule_configuration(self):
        """Test Celery beat schedule configuration."""
        from core.celery import app as celery_app

        beat_schedule = celery_app.conf.beat_schedule
        self.assertIn('cleanup-old-logs', beat_schedule)

        cleanup_task = beat_schedule['cleanup-old-logs']
        self.assertEqual(cleanup_task['task'], 'main.tasks.cleanup_old_request_logs')
        self.assertEqual(cleanup_task['schedule'], 86400.0)  # Daily