"""
Views for the CV management system.
"""
import json
import platform
import re
import sys
from datetime import datetime, timedelta
from io import BytesIO

import django
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView, TemplateView
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from .models import CV, RequestLog


class CVListView(ListView):
    """View to display a list of all CVs."""
    model = CV
    template_name = 'main/cv_list.html'
    context_object_name = 'cvs'
    paginate_by = 10

    def get_queryset(self):
        """Optimize database queries by using select_related and prefetch_related."""
        return CV.objects.select_related().prefetch_related(
            'skills', 'projects', 'contacts'
        )


class CVDetailView(DetailView):
    """View to display detailed information about a specific CV."""
    model = CV
    template_name = 'main/cv_detail.html'
    context_object_name = 'cv'

    def get_queryset(self):
        """Optimize database queries by using select_related and prefetch_related."""
        return CV.objects.select_related().prefetch_related(
            'skills', 'projects', 'contacts'
        )


class PDFGenerator:
    """
    Centralized PDF generation class to avoid code duplication.
    Handles all PDF styling and content generation.
    """

    def __init__(self, cv):
        self.cv = cv
        self.buffer = BytesIO()
        self.elements = []
        self.styles = self._create_styles()

    def _create_styles(self):
        """Create and return custom PDF styles."""
        base_styles = getSampleStyleSheet()

        return {
            'title': ParagraphStyle(
                'CustomTitle',
                parent=base_styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#007bff')
            ),
            'heading': ParagraphStyle(
                'CustomHeading',
                parent=base_styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                spaceBefore=20,
                textColor=colors.HexColor('#007bff'),
                borderWidth=1,
                borderColor=colors.HexColor('#007bff'),
                borderPadding=5,
                backColor=colors.HexColor('#f8f9fa')
            ),
            'normal': ParagraphStyle(
                'CustomNormal',
                parent=base_styles['Normal'],
                fontSize=11,
                spaceAfter=12,
                alignment=TA_JUSTIFY
            ),
            'contact': ParagraphStyle(
                'ContactStyle',
                parent=base_styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                alignment=TA_CENTER,
                textColor=colors.HexColor('#666666')
            )
        }

    def _add_header(self):
        """Add CV title and contact information."""
        # Title
        title = Paragraph(self.cv.full_name, self.styles['title'])
        self.elements.append(title)

        # Contact info
        contact_info = f"Email: {self.cv.email}"
        if self.cv.phone:
            contact_info += f" | Phone: {self.cv.phone}"
        contact_para = Paragraph(contact_info, self.styles['contact'])
        self.elements.append(contact_para)
        self.elements.append(Spacer(1, 20))

    def _add_biography(self):
        """Add professional summary section."""
        bio_heading = Paragraph("Professional Summary", self.styles['heading'])
        self.elements.append(bio_heading)
        bio_content = Paragraph(self.cv.bio, self.styles['normal'])
        self.elements.append(bio_content)
        self.elements.append(Spacer(1, 15))

    def _add_skills(self):
        """Add skills section with table layout."""
        if not self.cv.skills.exists():
            return

        skills_heading = Paragraph("Core Skills", self.styles['heading'])
        self.elements.append(skills_heading)

        # Create skills table (2 columns)
        skills_data = []
        skills_row = []

        for skill in self.cv.skills.all():
            skill_text = f"{skill.name}\n{skill.get_proficiency_display()}"
            skills_row.append(skill_text)

            if len(skills_row) == 2:
                skills_data.append(skills_row)
                skills_row = []

        # Add remaining skill if odd number
        if skills_row:
            skills_row.append("")
            skills_data.append(skills_row)

        if skills_data:
            skills_table = Table(skills_data, colWidths=[3*inch, 3*inch])
            skills_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e9ecef')),
            ]))
            self.elements.append(skills_table)
            self.elements.append(Spacer(1, 15))

    def _add_projects(self):
        """Add projects section."""
        if not self.cv.projects.exists():
            return

        projects_heading = Paragraph("Professional Projects", self.styles['heading'])
        self.elements.append(projects_heading)

        for project in self.cv.projects.all():
            # Project title with ongoing indicator
            project_title_text = f"<b>{project.title}</b>"
            if project.is_ongoing:
                project_title_text += " <font color='#28a745'>(Ongoing)</font>"

            # Date range
            date_range = f"{project.start_date.strftime('%b %Y')}"
            if project.end_date:
                date_range += f" - {project.end_date.strftime('%b %Y')}"
            else:
                date_range += " - Present"

            # Add project elements
            self.elements.append(Paragraph(project_title_text, self.styles['normal']))
            self.elements.append(Paragraph(f"<font color='#666666'>{date_range}</font>", self.styles['normal']))
            self.elements.append(Paragraph(project.description, self.styles['normal']))

            # Technologies
            if project.technologies_list:
                tech_text = "<b>Technologies:</b> " + ", ".join(project.technologies_list)
                self.elements.append(Paragraph(tech_text, self.styles['normal']))

            # URL
            if project.url:
                url_text = f"<b>URL:</b> <font color='#007bff'>{project.url}</font>"
                self.elements.append(Paragraph(url_text, self.styles['normal']))

            self.elements.append(Spacer(1, 12))

    def _add_contacts(self):
        """Add contact information section."""
        if not self.cv.contacts.exists():
            return

        contacts_heading = Paragraph("Contact & Social Media", self.styles['heading'])
        self.elements.append(contacts_heading)

        contacts_data = []
        for contact in self.cv.contacts.all():
            contacts_data.append([
                contact.get_contact_type_display(),
                contact.url
            ])

        if contacts_data:
            contacts_table = Table(contacts_data, colWidths=[2*inch, 4*inch])
            contacts_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e9ecef')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#007bff')),
            ]))
            self.elements.append(contacts_table)

    def _add_footer(self):
        """Add footer with generation date."""
        self.elements.append(Spacer(1, 30))
        footer_text = f"Generated on {self.cv.updated_at.strftime('%B %d, %Y')} | {self.cv.full_name} Professional CV"
        footer_para = Paragraph(footer_text, self.styles['contact'])
        self.elements.append(footer_para)

    def generate(self):
        """Generate the complete PDF and return the buffer."""
        # Create PDF document
        doc = SimpleDocTemplate(
            self.buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        # Add all sections
        self._add_header()
        self._add_biography()
        self._add_skills()
        self._add_projects()
        self._add_contacts()
        self._add_footer()

        # Build PDF
        doc.build(self.elements)

        return self.buffer


def generate_cv_pdf_buffer(cv):
    """
    Helper function to generate CV PDF and return as BytesIO buffer.
    Used by both download view and Celery email task.
    """
    generator = PDFGenerator(cv)
    return generator.generate()


def cv_pdf_download(request, pk):
    """Generate and download CV as PDF using ReportLab."""
    cv = get_object_or_404(CV, pk=pk)

    # Generate PDF using helper function
    buffer = generate_cv_pdf_buffer(cv)
    pdf = buffer.getvalue()
    buffer.close()

    # Create HTTP response
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"{cv.full_name.replace(' ', '_')}_CV.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


class RequestLogsView(ListView):
    """View to display recent request logs with filtering and pagination."""
    model = RequestLog
    template_name = 'main/request_logs.html'
    context_object_name = 'logs'
    paginate_by = 10

    def get_queryset(self):
        """Get filtered and ordered request logs."""
        queryset = RequestLog.objects.all().order_by('-timestamp')

        # Apply filters
        filters = {
            'method': self.request.GET.get('method'),
            'path': self.request.GET.get('path'),
            'ip': self.request.GET.get('ip'),
            'date_from': self.request.GET.get('date_from'),
            'date_to': self.request.GET.get('date_to'),
        }

        if filters['method']:
            queryset = queryset.filter(method=filters['method'])

        if filters['path']:
            queryset = queryset.filter(path__icontains=filters['path'])

        if filters['ip']:
            queryset = queryset.filter(remote_ip__icontains=filters['ip'])

        # Date filtering
        if filters['date_from']:
            try:
                date_from = datetime.strptime(filters['date_from'], '%Y-%m-%d')
                queryset = queryset.filter(timestamp__gte=date_from)
            except ValueError:
                pass

        if filters['date_to']:
            try:
                date_to = datetime.strptime(filters['date_to'], '%Y-%m-%d') + timedelta(days=1)
                queryset = queryset.filter(timestamp__lt=date_to)
            except ValueError:
                pass

        return queryset

    def get_context_data(self, **kwargs):
        """Add additional context data for the template."""
        context = super().get_context_data(**kwargs)

        # Add statistics and filter values
        context.update({
            'stats': RequestLog.get_stats(),
            'current_method': self.request.GET.get('method', ''),
            'current_path': self.request.GET.get('path', ''),
            'current_ip': self.request.GET.get('ip', ''),
            'current_date_from': self.request.GET.get('date_from', ''),
            'current_date_to': self.request.GET.get('date_to', ''),
            'available_methods': RequestLog.objects.values_list('method', flat=True).distinct().order_by('method'),
            'recent_summary': self._get_recent_summary(),
        })

        return context

    def _get_recent_summary(self):
        """Get summary of recent activity (last 24 hours)."""
        yesterday = datetime.now() - timedelta(hours=24)
        recent_logs = RequestLog.objects.filter(timestamp__gte=yesterday)

        if not recent_logs.exists():
            return None

        from django.db.models import Count, Avg

        return {
            'total_requests': recent_logs.count(),
            'unique_ips': recent_logs.values('remote_ip').distinct().count(),
            'avg_response_time': recent_logs.filter(
                response_time_ms__isnull=False
            ).aggregate(avg_time=Avg('response_time_ms'))['avg_time'],
            'methods': dict(recent_logs.values('method').annotate(
                count=Count('method')
            ).values_list('method', 'count')),
            'top_paths': list(recent_logs.values('path').annotate(
                count=Count('path')
            ).order_by('-count')[:5].values_list('path', 'count')),
        }


def request_logs_api(request):
    """API endpoint for request logs data (for AJAX requests)."""
    from django.core.serializers.json import DjangoJSONEncoder

    logs = RequestLog.get_recent_logs(20)

    logs_data = [{
        'id': log.id,
        'timestamp': log.timestamp.isoformat(),
        'method': log.method,
        'path': log.path,
        'query_string': log.query_string,
        'remote_ip': log.remote_ip,
        'response_status': log.response_status,
        'response_time_ms': log.response_time_ms,
        'full_url': log.full_url,
    } for log in logs]

    return JsonResponse({
        'logs': logs_data,
        'stats': RequestLog.get_stats(),
        'count': len(logs_data)
    }, encoder=DjangoJSONEncoder)


class SettingsView(TemplateView):
    """View to display Django settings and system information."""
    template_name = 'main/settings.html'

    def get_context_data(self, **kwargs):
        """Add settings and system information to template context."""
        context = super().get_context_data(**kwargs)

        # Categorized settings
        settings_categories = {
            'core_settings': {
                'DEBUG': getattr(settings, 'DEBUG', False),
                'ALLOWED_HOSTS': getattr(settings, 'ALLOWED_HOSTS', []),
                'TIME_ZONE': getattr(settings, 'TIME_ZONE', 'UTC'),
                'LANGUAGE_CODE': getattr(settings, 'LANGUAGE_CODE', 'en-us'),
                'USE_TZ': getattr(settings, 'USE_TZ', True),
                'USE_I18N': getattr(settings, 'USE_I18N', True),
            },
            'app_settings': {
                'INSTALLED_APPS': getattr(settings, 'INSTALLED_APPS', []),
                'ROOT_URLCONF': getattr(settings, 'ROOT_URLCONF', ''),
                'WSGI_APPLICATION': getattr(settings, 'WSGI_APPLICATION', ''),
                'DEFAULT_AUTO_FIELD': getattr(settings, 'DEFAULT_AUTO_FIELD', ''),
            },
            'middleware_settings': {
                'MIDDLEWARE': getattr(settings, 'MIDDLEWARE', []),
            },
            'template_settings': {
                'TEMPLATES': getattr(settings, 'TEMPLATES', []),
            },
            'static_settings': {
                'STATIC_URL': getattr(settings, 'STATIC_URL', '/static/'),
                'STATICFILES_DIRS': getattr(settings, 'STATICFILES_DIRS', []),
                'STATICFILES_FINDERS': getattr(settings, 'STATICFILES_FINDERS', []),
            },
        }

        # DRF settings if available
        if hasattr(settings, 'REST_FRAMEWORK'):
            settings_categories['drf_settings'] = getattr(settings, 'REST_FRAMEWORK', {})

        # System information
        system_info = {
            'python_version': sys.version,
            'django_version': django.get_version(),
            'platform': platform.platform(),
            'architecture': platform.architecture(),
            'processor': platform.processor(),
            'hostname': platform.node(),
            'current_time': datetime.now(),
        }

        # Safe environment variables
        safe_env_vars = self._get_safe_env_vars()

        context.update({
            **settings_categories,
            'system_info': system_info,
            'safe_env_vars': safe_env_vars,
            'page_title': 'Django Settings',
        })

        return context

    def _get_safe_env_vars(self):
        """Get non-sensitive environment variables."""
        import os
        safe_env_patterns = [
            'DJANGO_SETTINGS_MODULE', 'PYTHONPATH', 'PATH', 'HOME',
            'USER', 'VIRTUAL_ENV', 'SHELL', 'TERM',
        ]

        safe_env_vars = {}
        for var in safe_env_patterns:
            if var in os.environ:
                value = os.environ[var]
                if len(value) > 200:
                    value = value[:200] + '...'
                safe_env_vars[var] = value

        return safe_env_vars


def settings_api(request):
    """API endpoint that returns settings information as JSON."""
    from django.core.serializers.json import DjangoJSONEncoder

    view = SettingsView()
    view.request = request
    context = view.get_context_data()

    json_data = {
        'core_settings': context['core_settings'],
        'system_info': {
            'python_version': context['system_info']['python_version'],
            'django_version': context['system_info']['django_version'],
            'platform': context['system_info']['platform'],
            'current_time': context['system_info']['current_time'].isoformat(),
        },
        'app_counts': {
            'installed_apps': len(context['app_settings']['INSTALLED_APPS']),
            'middleware': len(context['middleware_settings']['MIDDLEWARE']),
            'template_engines': len(context['template_settings']['TEMPLATES']),
        }
    }

    return JsonResponse(json_data, encoder=DjangoJSONEncoder)


def email_cv_view(request, pk):
    """Handle CV email sending via AJAX."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        cv = get_object_or_404(CV, pk=pk)

        # Parse and validate JSON data
        try:
            data = json.loads(request.body)
            email = data.get('email', '').strip()
            sender_name = data.get('sender_name', '').strip()
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)

        # Validate email
        if not email:
            return JsonResponse({'success': False, 'error': 'Email address is required'}, status=400)

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        if not re.match(email_pattern, email):
            return JsonResponse({'success': False, 'error': 'Please enter a valid email address'}, status=400)

        # Queue email task
        from .tasks import send_cv_pdf_email

        task = send_cv_pdf_email.delay(
            cv_id=cv.pk,
            recipient_email=email,
            sender_name=sender_name or "CV Management System"
        )

        return JsonResponse({
            'success': True,
            'message': f'CV email queued successfully! It will be sent to {email} shortly.',
            'task_id': task.id,
            'cv_name': cv.full_name,
            'recipient': email
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
        }, status=500)


def translate_cv_view(request, pk):
    """Handle CV translation via AJAX."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)

    try:
        cv = get_object_or_404(CV, pk=pk)

        # Parse and validate JSON data
        try:
            data = json.loads(request.body)
            target_language = data.get('target_language', '').strip()
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data'}, status=400)

        # Validate target language
        if not target_language:
            return JsonResponse({'success': False, 'error': 'Target language is required'}, status=400)

        # Define supported languages
        supported_languages = {
            'cornish': 'Cornish',
            'manx': 'Manx',
            'breton': 'Breton',
            'inuktitut': 'Inuktitut',
            'kalaallisut': 'Kalaallisut',
            'romani': 'Romani',
            'occitan': 'Occitan',
            'ladino': 'Ladino',
            'northern_sami': 'Northern Sami',
            'upper_sorbian': 'Upper Sorbian',
            'kashubian': 'Kashubian',
            'zazaki': 'Zazaki',
            'chuvash': 'Chuvash',
            'livonian': 'Livonian',
            'tsakonian': 'Tsakonian',
            'saramaccan': 'Saramaccan',
            'bislama': 'Bislama'
        }

        if target_language not in supported_languages:
            return JsonResponse({
                'success': False,
                'error': f'Unsupported language: {target_language}'
            }, status=400)

        # Check if OpenAI API key is configured
        if not getattr(settings, 'OPENAI_API_KEY', None):
            return JsonResponse({
                'success': False,
                'error': 'Translation service is not configured. Please contact administrator.'
            }, status=503)

        # Queue translation task
        from .tasks import translate_cv_content

        task = translate_cv_content.delay(
            cv_id=cv.pk,
            target_language=supported_languages[target_language]
        )

        return JsonResponse({
            'success': True,
            'message': f'Translation to {supported_languages[target_language]} started...',
            'task_id': task.id,
            'cv_name': cv.full_name,
            'target_language': supported_languages[target_language],
            'target_language_key': target_language
        })

    except CV.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'CV not found'
        }, status=404)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Translation request failed: {str(e)}")

        return JsonResponse({
            'success': False,
            'error': 'Translation service is currently unavailable. Please try again later.'
        }, status=500)


@require_http_methods(["GET"])
def check_email_task_status(request, task_id):
    """Check the status of an email task."""
    try:
        from celery.result import AsyncResult
        from core.celery import app as celery_app

        task_result = AsyncResult(task_id, app=celery_app)

        state_responses = {
            'PENDING': {'state': task_result.state, 'status': 'Task is waiting to be processed...'},
            'PROGRESS': {'state': task_result.state, 'status': 'Task is being processed...'},
            'SUCCESS': {'state': task_result.state, 'status': 'Email sent successfully!', 'result': task_result.result},
        }

        response = state_responses.get(task_result.state, {
            'state': task_result.state,
            'status': 'Task failed',
            'error': str(task_result.info)
        })

        return JsonResponse(response)

    except Exception as e:
        return JsonResponse({
            'state': 'ERROR',
            'status': f'Error checking task status: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def check_translation_task_status(request, task_id):
    """Check the status of a translation task."""
    try:
        from celery.result import AsyncResult
        from core.celery import app as celery_app

        task_result = AsyncResult(task_id, app=celery_app)

        if task_result.state == 'PENDING':
            response = {
                'state': 'PENDING',
                'status': 'Translation is being queued...'
            }
        elif task_result.state == 'PROGRESS':
            response = {
                'state': 'PROGRESS',
                'status': 'Translation in progress...'
            }
        elif task_result.state == 'SUCCESS':
            result = task_result.result
            if result and result.get('success'):
                response = {
                    'state': 'SUCCESS',
                    'status': 'Translation completed successfully!',
                    'translated_data': result.get('translated_data'),
                    'target_language': result.get('target_language'),
                    'cv_name': result.get('cv_name')
                }
            else:
                response = {
                    'state': 'FAILURE',
                    'status': 'Translation failed',
                    'error': result.get('error', 'Unknown error occurred')
                }
        else:
            # FAILURE or other states
            error_msg = str(task_result.info) if task_result.info else 'Translation failed'
            response = {
                'state': task_result.state,
                'status': 'Translation failed',
                'error': error_msg
            }

        return JsonResponse(response)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error checking translation task status: {str(e)}")

        return JsonResponse({
            'state': 'ERROR',
            'status': 'Error checking translation status',
            'error': str(e)
        }, status=500)