# admin.py
from django.contrib import admin
from .models import (
    Student, Result, Subject, AcademicPeriod,
    School, GradingStructure, SchoolAdministrator
)
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML

# -------------------------
# Inline Result for Students
# -------------------------
class ResultInline(admin.TabularInline):
    model = Result
    extra = 0
    readonly_fields = ('subject', 'score', 'get_grade', 'get_remark', 'total_score', 'division')
    fields = ('subject', 'score', 'get_grade', 'get_remark', 'total_score', 'division')
    can_delete = False
    show_change_link = True

    def total_score(self, obj):
        return obj.total_score
    total_score.short_description = "Total Score"

    def division(self, obj):
        return obj.division
    division.short_description = "Division"

    def get_grade(self, obj):
        return obj.get_grade()
    get_grade.short_description = "Grade"

    def get_remark(self, obj):
        return obj.get_remark()
    get_remark.short_description = "Remark"

# -------------------------
# Student Admin
# -------------------------
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("index_number", "full_name", "school", "gender", "year")
    search_fields = ("index_number", "full_name")
    list_filter = ("school", "gender", "year")
    inlines = [ResultInline]
    actions = ['print_pass_slip']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Only students of the school assigned to this user
        return qs.filter(school=request.user.schooladministrator.school)

    # -------------------------
    # Print Pass Slip action
    # -------------------------
    def print_pass_slip(self, request, queryset):
        student = queryset.first()  # handle 1 student at a time
        period = AcademicPeriod.objects.last()  # or select dynamically

        results = student.result_set.filter(academic_period=period)

        html = render_to_string("resultsapp/pass_slip.html", {
            "student": student,
            "results": results,
            "total": sum(r.score for r in results),
            "division": results.first().division if results.exists() else "",
            "period": period
        })

        pdf = HTML(string=html).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'filename="PassSlip_{student.index_number}.pdf"'
        return response

    print_pass_slip.short_description = "Print Pass Slip"

# -------------------------
# School Admin
# -------------------------
@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "district")
    search_fields = ("name", "code")
    list_filter = ("district",)

# -------------------------
# School Administrator
# -------------------------
@admin.register(SchoolAdministrator)
class SchoolAdministratorAdmin(admin.ModelAdmin):
    list_display = ('user', 'school')
    search_fields = ('user__username', 'school__name')

# -------------------------
# Other Admins
# -------------------------
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "name")
    search_fields = ("name", "code")

@admin.register(AcademicPeriod)
class AcademicPeriodAdmin(admin.ModelAdmin):
    list_display = ("year", "date")
    list_filter = ("year",)

@admin.register(GradingStructure)
class GradingStructureAdmin(admin.ModelAdmin):
    list_display = ("subject", "grade", "min_score", "max_score", "remark")
    list_filter = ("subject", "grade")
    ordering = ("subject", "-max_score")

@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ("student", "subject", "score", "academic_period", "computed_grade", "computed_remark")
    list_filter = ("academic_period", "subject")
    search_fields = ("student__full_name", "student__index_number")

    def computed_grade(self, obj):
        return obj.get_grade()

    def computed_remark(self, obj):
        return obj.get_remark()

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        # Only results belonging to this school
        return qs.filter(student__school=request.user.schooladministrator.school)
