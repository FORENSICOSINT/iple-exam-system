from .models import Result, GradingStructure

def total_score(student, period):
    """
    Returns the total score of a student in a given academic period.
    """
    results = Result.objects.filter(student=student, academic_period=period)
    return sum(r.score for r in results)


def compute_division(student, period):
    """
    Computes the division based on the student's total score and the grading rules.
    """
    total = total_score(student, period)  # get total score first

    # Get grading structures (ordered by highest min_score)
    grading_rules = GradingStructure.objects.all().order_by('-min_score')

    # Determine division
    for rule in grading_rules:
        if total >= rule.min_score:
            return rule.division

    return "Ungraded"
