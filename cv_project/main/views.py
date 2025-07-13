"""
Views for the CV management system.
"""

from django.views.generic import ListView, DetailView
from .models import CV


class CVListView(ListView):
    """
    View to display a list of all CVs.
    """
    model = CV
    template_name = 'main/cv_list.html'
    context_object_name = 'cvs'
    paginate_by = 10

    def get_queryset(self):
        """
        Optimize database queries by using select_related and prefetch_related.
        """
        return CV.objects.select_related().prefetch_related(
            'skills', 'projects', 'contacts'
        )


class CVDetailView(DetailView):
    """
    View to display detailed information about a specific CV.
    """
    model = CV
    template_name = 'main/cv_detail.html'
    context_object_name = 'cv'

    def get_queryset(self):
        """
        Optimize database queries by using select_related and prefetch_related.
        """
        return CV.objects.select_related().prefetch_related(
            'skills', 'projects', 'contacts'
        )