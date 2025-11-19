from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from weasyprint import HTML
from .models import Student, AcademicPeriod, Result
from .utils import compute_division, total_score

def pass_slip_pdf(request, index_number, year):
    student = get_object_or_404(Student, index_number=index_number)
    period = get_object_or_404(AcademicPeriod, year=year)

    # Get all results for this student and period
    results = Result.objects.filter(student=student, academic_period=period)

    # Compute total score using utils
    total = total_score(student, period)

    # Compute division using utils
    division = compute_division(student, period)

    # Render HTML for PDF
    html = render(request, "pass_slip.html", {
        "student": student,
        "results": results,
        "total": total,
        "division": division,
        "period": period
    })

    # Generate PDF
    pdf = HTML(string=html.content).write_pdf()

    # Return PDF as response
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'filename="PassSlip_{index_number}.pdf"'
    return response
