"""
API URL configuration for CV management system.
"""

from django.urls import path
from . import api_views

urlpatterns = [
    # API Overview
    path('', api_views.api_overview, name='api_overview'),

    # CV endpoints
    path('cvs/', api_views.CVListCreateAPIView.as_view(), name='cv_list_create_api'),
    path('cvs/<int:pk>/', api_views.CVRetrieveUpdateDestroyAPIView.as_view(), name='cv_detail_api'),

    # CV nested endpoints
    path('cvs/<int:cv_id>/skills/', api_views.cv_skills, name='cv_skills_api'),
    path('cvs/<int:cv_id>/projects/', api_views.cv_projects, name='cv_projects_api'),
    path('cvs/<int:cv_id>/contacts/', api_views.cv_contacts, name='cv_contacts_api'),

    # CV nested creation endpoints
    path('cvs/<int:cv_id>/skills/add/', api_views.cv_add_skill, name='cv_add_skill_api'),
    path('cvs/<int:cv_id>/projects/add/', api_views.cv_add_project, name='cv_add_project_api'),
    path('cvs/<int:cv_id>/contacts/add/', api_views.cv_add_contact, name='cv_add_contact_api'),

    # Skill endpoints
    path('skills/', api_views.SkillListCreateAPIView.as_view(), name='skill_list_create_api'),
    path('skills/<int:pk>/', api_views.SkillRetrieveUpdateDestroyAPIView.as_view(), name='skill_detail_api'),

    # Project endpoints
    path('projects/', api_views.ProjectListCreateAPIView.as_view(), name='project_list_create_api'),
    path('projects/<int:pk>/', api_views.ProjectRetrieveUpdateDestroyAPIView.as_view(), name='project_detail_api'),

    # Contact endpoints
    path('contacts/', api_views.ContactListCreateAPIView.as_view(), name='contact_list_create_api'),
    path('contacts/<int:pk>/', api_views.ContactRetrieveUpdateDestroyAPIView.as_view(), name='contact_detail_api'),
]