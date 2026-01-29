def format_student_name(first, last):
    return f"{first.capitalize()} {last.capitalize()}"

def generate_student_email(student_id):
    return f"{student_id}@student.uni.edu"

def count_words(text):
    return len(text.split())