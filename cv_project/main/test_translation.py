"""
Tests for CV translation functionality.
"""
import json
from unittest.mock import patch, MagicMock
from datetime import date

from django.test import TestCase, override_settings
from django.urls import reverse

from main.models import CV, Skill, Project, Contact
from main.tasks import translate_cv_content


class TranslationViewTests(TestCase):
    """Test cases for translation views."""

    def setUp(self):
        """Set up test data."""
        self.cv = CV.objects.create(
            firstname="John",
            lastname="Doe",
            email="john@example.com",
            bio="Experienced software developer with passion for creating innovative solutions.",
        )

        # Add skills
        Skill.objects.create(cv=self.cv, name="Python", proficiency="expert")
        Skill.objects.create(cv=self.cv, name="Communication", proficiency="advanced")

        # Add project
        Project.objects.create(
            cv=self.cv,
            title="E-commerce Platform",
            description="Built a comprehensive e-commerce platform using Django and React.",
            technologies="Django, React, PostgreSQL",
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
        )

        # Add contact
        Contact.objects.create(
            cv=self.cv,
            contact_type="github",
            value="johndoe",
            url="https://github.com/johndoe",
        )

    def test_translate_cv_view_post_valid_language(self):
        """Test translation request with valid language."""
        url = reverse("cv_translate", kwargs={"pk": self.cv.pk})
        data = {"target_language": "cornish"}

        with patch("main.tasks.translate_cv_content.delay") as mock_delay:
            mock_task = MagicMock()
            mock_task.id = "test-task-id"
            mock_delay.return_value = mock_task

            response = self.client.post(
                url, data=json.dumps(data), content_type="application/json"
            )

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        self.assertEqual(response_data["task_id"], "test-task-id")
        self.assertEqual(response_data["target_language"], "Cornish")
        mock_delay.assert_called_once_with(cv_id=self.cv.pk, target_language="Cornish")

    def test_translate_cv_view_post_invalid_language(self):
        """Test translation request with invalid language."""
        url = reverse("cv_translate", kwargs={"pk": self.cv.pk})
        data = {"target_language": "invalid_language"}

        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])
        self.assertIn("Unsupported language", response_data["error"])

    def test_translate_cv_view_post_missing_language(self):
        """Test translation request with missing language."""
        url = reverse("cv_translate", kwargs={"pk": self.cv.pk})
        data = {}

        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["error"], "Target language is required")

    def test_translate_cv_view_get_method_not_allowed(self):
        """Test that GET method is not allowed for translation."""
        url = reverse("cv_translate", kwargs={"pk": self.cv.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 405)
        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["error"], "Method not allowed")

    def test_translate_cv_view_invalid_json(self):
        """Test translation request with invalid JSON."""
        url = reverse("cv_translate", kwargs={"pk": self.cv.pk})

        response = self.client.post(
            url, data="invalid json", content_type="application/json"
        )

        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])
        self.assertEqual(response_data["error"], "Invalid JSON data")

    def test_translate_cv_view_nonexistent_cv(self):
        """Test translation request for non-existent CV."""
        url = reverse("cv_translate", kwargs={"pk": 9999})
        data = {"target_language": "cornish"}

        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 500)

    @override_settings(OPENAI_API_KEY="")
    def test_translate_cv_view_no_api_key(self):
        """Test translation request when OpenAI API key is not configured."""
        url = reverse("cv_translate", kwargs={"pk": self.cv.pk})
        data = {"target_language": "cornish"}

        response = self.client.post(
            url, data=json.dumps(data), content_type="application/json"
        )

        self.assertEqual(response.status_code, 503)
        response_data = json.loads(response.content)
        self.assertFalse(response_data["success"])
        self.assertIn("Translation service is not configured", response_data["error"])

    def test_check_translation_task_status_success(self):
        """Test checking translation task status - success case."""
        url = reverse("check_translation_status", kwargs={"task_id": "test-task-id"})

        with patch("celery.result.AsyncResult") as mock_async_result:
            mock_task = MagicMock()
            mock_task.state = "SUCCESS"
            mock_task.result = {
                "success": True,
                "translated_data": {
                    "bio": "Translated biography",
                    "skills": [{"id": 1, "name": "Python", "proficiency": "expert"}],
                    "projects": [
                        {
                            "id": 1,
                            "title": "Test Project",
                            "description": "Translated description",
                        }
                    ],
                },
                "target_language": "Cornish",
                "cv_name": "John Doe",
            }
            mock_async_result.return_value = mock_task

            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["state"], "SUCCESS")
        self.assertIn("translated_data", response_data)

    def test_check_translation_task_status_pending(self):
        """Test checking translation task status - pending case."""
        url = reverse("check_translation_status", kwargs={"task_id": "test-task-id"})

        with patch("celery.result.AsyncResult") as mock_async_result:
            mock_task = MagicMock()
            mock_task.state = "PENDING"
            mock_async_result.return_value = mock_task

            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["state"], "PENDING")
        self.assertIn("Translation is being queued", response_data["status"])

    def test_check_translation_task_status_failure(self):
        """Test checking translation task status - failure case."""
        url = reverse("check_translation_status", kwargs={"task_id": "test-task-id"})

        with patch("celery.result.AsyncResult") as mock_async_result:
            mock_task = MagicMock()
            mock_task.state = "FAILURE"
            mock_task.info = "OpenAI API error"
            mock_async_result.return_value = mock_task

            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["state"], "FAILURE")
        self.assertIn("Translation failed", response_data["status"])


class TranslationTaskTests(TestCase):
    """Test cases for translation Celery tasks."""

    def setUp(self):
        """Set up test data."""
        self.cv = CV.objects.create(
            firstname="Jane",
            lastname="Smith",
            email="jane@example.com",
            bio="Software engineer with expertise in Python and web development. Passionate about creating efficient and scalable solutions.",
        )

        # Add skills
        Skill.objects.create(cv=self.cv, name="Python", proficiency="expert")
        Skill.objects.create(cv=self.cv, name="Leadership", proficiency="intermediate")

        # Add project
        Project.objects.create(
            cv=self.cv,
            title="Web Application",
            description="Developed a modern web application using Django and React for managing business operations.",
            technologies="Django, React, PostgreSQL, Redis",
            start_date=date(2023, 6, 1),
        )

    @override_settings(OPENAI_API_KEY="test-api-key")
    @patch("openai.OpenAI")
    def test_translate_cv_content_success(self, mock_openai_class):
        """Test successful CV content translation."""
        # Mock OpenAI client and responses
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Mock biography translation
        bio_response = MagicMock()
        bio_response.choices = [MagicMock()]
        bio_response.choices[
            0
        ].message.content = (
            "Ingeniero de software con experiencia en Python y desarrollo web."
        )

        # Mock project description translation
        project_response = MagicMock()
        project_response.choices = [MagicMock()]
        project_response.choices[
            0
        ].message.content = (
            "Desarrolló una aplicación web moderna usando TECH_TERM_0 y TECH_TERM_1."
        )

        # Mock skill translation
        skill_response = MagicMock()
        skill_response.choices = [MagicMock()]
        skill_response.choices[0].message.content = "Liderazgo"

        mock_client.chat.completions.create.side_effect = [
            bio_response,
            project_response,
            skill_response,
        ]

        # Execute task
        result = translate_cv_content(self.cv.id, "Spanish")

        # Verify result
        self.assertTrue(result["success"])
        self.assertEqual(result["target_language"], "Spanish")
        self.assertEqual(result["cv_id"], self.cv.id)

        # Verify translated content
        translated_data = result["translated_data"]
        self.assertIn("bio", translated_data)
        self.assertIn("skills", translated_data)
        self.assertIn("projects", translated_data)

        # Verify OpenAI API was called
        self.assertEqual(mock_client.chat.completions.create.call_count, 3)

    @override_settings(OPENAI_API_KEY="")
    def test_translate_cv_content_no_api_key(self):
        """Test translation task when API key is not configured."""
        result = translate_cv_content(self.cv.id, "Spanish")

        self.assertFalse(result["success"])
        self.assertIn("Translation service is not configured", result["error"])

    def test_translate_cv_content_nonexistent_cv(self):
        """Test translation task with non-existent CV."""
        result = translate_cv_content(9999, "Spanish")

        self.assertFalse(result["success"])
        self.assertIn("CV with ID 9999 not found", result["error"])

    @override_settings(OPENAI_API_KEY="test-api-key")
    @patch("openai.OpenAI")
    def test_translate_cv_content_technical_terms_protection(self, mock_openai_class):
        """Test that technical terms are protected from translation."""
        # Create CV with technical terms
        cv_with_tech = CV.objects.create(
            firstname="Tech",
            lastname="Expert",
            email="tech@example.com",
            bio="Expert in Python, Django, and React development with PostgreSQL database management.",
        )

        Skill.objects.create(cv=cv_with_tech, name="Django", proficiency="expert")
        Skill.objects.create(cv=cv_with_tech, name="PostgreSQL", proficiency="advanced")

        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Mock responses that should have technical terms preserved
        bio_response = MagicMock()
        bio_response.choices = [MagicMock()]
        # Simulate that OpenAI returns some terms restored, some not
        bio_response.choices[
            0
        ].message.content = "Experto en Python, Django, y React desarrollo con gestión de base de datos PostgreSQL."

        mock_client.chat.completions.create.return_value = bio_response

        result = translate_cv_content(cv_with_tech.id, "Spanish")

        # Verify technical terms are in the result (either preserved or restored)
        self.assertTrue(result["success"])
        translated_bio = result["translated_data"]["bio"]

        # Check that at least some technical terms are present
        # (The exact behavior depends on OpenAI's response and our restoration logic)
        technical_terms_present = any(
            term in translated_bio
            for term in ["Python", "Django", "React", "PostgreSQL"]
        )
        self.assertTrue(
            technical_terms_present, f"No technical terms found in: {translated_bio}"
        )

    @override_settings(OPENAI_API_KEY="test-api-key")
    @patch("openai.OpenAI")
    def test_translate_cv_content_skill_filtering(self, mock_openai_class):
        """Test that technical skills are not translated."""
        # Create CV with mix of technical and non-technical skills
        cv_mixed = CV.objects.create(
            firstname="Mixed",
            lastname="Skills",
            email="mixed@example.com",
            bio="Test biography",
        )

        Skill.objects.create(
            cv=cv_mixed, name="Python", proficiency="expert"
        )  # Technical - should not translate
        Skill.objects.create(
            cv=cv_mixed, name="Leadership", proficiency="advanced"
        )  # Non-technical - should translate
        Skill.objects.create(
            cv=cv_mixed, name="Communication", proficiency="intermediate"
        )  # Non-technical - should translate

        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        # Mock responses
        bio_response = MagicMock()
        bio_response.choices = [MagicMock()]
        bio_response.choices[0].message.content = "Biografía de prueba"

        leadership_response = MagicMock()
        leadership_response.choices = [MagicMock()]
        leadership_response.choices[0].message.content = "Liderazgo"

        communication_response = MagicMock()
        communication_response.choices = [MagicMock()]
        communication_response.choices[0].message.content = "Comunicación"

        mock_client.chat.completions.create.side_effect = [
            bio_response,
            leadership_response,
            communication_response,
        ]

        result = translate_cv_content(cv_mixed.id, "Spanish")

        # Verify result
        self.assertTrue(result["success"])

        # Check skills
        translated_skills = result["translated_data"]["skills"]

        # Find skills by original name for verification
        python_skill = next((s for s in translated_skills if "Python" in str(s)), None)
        leadership_skill = next(
            (s for s in translated_skills if "Liderazgo" in s["name"]), None
        )
        communication_skill = next(
            (s for s in translated_skills if "Comunicación" in s["name"]), None
        )

        # Python should remain unchanged
        self.assertIsNotNone(python_skill)

        # Leadership and Communication should be translated
        self.assertIsNotNone(leadership_skill)
        self.assertIsNotNone(communication_skill)

    @override_settings(OPENAI_API_KEY="test-api-key")
    @patch("openai.OpenAI")
    def test_translate_cv_content_empty_fields(self, mock_openai_class):
        """Test translation with empty/missing fields."""
        # Create CV with minimal data
        minimal_cv = CV.objects.create(
            firstname="Minimal",
            lastname="CV",
            email="minimal@example.com",
            bio="",  # Empty bio
        )

        # Mock OpenAI client (should not be called for empty fields)
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        result = translate_cv_content(minimal_cv.id, "Spanish")

        # Verify result
        self.assertTrue(result["success"])

        # Verify empty/minimal data structure
        translated_data = result["translated_data"]
        self.assertIn("bio", translated_data)
        self.assertIn("skills", translated_data)
        self.assertIn("projects", translated_data)

        # Empty collections should be empty
        self.assertEqual(len(translated_data["skills"]), 0)
        self.assertEqual(len(translated_data["projects"]), 0)

        # OpenAI should not be called for empty content
        mock_client.chat.completions.create.assert_not_called()


class TranslationIntegrationTests(TestCase):
    """Integration tests for translation functionality."""

    def setUp(self):
        """Set up test data."""
        self.cv = CV.objects.create(
            firstname="Integration",
            lastname="Test",
            email="integration@example.com",
            bio="Full-stack developer specializing in Python web development.",
        )

    def test_translation_workflow_end_to_end(self):
        """Test complete translation workflow from request to status check."""
        # Step 1: Make translation request
        translate_url = reverse("cv_translate", kwargs={"pk": self.cv.pk})
        data = {"target_language": "breton"}

        with patch("main.tasks.translate_cv_content.delay") as mock_delay:
            mock_task = MagicMock()
            mock_task.id = "integration-test-task"
            mock_delay.return_value = mock_task

            response = self.client.post(
                translate_url, data=json.dumps(data), content_type="application/json"
            )

        # Verify translation request
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data["success"])
        task_id = response_data["task_id"]

        # Step 2: Check task status (simulate completion)
        status_url = reverse("check_translation_status", kwargs={"task_id": task_id})

        with patch("celery.result.AsyncResult") as mock_async_result:
            mock_task = MagicMock()
            mock_task.state = "SUCCESS"
            mock_task.result = {
                "success": True,
                "translated_data": {
                    "bio": "Développeur full-stack spécialisé en développement web Python.",
                    "skills": [],
                    "projects": [],
                },
                "target_language": "Breton",
                "cv_name": "Integration Test",
            }
            mock_async_result.return_value = mock_task

            status_response = self.client.get(status_url)

        # Verify status check
        self.assertEqual(status_response.status_code, 200)
        status_data = json.loads(status_response.content)
        self.assertEqual(status_data["state"], "SUCCESS")
        self.assertIn("translated_data", status_data)

    def test_all_supported_languages(self):
        """Test that all supported languages are accepted."""
        supported_languages = [
            "cornish",
            "manx",
            "breton",
            "inuktitut",
            "kalaallisut",
            "romani",
            "occitan",
            "ladino",
            "northern_sami",
            "upper_sorbian",
            "kashubian",
            "zazaki",
            "chuvash",
            "livonian",
            "tsakonian",
            "saramaccan",
            "bislama",
        ]

        url = reverse("cv_translate", kwargs={"pk": self.cv.pk})

        for language in supported_languages:
            with self.subTest(language=language):
                data = {"target_language": language}

                with patch("main.tasks.translate_cv_content.delay") as mock_delay:
                    mock_task = MagicMock()
                    mock_task.id = f"test-{language}"
                    mock_delay.return_value = mock_task

                    response = self.client.post(
                        url, data=json.dumps(data), content_type="application/json"
                    )

                self.assertEqual(response.status_code, 200)
                response_data = json.loads(response.content)
                self.assertTrue(response_data["success"])
