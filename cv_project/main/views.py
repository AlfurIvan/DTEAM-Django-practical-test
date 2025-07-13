"""
Views for the CV management system.
"""

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.views.generic import ListView, DetailView
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from io import BytesIO
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

def cv_pdf_download(request, pk):
    """
    Generate and download CV as PDF using ReportLab.
    """
    cv = get_object_or_404(CV, pk=pk)

    # Create PDF buffer
    buffer = BytesIO()

    # Create PDF document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18
    )

    # Container for the 'Flowable' objects
    elements = []

    # Define styles
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#007bff')
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceAfter=12,
        spaceBefore=20,
        textColor=colors.HexColor('#007bff'),
        borderWidth=1,
        borderColor=colors.HexColor('#007bff'),
        borderPadding=5,
        backColor=colors.HexColor('#f8f9fa')
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=12,
        alignment=TA_JUSTIFY
    )

    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=6,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#666666')
    )

    # Add title
    title = Paragraph(cv.full_name, title_style)
    elements.append(title)

    # Add contact information
    contact_info = f"Email: {cv.email}"
    if cv.phone:
        contact_info += f" | Phone: {cv.phone}"
    contact_para = Paragraph(contact_info, contact_style)
    elements.append(contact_para)
    elements.append(Spacer(1, 20))

    # Add Biography
    bio_heading = Paragraph("Professional Summary", heading_style)
    elements.append(bio_heading)
    bio_content = Paragraph(cv.bio, normal_style)
    elements.append(bio_content)
    elements.append(Spacer(1, 15))

    # Add Skills
    if cv.skills.exists():
        skills_heading = Paragraph("Core Skills", heading_style)
        elements.append(skills_heading)

        # Create skills table - Fix: Remove HTML tags, use plain text
        skills_data = []
        skills_row = []
        for i, skill in enumerate(cv.skills.all()):
            # Create clean skill text without HTML tags
            skill_text = f"{skill.name}\n{skill.get_proficiency_display()}"
            skills_row.append(skill_text)

            # Create new row every 2 skills
            if len(skills_row) == 2:
                skills_data.append(skills_row)
                skills_row = []

        # Add remaining skills if any
        if skills_row:
            while len(skills_row) < 2:
                skills_row.append("")
            skills_data.append(skills_row)

        if skills_data:
            skills_table = Table(skills_data, colWidths=[3*inch, 3*inch])
            skills_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('TOPPADDING', (0, 0), (-1, -1), 12),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e9ecef')),
                # Make skill names bold and proficiency smaller
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ]))
            elements.append(skills_table)
            elements.append(Spacer(1, 15))

    # Add Projects
    if cv.projects.exists():
        projects_heading = Paragraph("Professional Projects", heading_style)
        elements.append(projects_heading)

        for project in cv.projects.all():
            # Project title with dates - Fix: Use proper Paragraph formatting
            project_title_text = f"<b>{project.title}</b>"
            if project.is_ongoing:
                project_title_text += " <font color='#28a745'>(Ongoing)</font>"

            date_range = f"{project.start_date.strftime('%b %Y')}"
            if project.end_date:
                date_range += f" - {project.end_date.strftime('%b %Y')}"
            else:
                date_range += " - Present"

            # Create title paragraph
            project_title_para = Paragraph(project_title_text, normal_style)
            elements.append(project_title_para)

            # Add date range
            date_para = Paragraph(f"<font color='#666666'>{date_range}</font>", normal_style)
            elements.append(date_para)

            # Project description
            project_desc = Paragraph(project.description, normal_style)
            elements.append(project_desc)

            # Technologies
            if project.technologies_list:
                tech_text = "<b>Technologies:</b> " + ", ".join(project.technologies_list)
                tech_para = Paragraph(tech_text, normal_style)
                elements.append(tech_para)

            # URL
            if project.url:
                url_text = f"<b>URL:</b> <font color='#007bff'>{project.url}</font>"
                url_para = Paragraph(url_text, normal_style)
                elements.append(url_para)

            elements.append(Spacer(1, 12))

    # Add Contacts - Fix: Use clean table format
    if cv.contacts.exists():
        contacts_heading = Paragraph("Contact & Social Media", heading_style)
        elements.append(contacts_heading)

        contacts_data = []
        for contact in cv.contacts.all():
            # Clean contact info without HTML tags for table
            contact_info = [
                contact.get_contact_type_display(),
                contact.url
            ]
            contacts_data.append(contact_info)

        if contacts_data:
            contacts_table = Table(contacts_data, colWidths=[2*inch, 4*inch])
            contacts_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8f9fa')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),  # Make contact type bold
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),        # Regular font for URL
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e9ecef')),
                ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#007bff')),  # Blue color for URLs
            ]))
            elements.append(contacts_table)

    # Add footer
    elements.append(Spacer(1, 30))
    footer_text = f"Generated on {cv.updated_at.strftime('%B %d, %Y')} | {cv.full_name} Professional CV"
    footer_para = Paragraph(footer_text, contact_style)
    elements.append(footer_para)

    # Build PDF
    doc.build(elements)

    # Get PDF data
    pdf = buffer.getvalue()
    buffer.close()

    # Create HTTP response
    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"{cv.full_name.replace(' ', '_')}_CV.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response

