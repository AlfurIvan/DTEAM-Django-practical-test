"""
Celery tasks for CV management system.
"""
import logging
import re
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone

from .models import CV, RequestLog

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_cv_pdf_email(self, cv_id, recipient_email, sender_name=None):
    """
    Send CV PDF via email using Celery.

    Args:
        cv_id (int): ID of the CV to send
        recipient_email (str): Email address to send CV to
        sender_name (str, optional): Name of the person sending the email

    Returns:
        dict: Status information about the email sending
    """
    try:
        # Get CV object
        try:
            cv = CV.objects.select_related().prefetch_related(
                'skills', 'projects', 'contacts'
            ).get(pk=cv_id)
        except CV.DoesNotExist:
            logger.error(f"CV with ID {cv_id} does not exist")
            return {
                'success': False,
                'error': f'CV with ID {cv_id} not found'
            }

        # Generate PDF using the helper function from views
        try:
            from .views import generate_cv_pdf_buffer
            pdf_buffer = generate_cv_pdf_buffer(cv)
            pdf_data = pdf_buffer.getvalue()
            pdf_buffer.close()
        except Exception as e:
            logger.error(f"Failed to generate PDF for CV {cv_id}: {str(e)}")
            raise self.retry(exc=e, countdown=60)

        # Prepare email content
        context = {
            'cv': cv,
            'sender_name': sender_name or 'CV Management System',
            'recipient_email': recipient_email,
        }

        # Render email templates
        try:
            html_content = render_to_string('emails/cv_pdf_email.html', context)
            text_content = render_to_string('emails/cv_pdf_email.txt', context)
        except Exception as e:
            logger.error(f"Failed to render email templates: {str(e)}")
            # Fallback to simple text
            html_content = f"""
            <html>
            <body>
                <h2>CV: {cv.full_name}</h2>
                <p>Please find attached the CV for {cv.full_name}.</p>
                <p>Best regards,<br>{sender_name or 'CV Management System'}</p>
            </body>
            </html>
            """
            text_content = f"CV: {cv.full_name}\n\nPlease find attached the CV for {cv.full_name}.\n\nBest regards,\n{sender_name or 'CV Management System'}"

        # Create email
        subject = f"CV: {cv.full_name}"
        from_email = settings.EMAIL_FROM or settings.EMAIL_HOST_USER

        email = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=from_email,
            to=[recipient_email],
        )
        email.content_subtype = 'html'  # Set email as HTML

        # Attach PDF
        filename = f"{cv.full_name.replace(' ', '_')}_CV.pdf"
        email.attach(filename, pdf_data, 'application/pdf')

        # Send email
        try:
            email.send()
            logger.info(f"CV PDF email sent successfully to {recipient_email} for CV {cv_id}")
            return {
                'success': True,
                'message': f'CV sent successfully to {recipient_email}',
                'cv_name': cv.full_name,
                'recipient': recipient_email,
                'filename': filename
            }
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            raise self.retry(exc=e, countdown=60)

    except Exception as e:
        if self.request.retries >= self.max_retries:
            logger.error(f"Failed to send CV PDF email after {self.max_retries} retries: {str(e)}")
            return {
                'success': False,
                'error': f'Failed to send email after {self.max_retries} attempts: {str(e)}'
            }
        else:
            logger.warning(f"Retrying CV PDF email task (attempt {self.request.retries + 1}): {str(e)}")
            raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def translate_cv_content(self, cv_id, target_language):
    """
    Translate CV content using OpenAI gpt-3.5-turbo.

    Args:
        cv_id (int): ID of the CV to translate
        target_language (str): Target language for translation

    Returns:
        dict: Translated content or error information
    """
    try:
        # Get CV object
        try:
            cv = CV.objects.select_related().prefetch_related(
                'skills', 'projects', 'contacts'
            ).get(pk=cv_id)
        except CV.DoesNotExist:
            logger.error(f"CV with ID {cv_id} does not exist")
            return {
                'success': False,
                'error': f'CV with ID {cv_id} not found'
            }

        # Check if OpenAI API key is configured
        openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not openai_api_key:
            logger.error("OpenAI API key not configured")
            return {
                'success': False,
                'error': 'Translation service is not configured'
            }

        # Initialize OpenAI client
        try:
            import openai
            client = openai.OpenAI(api_key=openai_api_key)
        except ImportError:
            logger.error("OpenAI library not installed")
            return {
                'success': False,
                'error': 'Translation service dependencies not available'
            }

        # Define technical terms to avoid translating
        technical_terms = {
            'Python', 'Django', 'JavaScript', 'React', 'Vue', 'Angular', 'Node.js',
            'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Docker', 'Kubernetes',
            'AWS', 'Azure', 'GCP', 'Git', 'GitHub', 'GitLab', 'CI/CD', 'API',
            'REST', 'GraphQL', 'HTML', 'CSS', 'SCSS', 'TypeScript', 'Java',
            'C++', 'C#', 'PHP', 'Ruby', 'Go', 'Rust', 'Swift', 'Kotlin',
            'Flask', 'FastAPI', 'Express', 'Spring', 'Laravel', 'Symfony',
            'TensorFlow', 'PyTorch', 'scikit-learn', 'NumPy', 'Pandas',
            'Jupyter', 'Anaconda', 'Linux', 'Ubuntu', 'CentOS', 'Windows',
            'macOS', 'iOS', 'Android', 'Unity', 'Unreal', 'Blender',
            'Photoshop', 'Illustrator', 'Figma', 'Sketch', 'Adobe',
            'Webpack', 'Babel', 'npm', 'yarn', 'pip', 'composer',
            'Terraform', 'Ansible', 'Jenkins', 'Nginx', 'Apache',
            'Elasticsearch', 'Kafka', 'RabbitMQ', 'Celery', 'Gunicorn'
        }

        def protect_technical_terms(text):
            """Wrap technical terms to prevent translation."""
            if not text:
                return text, {}
            
            protected_text = text
            term_map = {}
            
            # Sort terms by length (longest first) to avoid partial matches
            sorted_terms = sorted(technical_terms, key=len, reverse=True)
            
            for i, term in enumerate(sorted_terms):
                # Case-insensitive search with word boundaries
                pattern = r'\b' + re.escape(term) + r'\b'
                matches = re.finditer(pattern, protected_text, re.IGNORECASE)
                
                for match in matches:
                    original_term = match.group()
                    placeholder = f"TECH_TERM_{i}"
                    term_map[placeholder] = original_term
                    protected_text = protected_text.replace(original_term, placeholder, 1)
            
            return protected_text, term_map

        def restore_technical_terms(text, term_map):
            """Restore technical terms after translation."""
            if not text or not term_map:
                return text
                
            restored_text = text
            for placeholder, original_term in term_map.items():
                restored_text = restored_text.replace(placeholder, original_term)
            
            return restored_text

        # Prepare content for translation
        translation_data = {}

        # 1. Translate biography
        if cv.bio:
            try:
                protected_bio, bio_term_map = protect_technical_terms(cv.bio)
                
                bio_response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": f"You are a professional translator. Translate the following professional biography to {target_language}. Maintain professional tone and keep any placeholders (TECH_TERM_X) unchanged. Preserve paragraph structure."
                        },
                        {
                            "role": "user",
                            "content": protected_bio
                        }
                    ],
                    max_tokens=1000,
                    temperature=0.3
                )
                
                translated_bio = bio_response.choices[0].message.content.strip()
                translation_data['bio'] = restore_technical_terms(translated_bio, bio_term_map)
                
            except Exception as e:
                logger.warning(f"Failed to translate biography: {str(e)}")
                translation_data['bio'] = cv.bio  # Keep original if translation fails
        else:
            # Include empty bio in result
            translation_data['bio'] = cv.bio or ""

        # 2. Translate projects
        translation_data['projects'] = []
        for project in cv.projects.all():
            try:
                project_data = {
                    'id': project.id,
                    'title': project.title,  # Keep title as is (usually technical)
                    'description': project.description,
                    'technologies': project.technologies,
                    'url': project.url,
                    'start_date': project.start_date,
                    'end_date': project.end_date,
                    'is_ongoing': project.is_ongoing
                }

                # Translate description
                if project.description:
                    protected_desc, desc_term_map = protect_technical_terms(project.description)
                    
                    desc_response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {
                                "role": "system",
                                "content": f"You are a professional translator. Translate the following project description to {target_language}. Maintain professional tone and keep any placeholders (TECH_TERM_X) unchanged."
                            },
                            {
                                "role": "user",
                                "content": protected_desc
                            }
                        ],
                        max_tokens=500,
                        temperature=0.3
                    )
                    
                    translated_desc = desc_response.choices[0].message.content.strip()
                    project_data['description'] = restore_technical_terms(translated_desc, desc_term_map)

                translation_data['projects'].append(project_data)

            except Exception as e:
                logger.warning(f"Failed to translate project {project.id}: {str(e)}")
                # Keep original data if translation fails
                translation_data['projects'].append({
                    'id': project.id,
                    'title': project.title,
                    'description': project.description,
                    'technologies': project.technologies,
                    'url': project.url,
                    'start_date': project.start_date,
                    'end_date': project.end_date,
                    'is_ongoing': project.is_ongoing
                })

        # 3. Skills - only translate non-technical skill names
        translation_data['skills'] = []
        for skill in cv.skills.all():
            skill_data = {
                'id': skill.id,
                'name': skill.name,
                'proficiency': skill.proficiency
            }

            # Check if skill name is technical (skip translation)
            if skill.name not in technical_terms:
                try:
                    skill_response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {
                                "role": "system",
                                "content": f"You are a professional translator. Translate this skill name to {target_language}. If it's a technical term or proper noun, return it unchanged. Return only the translated text."
                            },
                            {
                                "role": "user",
                                "content": skill.name
                            }
                        ],
                        max_tokens=50,
                        temperature=0.3
                    )
                    
                    translated_skill = skill_response.choices[0].message.content.strip()
                    # Only use translation if it's different and not just the original
                    if translated_skill.lower() != skill.name.lower():
                        skill_data['name'] = translated_skill

                except Exception as e:
                    logger.warning(f"Failed to translate skill {skill.name}: {str(e)}")
                    # Keep original if translation fails

            translation_data['skills'].append(skill_data)

        logger.info(f"Successfully translated CV {cv_id} to {target_language}")
        
        return {
            'success': True,
            'cv_id': cv_id,
            'target_language': target_language,
            'translated_data': translation_data,
            'cv_name': cv.full_name
        }

    except Exception as e:
        if self.request.retries >= self.max_retries:
            logger.error(f"Failed to translate CV {cv_id} after {self.max_retries} retries: {str(e)}")
            return {
                'success': False,
                'error': f'Translation failed after {self.max_retries} attempts: {str(e)}'
            }
        else:
            logger.warning(f"Retrying CV translation task (attempt {self.request.retries + 1}): {str(e)}")
            # In test mode, don't actually retry to avoid infinite loops
            import sys
            if 'test' in sys.argv or hasattr(self, '_called_from_test'):
                return {
                    'success': False,
                    'error': f'Translation failed after {self.max_retries} attempts: {str(e)}'
                }
            raise self.retry(exc=e, countdown=30)


@shared_task
def cleanup_old_request_logs(days=30):
    """
    Clean up old request logs older than specified days.

    Args:
        days (int): Number of days to keep logs

    Returns:
        dict: Cleanup statistics
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        deleted_count = RequestLog.objects.filter(
            timestamp__lt=cutoff_date
        ).delete()[0]

        logger.info(f"Cleaned up {deleted_count} old request logs older than {days} days")
        return {
            'success': True,
            'deleted_count': deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to cleanup old request logs: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


@shared_task
def test_celery_task():
    """
    Simple test task to verify Celery is working.
    """
    logger.info("Test Celery task executed successfully")
    return {
        'success': True,
        'message': 'Celery is working correctly!',
        'timestamp': timezone.now().isoformat()
    }