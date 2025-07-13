"""
Tests for the CV management system.
"""

from django.test import TestCase, Client
from django.urls import reverse
from datetime import date
from main.models import CV, Skill, Project, Contact


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
        with self.assertNumQueries(4):  # Expecting optimized queries
            response = self.client.get(reverse('cv_detail', kwargs={'pk': self.cv.pk}))
            # Access related objects to trigger queries
            cv = response.context['cv']
            list(cv.skills.all())
            list(cv.projects.all())
            list(cv.contacts.all())