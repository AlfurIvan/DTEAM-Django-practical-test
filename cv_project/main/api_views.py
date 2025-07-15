"""
API views for the CV management system.
"""

from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import CV, Skill, Project, Contact
from .serializers import (
    CVSerializer,
    CVCreateUpdateSerializer,
    SkillSerializer,
    SkillCreateUpdateSerializer,
    ProjectSerializer,
    ProjectCreateUpdateSerializer,
    ContactSerializer,
    ContactCreateUpdateSerializer,
)


class CVListCreateAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating CVs.
    GET /api/cvs/ - List all CVs
    POST /api/cvs/ - Create new CV
    """

    queryset = CV.objects.all().prefetch_related("skills", "projects", "contacts")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CVCreateUpdateSerializer
        return CVSerializer

    def get_queryset(self):
        """
        Optionally filter CVs by query parameters.
        """
        queryset = CV.objects.all().prefetch_related("skills", "projects", "contacts")

        # Filter by email
        email = self.request.query_params.get("email", None)
        if email is not None:
            queryset = queryset.filter(email__icontains=email)

        # Filter by name
        name = self.request.query_params.get("name", None)
        if name is not None:
            queryset = queryset.filter(firstname__icontains=name) | queryset.filter(
                lastname__icontains=name
            )

        return queryset.order_by("-created_at")


class CVRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a specific CV.
    GET /api/cvs/{id}/ - Retrieve CV
    PUT /api/cvs/{id}/ - Update CV
    PATCH /api/cvs/{id}/ - Partial update CV
    DELETE /api/cvs/{id}/ - Delete CV
    """

    queryset = CV.objects.all().prefetch_related("skills", "projects", "contacts")

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return CVCreateUpdateSerializer
        return CVSerializer


class SkillListCreateAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating skills.
    GET /api/skills/ - List all skills
    POST /api/skills/ - Create new skill
    """

    serializer_class = SkillCreateUpdateSerializer

    def get_queryset(self):
        """
        Optionally filter skills by CV.
        """
        queryset = Skill.objects.select_related("cv")
        cv_id = self.request.query_params.get("cv", None)
        if cv_id is not None:
            queryset = queryset.filter(cv_id=cv_id)
        return queryset.order_by("name")


class SkillRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a specific skill.
    """

    queryset = Skill.objects.select_related("cv")
    serializer_class = SkillCreateUpdateSerializer


class ProjectListCreateAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating projects.
    GET /api/projects/ - List all projects
    POST /api/projects/ - Create new project
    """

    serializer_class = ProjectCreateUpdateSerializer

    def get_queryset(self):
        """
        Optionally filter projects by CV.
        """
        queryset = Project.objects.select_related("cv")
        cv_id = self.request.query_params.get("cv", None)
        if cv_id is not None:
            queryset = queryset.filter(cv_id=cv_id)
        return queryset.order_by("-start_date")


class ProjectRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a specific project.
    """

    queryset = Project.objects.select_related("cv")
    serializer_class = ProjectCreateUpdateSerializer


class ContactListCreateAPIView(generics.ListCreateAPIView):
    """
    API view for listing and creating contacts.
    GET /api/contacts/ - List all contacts
    POST /api/contacts/ - Create new contact
    """

    serializer_class = ContactCreateUpdateSerializer

    def get_queryset(self):
        """
        Optionally filter contacts by CV.
        """
        queryset = Contact.objects.select_related("cv")
        cv_id = self.request.query_params.get("cv", None)
        if cv_id is not None:
            queryset = queryset.filter(cv_id=cv_id)
        return queryset.order_by("contact_type")


class ContactRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API view for retrieving, updating, and deleting a specific contact.
    """

    queryset = Contact.objects.select_related("cv")
    serializer_class = ContactCreateUpdateSerializer


@api_view(["GET"])
def cv_skills(request, cv_id):
    """
    Get all skills for a specific CV.
    GET /api/cvs/{cv_id}/skills/
    """
    cv = get_object_or_404(CV, pk=cv_id)
    skills = cv.skills.all()
    serializer = SkillSerializer(skills, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def cv_projects(request, cv_id):
    """
    Get all projects for a specific CV.
    GET /api/cvs/{cv_id}/projects/
    """
    cv = get_object_or_404(CV, pk=cv_id)
    projects = cv.projects.all().order_by("-start_date")
    serializer = ProjectSerializer(projects, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def cv_contacts(request, cv_id):
    """
    Get all contacts for a specific CV.
    GET /api/cvs/{cv_id}/contacts/
    """
    cv = get_object_or_404(CV, pk=cv_id)
    contacts = cv.contacts.all()
    serializer = ContactSerializer(contacts, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def cv_add_skill(request, cv_id):
    """
    Add a skill to a specific CV.
    POST /api/cvs/{cv_id}/skills/
    """
    cv = get_object_or_404(CV, pk=cv_id)

    data = request.data.copy()
    data["cv"] = cv.id

    serializer = SkillCreateUpdateSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def cv_add_project(request, cv_id):
    """
    Add a project to a specific CV.
    POST /api/cvs/{cv_id}/projects/
    """
    cv = get_object_or_404(CV, pk=cv_id)

    data = request.data.copy()
    data["cv"] = cv.id

    serializer = ProjectCreateUpdateSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def cv_add_contact(request, cv_id):
    """
    Add a contact to a specific CV.
    POST /api/cvs/{cv_id}/contacts/
    """
    cv = get_object_or_404(CV, pk=cv_id)

    data = request.data.copy()
    data["cv"] = cv.id

    serializer = ContactCreateUpdateSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def api_overview(request):
    """
    API overview with available endpoints.
    GET /api/
    """
    api_urls = {
        "overview": "/api/",
        "cvs": {
            "list_create": "/api/cvs/",
            "retrieve_update_delete": "/api/cvs/{id}/",
            "skills": "/api/cvs/{id}/skills/",
            "projects": "/api/cvs/{id}/projects/",
            "contacts": "/api/cvs/{id}/contacts/",
            "add_skill": "POST /api/cvs/{id}/skills/",
            "add_project": "POST /api/cvs/{id}/projects/",
            "add_contact": "POST /api/cvs/{id}/contacts/",
        },
        "skills": {
            "list_create": "/api/skills/",
            "retrieve_update_delete": "/api/skills/{id}/",
        },
        "projects": {
            "list_create": "/api/projects/",
            "retrieve_update_delete": "/api/projects/{id}/",
        },
        "contacts": {
            "list_create": "/api/contacts/",
            "retrieve_update_delete": "/api/contacts/{id}/",
        },
    }
    return Response(api_urls)
