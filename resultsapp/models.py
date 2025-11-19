from django.db import models
from django.contrib.auth.models import User

# -------------------------
#  SCHOOLS
# -------------------------
class School(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, unique=True)
    district = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.code} - {self.name}"


class SchoolAdministrator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.user.username} - {self.school.name}"



# -------------------------
#  ACADEMIC PERIOD / EXAM SESSION
# -------------------------
class AcademicPeriod(models.Model):
    year = models.IntegerField(unique=True)
    date = models.DateField()

    def __str__(self):
        return str(self.year)


# -------------------------
#  SUBJECTS
# -------------------------
class Subject(models.Model):
    name = models.CharField(max_length=50)
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


# -------------------------
#  STUDENTS
# -------------------------
class Student(models.Model):
    GENDER = (
        ("M", "Male"),
        ("F", "Female"),
    )
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    index_number = models.CharField(max_length=30, unique=True)
    gender = models.CharField(max_length=1, choices=GENDER)
    year = models.IntegerField()

    def __str__(self):
        return f"{self.index_number} - {self.full_name}"
    



# -------------------------
#  GRADING STRUCTURE
# -------------------------
class GradingStructure(models.Model):
    """
    Defines grade boundaries for each subject or globally.
    """
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, null=True, blank=True, help_text="Leave blank for global grading.")
    min_score = models.IntegerField()
    max_score = models.IntegerField()
    grade = models.CharField(max_length=10)
    remark = models.CharField(max_length=100, blank=True)

    class Meta:
        unique_together = ("subject", "min_score", "max_score")
        ordering = ["-max_score"]

    def __str__(self):
        if self.subject:
            return f"{self.subject.name}: {self.grade} ({self.min_score}-{self.max_score})"
        return f"Global: {self.grade} ({self.min_score}-{self.max_score})"


# -------------------------
#  RESULTS
# -------------------------

class Result(models.Model):
    student = models.ForeignKey("Student", on_delete=models.CASCADE)
    subject = models.ForeignKey("Subject", on_delete=models.CASCADE)
    academic_period = models.ForeignKey("AcademicPeriod", on_delete=models.CASCADE)
    score = models.IntegerField()

    class Meta:
        unique_together = ("student", "subject", "academic_period")

    def __str__(self):
        return f"{self.student.index_number} - {self.subject.code} - {self.score}"

    # -------------------------
    # Compute grade
    # -------------------------
    def get_grade(self):
        # Subject-specific grading
        grading = GradingStructure.objects.filter(
            subject=self.subject,
            min_score__lte=self.score,
            max_score__gte=self.score
        ).first()

        # Global grading
        if not grading:
            grading = GradingStructure.objects.filter(
                subject__isnull=True,
                min_score__lte=self.score,
                max_score__gte=self.score
            ).first()

        return grading.grade if grading else "N/A"

    # -------------------------
    # Compute remark
    # -------------------------
    def get_remark(self):
        # Subject-specific grading
        grading = GradingStructure.objects.filter(
            subject=self.subject,
            min_score__lte=self.score,
            max_score__gte=self.score
        ).first()

        # Global grading
        if not grading:
            grading = GradingStructure.objects.filter(
                subject__isnull=True,
                min_score__lte=self.score,
                max_score__gte=self.score
            ).first()

        return grading.remark if grading else ""

    # -------------------------
    # Compute total score for the student in this period
    # -------------------------
    @property
    def total_score(self):
        results = Result.objects.filter(
            student=self.student,
            academic_period=self.academic_period
        )
        return sum(r.score for r in results)

    # -------------------------
    # Compute division dynamically based on total_score
    # -------------------------
    @property
    def division(self):
        total = self.total_score
        grading_rules = GradingStructure.objects.all().order_by('-min_score')
        for rule in grading_rules:
            if total >= rule.min_score:
                return rule.grade 
        return "Ungraded"


