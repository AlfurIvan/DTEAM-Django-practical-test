"""
Models for the CV management system.
"""

from django.db import models
from django.urls import reverse


class CV(models.Model):
    """
    CV model representing a person's curriculum vitae.
    """
    firstname = models.CharField(max_length=100, verbose_name="First Name")
    lastname = models.CharField(max_length=100, verbose_name="Last Name")
    email = models.EmailField(verbose_name="Email Address")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Phone Number")
    bio = models.TextField(verbose_name="Biography")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "CV"
        verbose_name_plural = "CVs"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.firstname} {self.lastname}"

    def get_absolute_url(self):
        return reverse('cv_detail', kwargs={'pk': self.pk})

    @property
    def full_name(self):
        return f"{self.firstname} {self.lastname}"


class Skill(models.Model):
    """
    Model representing a skill associated with a CV.
    """
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100, verbose_name="Skill Name")
    proficiency = models.CharField(
        max_length=20,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('expert', 'Expert'),
        ],
        default='intermediate',
        verbose_name="Proficiency Level"
    )

    class Meta:
        verbose_name = "Skill"
        verbose_name_plural = "Skills"
        unique_together = ['cv', 'name']

    def __str__(self):
        return f"{self.name} ({self.proficiency})"


class Project(models.Model):
    """
    Model representing a project associated with a CV.
    """
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200, verbose_name="Project Title")
    description = models.TextField(verbose_name="Project Description")
    technologies = models.CharField(
        max_length=500,
        help_text="Comma-separated list of technologies used",
        verbose_name="Technologies Used"
    )
    url = models.URLField(blank=True, verbose_name="Project URL")
    start_date = models.DateField(verbose_name="Start Date")
    end_date = models.DateField(null=True, blank=True, verbose_name="End Date")

    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ['-start_date']

    def __str__(self):
        return self.title

    @property
    def is_ongoing(self):
        return self.end_date is None

    @property
    def technologies_list(self):
        return [tech.strip() for tech in self.technologies.split(',') if tech.strip()]


class Contact(models.Model):
    """
    Model representing contact information for a CV.
    """
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='contacts')
    contact_type = models.CharField(
        max_length=20,
        choices=[
            ('linkedin', 'LinkedIn'),
            ('github', 'GitHub'),
            ('website', 'Website'),
            ('twitter', 'Twitter'),
            ('other', 'Other'),
        ],
        verbose_name="Contact Type"
    )
    value = models.CharField(max_length=200, verbose_name="Contact Value")
    url = models.URLField(verbose_name="Contact URL")

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        unique_together = ['cv', 'contact_type']

    def __str__(self):
        return f"{self.contact_type}: {self.value}"


class RequestLog(models.Model):
    """
    Model for logging HTTP requests for audit purposes.
    """
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Request Time")
    method = models.CharField(max_length=10, verbose_name="HTTP Method")
    path = models.CharField(max_length=500, verbose_name="Request Path")
    query_string = models.TextField(blank=True, verbose_name="Query String")
    remote_ip = models.GenericIPAddressField(verbose_name="Remote IP Address")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    response_status = models.IntegerField(null=True, blank=True, verbose_name="Response Status Code")
    response_time_ms = models.IntegerField(null=True, blank=True, verbose_name="Response Time (ms)")

    class Meta:
        verbose_name = "Request Log"
        verbose_name_plural = "Request Logs"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['method']),
            models.Index(fields=['path']),
            models.Index(fields=['remote_ip']),
        ]

    def __str__(self):
        return f"{self.method} {self.path} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    @property
    def full_url(self):
        """Reconstruct the full URL from path and query string."""
        if self.query_string:
            return f"{self.path}?{self.query_string}"
        return self.path

    @property
    def response_time_seconds(self):
        """Convert response time from milliseconds to seconds."""
        if self.response_time_ms is not None:
            return self.response_time_ms / 1000.0
        return None

    @classmethod
    def get_recent_logs(cls, limit=10):
        """Get the most recent request logs."""
        return cls.objects.all()[:limit]

    @classmethod
    def get_stats(cls):
        """Get basic statistics about logged requests."""
        from django.db.models import Count, Avg

        total_requests = cls.objects.count()
        if total_requests == 0:
            return {
                'total_requests': 0,
                'methods': {},
                'avg_response_time': None,
                'unique_ips': 0
            }

        methods = dict(cls.objects.values('method').annotate(count=Count('method')).values_list('method', 'count'))
        avg_response_time = cls.objects.filter(response_time_ms__isnull=False).aggregate(
            avg_time=Avg('response_time_ms')
        )['avg_time']
        unique_ips = cls.objects.values('remote_ip').distinct().count()

        return {
            'total_requests': total_requests,
            'methods': methods,
            'avg_response_time': avg_response_time,
            'unique_ips': unique_ips
        }
