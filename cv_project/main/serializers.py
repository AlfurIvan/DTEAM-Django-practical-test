"""
Serializers for the CV management system API.
"""

from rest_framework import serializers
from .models import CV, Skill, Project, Contact


class SkillSerializer(serializers.ModelSerializer):
    """
    Serializer for Skill model.
    """

    class Meta:
        model = Skill
        fields = ['id', 'name', 'proficiency']

    def validate_name(self, value):
        """
        Validate that skill name is not empty.
        """
        if not value.strip():
            raise serializers.ValidationError("Skill name cannot be empty.")
        return value.strip()


class ContactSerializer(serializers.ModelSerializer):
    """
    Serializer for Contact model.
    """

    class Meta:
        model = Contact
        fields = ['id', 'contact_type', 'value', 'url']

    def validate_url(self, value):
        """
        Validate URL format.
        """
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for Project model.
    """
    is_ongoing = serializers.ReadOnlyField()
    technologies_list = serializers.ReadOnlyField()

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'technologies', 'technologies_list',
            'url', 'start_date', 'end_date', 'is_ongoing'
        ]

    def validate(self, data):
        """
        Validate that end_date is after start_date if provided.
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                "End date must be after start date."
            )
        return data


class CVSerializer(serializers.ModelSerializer):
    """
    Serializer for CV model with nested relationships.
    """
    skills = SkillSerializer(many=True, read_only=True)
    projects = ProjectSerializer(many=True, read_only=True)
    contacts = ContactSerializer(many=True, read_only=True)
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = CV
        fields = [
            'id', 'firstname', 'lastname', 'full_name', 'email', 'phone',
            'bio', 'created_at', 'updated_at', 'skills', 'projects', 'contacts'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_email(self, value):
        """
        Validate email format and uniqueness.
        """
        if CV.objects.filter(email=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("A CV with this email already exists.")
        return value


class CVCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating/updating CVs without nested objects.
    """

    class Meta:
        model = CV
        fields = [
            'id', 'firstname', 'lastname', 'email', 'phone', 'bio'
        ]
        read_only_fields = ['id']

    def validate_email(self, value):
        """
        Validate email format and uniqueness.
        """
        if CV.objects.filter(email=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("A CV with this email already exists.")
        return value


class SkillCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating skills.
    """

    class Meta:
        model = Skill
        fields = ['id', 'cv', 'name', 'proficiency']

    def validate(self, data):
        """
        Validate that CV and skill name combination is unique.
        """
        cv = data.get('cv')
        name = data.get('name')

        if cv and name:
            existing_skill = Skill.objects.filter(cv=cv, name=name)
            if self.instance:
                existing_skill = existing_skill.exclude(pk=self.instance.pk)

            if existing_skill.exists():
                raise serializers.ValidationError(
                    "A skill with this name already exists for this CV."
                )
        return data


class ProjectCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating projects.
    """

    class Meta:
        model = Project
        fields = [
            'id', 'cv', 'title', 'description', 'technologies',
            'url', 'start_date', 'end_date'
        ]

    def validate(self, data):
        """
        Validate project data.
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                "End date must be after start date."
            )
        return data


class ContactCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating contacts.
    """

    class Meta:
        model = Contact
        fields = ['id', 'cv', 'contact_type', 'value', 'url']

    def validate(self, data):
        """
        Validate that CV and contact_type combination is unique.
        """
        cv = data.get('cv')
        contact_type = data.get('contact_type')

        if cv and contact_type:
            existing_contact = Contact.objects.filter(cv=cv, contact_type=contact_type)
            if self.instance:
                existing_contact = existing_contact.exclude(pk=self.instance.pk)

            if existing_contact.exists():
                raise serializers.ValidationError(
                    "A contact with this type already exists for this CV."
                )
        return data

    def validate_url(self, value):
        """
        Validate URL format.
        """
        if not value.startswith(('http://', 'https://')):
            raise serializers.ValidationError("URL must start with http:// or https://")
        return value