from openpyxl import load_workbook
from .models import Player, Game
import os
from django.conf import settings
from datetime import datetime

def write_ratings():
    file_path = os.path.join(settings.BASE_DIR, 'files', 'RatingsTemplate.xlsx')
    workbook = load_workbook(file_path)
    sheet = workbook.active

    students = Player.objects.filter(active_member=True, is_volunteer=False, is_active=True).order_by('-rating', '-grade', 'last_name', 'first_name')

    start_row = 2

    for index, student in enumerate(students, start=start_row):
        sheet[f'A{index}'] = student.name()  # Name
        sheet[f'B{index}'] = student.grade  # Grade
        sheet[f'C{index}'] = student.rating  # Rating
        sheet[f'D{index}'] = student.lesson_class.name if student.lesson_class else ''

    date = datetime.now().strftime('%m-%d-%Y')

    # Save the file in a location accessible for downloads (e.g., media/ratings)
    new_file_path = os.path.join(settings.BASE_DIR, 'files','ratings', f'Ratings_{date}.xlsx')
    os.makedirs(os.path.dirname(new_file_path), exist_ok=True)
    workbook.save(new_file_path)

    return new_file_path
