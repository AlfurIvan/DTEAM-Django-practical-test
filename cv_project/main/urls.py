"""
URL configuration for main app.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.CVListView.as_view(), name='cv_list'),
    path('cv/<int:pk>/', views.CVDetailView.as_view(), name='cv_detail'),
    path('cv/<int:pk>/pdf/', views.cv_pdf_download, name='cv_pdf_download'),
]