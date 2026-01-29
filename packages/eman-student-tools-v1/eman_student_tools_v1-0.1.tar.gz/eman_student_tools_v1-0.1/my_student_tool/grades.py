def calculate_gpa(grade_points):
    if not grade_points:
        return 0.0
    return sum(grade_points) / len(grade_points)

def has_passed(score, passing_mark=50):
    if score >= passing_mark:
        return "Pass"
    else:
        return "Fail"

def attendance_rate(classes_attended, total_classes):
    if total_classes == 0:
        return 0
    return (classes_attended / total_classes) * 100