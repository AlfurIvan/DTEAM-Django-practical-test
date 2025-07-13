"""
Admin configuration for CV models.
"""

from django.contrib import admin
from .models import CV, Skill, Project, Contact


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 1


class ProjectInline(admin.TabularInline):
    model = Project
    extra = 1


class ContactInline(admin.TabularInline):
    model = Contact
    extra = 1


@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'created_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('firstname', 'lastname', 'email')
    readonly_fields = ('created_at', 'updated_at')

    inlines = [SkillInline, ProjectInline, ContactInline]

    fieldsets = (
        ('Personal Information', {
            'fields': ('firstname', 'lastname', 'email', 'phone')
        }),
        ('Biography', {
            'fields': ('bio',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'cv', 'proficiency')
    list_filter = ('proficiency',)
    search_fields = ('name', 'cv__firstname', 'cv__lastname')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'cv', 'start_date', 'is_ongoing')
    list_filter = ('start_date', 'end_date')
    search_fields = ('title', 'cv__firstname', 'cv__lastname')


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('contact_type', 'value', 'cv')
    list_filter = ('contact_type',)
    search_fields = ('value', 'cv__firstname', 'cv__lastname')