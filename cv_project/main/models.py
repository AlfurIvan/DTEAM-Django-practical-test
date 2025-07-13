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