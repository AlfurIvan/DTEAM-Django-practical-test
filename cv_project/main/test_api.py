"""
API tests for the CV management system.
"""

from datetime import date, timedelta
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from main.models import CV, Skill, Project, Contact


class SkillAPITestCase(APITestCase):
    """Test cases for Skill API endpoints."""

    def setUp(self):
        """Set up clean test data."""
        self.client = APIClient()
        # Clear all existing data to avoid fixture interference
        CV.objects.all().delete()
        Skill.objects.all().delete()
        Project.objects.all().delete()
        Contact.objects.all().delete()

        self.cv = CV.objects.create(
            firstname='SkillTest',
            lastname='User',
            email='skill.test@example.com',
            bio='Skill test biography'
        )
        self.skill = Skill.objects.create(
            cv=self.cv,
            name='TestSkill',
            proficiency='expert'
        )

    def test_skill_list_api(self):
        """Test skill list API endpoint."""
        url = reverse('skill_list_create_api')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if response is paginated or direct list
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
            self.assertEqual(response.data['results'][0]['name'], 'TestSkill')
        else:
            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]['name'], 'TestSkill')

    def test_skill_create_api(self):
        """Test skill creation via API."""
        url = reverse('skill_list_create_api')
        skill_data = {
            'cv': self.cv.id,
            'name': 'NewSkill',
            'proficiency': 'advanced'
        }
        response = self.client.post(url, skill_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Skill.objects.count(), 2)
        self.assertEqual(response.data['name'], 'NewSkill')

    def test_skill_retrieve_api(self):
        """Test skill retrieval via API."""
        url = reverse('skill_detail_api', kwargs={'pk': self.skill.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'TestSkill')

    def test_skill_delete_api(self):
        """Test skill deletion via API."""
        url = reverse('skill_detail_api', kwargs={'pk': self.skill.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Skill.objects.count(), 0)

    def test_skill_filter_by_cv(self):
        """Test skill filtering by CV."""
        # Create another CV and skill
        cv2 = CV.objects.create(
            firstname='Another',
            lastname='User',
            email='another.user@example.com',
            bio='Another user bio'
        )
        Skill.objects.create(cv=cv2, name='AnotherSkill', proficiency='intermediate')

        url = reverse('skill_list_create_api')
        response = self.client.get(url, {'cv': self.cv.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if response is paginated or direct list
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
            self.assertEqual(response.data['results'][0]['name'], 'TestSkill')
        else:
            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]['name'], 'TestSkill')


class ProjectAPITestCase(APITestCase):
    """Test cases for Project API endpoints."""

    def setUp(self):
        """Set up clean test data."""
        self.client = APIClient()
        # Clear all existing data to avoid fixture interference
        CV.objects.all().delete()
        Project.objects.all().delete()
        Skill.objects.all().delete()
        Contact.objects.all().delete()

        self.cv = CV.objects.create(
            firstname='ProjectTest',
            lastname='User',
            email='project.test@example.com',
            bio='Project test biography'
        )
        self.project = Project.objects.create(
            cv=self.cv,
            title='Test API Project',
            description='Test project for API',
            technologies='Python, Django, DRF',
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )

    def test_project_list_api(self):
        """Test project list API endpoint."""
        url = reverse('project_list_create_api')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if response is paginated or direct list
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
            self.assertEqual(response.data['results'][0]['title'], 'Test API Project')
        else:
            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]['title'], 'Test API Project')

    def test_project_create_api(self):
        """Test project creation via API."""
        url = reverse('project_list_create_api')
        project_data = {
            'cv': self.cv.id,
            'title': 'New API Project',
            'description': 'New project via API',
            'technologies': 'React, Node.js',
            'start_date': '2024-01-01'
        }
        response = self.client.post(url, project_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 2)
        self.assertEqual(response.data['title'], 'New API Project')

    def test_project_retrieve_api(self):
        """Test project retrieval via API."""
        url = reverse('project_detail_api', kwargs={'pk': self.project.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test API Project')

    def test_project_delete_api(self):
        """Test project deletion via API."""
        url = reverse('project_detail_api', kwargs={'pk': self.project.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Project.objects.count(), 0)


class ContactAPITestCase(APITestCase):
    """Test cases for Contact API endpoints."""

    def setUp(self):
        """Set up clean test data."""
        self.client = APIClient()
        # Clear all existing data to avoid fixture interference
        CV.objects.all().delete()
        Contact.objects.all().delete()
        Skill.objects.all().delete()
        Project.objects.all().delete()

        self.cv = CV.objects.create(
            firstname='ContactTest',
            lastname='User',
            email='contact.test@example.com',
            bio='Contact test biography'
        )
        self.contact = Contact.objects.create(
            cv=self.cv,
            contact_type='github',
            value='testuser',
            url='https://github.com/testuser'
        )

    def test_contact_list_api(self):
        """Test contact list API endpoint."""
        url = reverse('contact_list_create_api')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if response is paginated or direct list
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
            self.assertEqual(response.data['results'][0]['contact_type'], 'github')
        else:
            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]['contact_type'], 'github')

    def test_contact_create_api(self):
        """Test contact creation via API."""
        url = reverse('contact_list_create_api')
        contact_data = {
            'cv': self.cv.id,
            'contact_type': 'linkedin',
            'value': 'test-user',
            'url': 'https://linkedin.com/in/test-user'
        }
        response = self.client.post(url, contact_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Contact.objects.count(), 2)
        self.assertEqual(response.data['contact_type'], 'linkedin')

    def test_contact_retrieve_api(self):
        """Test contact retrieval via API."""
        url = reverse('contact_detail_api', kwargs={'pk': self.contact.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['contact_type'], 'github')

    def test_contact_delete_api(self):
        """Test contact deletion via API."""
        url = reverse('contact_detail_api', kwargs={'pk': self.contact.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Contact.objects.count(), 0)

    def test_contact_invalid_url(self):
        """Test contact creation with invalid URL."""
        url = reverse('contact_list_create_api')
        contact_data = {
            'cv': self.cv.id,
            'contact_type': 'website',
            'value': 'testsite.com',
            'url': 'testsite.com'  # Invalid URL without protocol
        }
        response = self.client.post(url, contact_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProjectAPIAdvancedTestCase(APITestCase):
    """Advanced test cases for Project API endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        # Clear all existing data to avoid fixture interference
        CV.objects.all().delete()
        Project.objects.all().delete()
        Skill.objects.all().delete()
        Contact.objects.all().delete()

        self.cv = CV.objects.create(
            firstname='Project',
            lastname='Tester',
            email='project@example.com',
            bio='Project tester'
        )

    def test_project_ongoing_validation(self):
        """Test project creation without end date (ongoing)."""
        url = reverse('project_list_create_api')
        project_data = {
            'cv': self.cv.id,
            'title': 'Ongoing Project',
            'description': 'This project is ongoing',
            'technologies': 'Python, Django',
            'start_date': '2024-01-01'
            # No end_date = ongoing project
        }
        response = self.client.post(url, project_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        project = Project.objects.get(title='Ongoing Project')
        self.assertIsNone(project.end_date)
        self.assertTrue(project.is_ongoing)

    def test_project_future_start_date(self):
        """Test project with future start date."""
        url = reverse('project_list_create_api')
        future_date = (date.today() + timedelta(days=30)).strftime('%Y-%m-%d')
        project_data = {
            'cv': self.cv.id,
            'title': 'Future Project',
            'description': 'Project starting in the future',
            'technologies': 'React, Node.js',
            'start_date': future_date
        }
        response = self.client.post(url, project_data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_project_technologies_list_property(self):
        """Test project technologies property through API."""
        project = Project.objects.create(
            cv=self.cv,
            title='Tech Test Project',
            description='Testing technologies',
            technologies='Python, Django, React, PostgreSQL',
            start_date=date(2023, 1, 1)
        )

        url = reverse('project_detail_api', kwargs={'pk': project.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check that technologies field exists (technologies_list is read-only in serializer)
        self.assertIn('technologies', response.data)
        self.assertEqual(response.data['technologies'], 'Python, Django, React, PostgreSQL')

    def test_project_ordering(self):
        """Test project ordering by start_date (descending)."""
        # Create projects with different start dates
        Project.objects.create(
            cv=self.cv, title='Old Project',
            description='Older project', technologies='Python',
            start_date=date(2022, 1, 1)
        )
        Project.objects.create(
            cv=self.cv, title='New Project',
            description='Newer project', technologies='Django',
            start_date=date(2024, 1, 1)
        )

        url = reverse('project_list_create_api')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if response is paginated or direct list
        if isinstance(response.data, dict) and 'results' in response.data:
            # First project should be the newer one (ordered by -start_date)
            self.assertEqual(response.data['results'][0]['title'], 'New Project')
        else:
            # Direct list response
            self.assertEqual(response.data[0]['title'], 'New Project')


class APIPerformanceTestCase(APITestCase):
    """Test cases for API performance and optimization."""

    def setUp(self):
        """Set up test data with relationships."""
        self.client = APIClient()
        # Clear all existing data to avoid fixture interference
        CV.objects.all().delete()
        Skill.objects.all().delete()
        Project.objects.all().delete()
        Contact.objects.all().delete()

        self.cv = CV.objects.create(
            firstname='Performance',
            lastname='Test',
            email='performance@example.com',
            bio='Performance test CV'
        )

        # Create related objects
        for i in range(5):
            Skill.objects.create(
                cv=self.cv,
                name=f'Skill{i}',
                proficiency='expert'
            )
            Project.objects.create(
                cv=self.cv,
                title=f'Project{i}',
                description=f'Description for project {i}',
                technologies='Python, Django',
                start_date=date(2023, 1, 1)
            )
            Contact.objects.create(
                cv=self.cv,
                contact_type=['linkedin', 'github', 'website', 'twitter', 'other'][i],
                value=f'user{i}',
                url=f'https://example{i}.com'
            )

    def test_cv_detail_query_optimization(self):
        """Test that CV detail endpoint uses optimized queries."""
        url = reverse('cv_detail_api', kwargs={'pk': self.cv.pk})

        # Should use select_related/prefetch_related to minimize queries
        with self.assertNumQueries(4):  # Adjust expected number based on actual optimization
            response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify all related data is included
        self.assertEqual(len(response.data['skills']), 5)
        self.assertEqual(len(response.data['projects']), 5)
        self.assertEqual(len(response.data['contacts']), 5)

    def test_cv_list_query_optimization(self):
        """Test that CV list endpoint uses optimized queries."""
        url = reverse('cv_list_create_api')

        # Based on the actual query output, expect 5 queries:
        # 1. COUNT for pagination
        # 2. CV objects
        # 3. Skills prefetch
        # 4. Projects prefetch
        # 5. Contacts prefetch
        with self.assertNumQueries(5):  # Updated to match actual query count
            response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verify related data is accessible
        cv_data = response.data['results'][0]
        self.assertIn('skills', cv_data)
        self.assertIn('projects', cv_data)
        self.assertIn('contacts', cv_data)
        # Verify the prefetch worked - should have 5 of each
        self.assertEqual(len(cv_data['skills']), 5)
        self.assertEqual(len(cv_data['projects']), 5)
        self.assertEqual(len(cv_data['contacts']), 5)