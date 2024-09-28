import csv
from django.core.management.base import BaseCommand
from chess.models import Player, LessonClass
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Import all data from CSV files: volunteers, classes, and players'

    def add_arguments(self, parser):
        parser.add_argument('volunteers_csv', type=str, help='The path to the volunteers CSV file')
        parser.add_argument('classes_csv', type=str, help='The path to the classes CSV file')
        parser.add_argument('players_csv', type=str, help='The path to the players CSV file')

    def handle(self, *args, **kwargs):
        volunteers_csv = kwargs['volunteers_csv']
        classes_csv = kwargs['classes_csv']
        players_csv = kwargs['players_csv']

        self.volunteer_import(volunteers_csv)
        self.class_import(classes_csv)
        self.player_import(players_csv)

    def volunteer_import(self, csv_file_path):
        self.stdout.write('Starting volunteer import...')
        with open(csv_file_path, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')

            for row in reader:
                beginning_rating = row.get('beginning_rating')
                if beginning_rating in ['', 'NULL', 'None']:
                    beginning_rating = None

                grade = row.get('grade')
                if grade in ['', 'NULL', 'None']:
                    grade = None

                player, created = Player.objects.update_or_create(
                    last_name=row['last_name'].strip(),
                    first_name=row['first_name'].strip(),
                    defaults={
                        'rating': row.get('rating', 100),
                        'beginning_rating': beginning_rating,
                        'grade': grade,
                        'active_member': row.get('active_member', 'True').lower() == 'true',
                        'is_volunteer': True,
                        'parent_or_guardian': row.get('parent_or_guardian'),
                        'email': row.get('email'),
                        'phone': row.get('phone'),
                        'additional_info': row.get('additional_info'),
                        'modified_by': User.objects.get(username='root'),
                        'is_active': row.get('is_active', 'True').lower() == 'true',
                        'end_at': row.get('end_at')
                    }
                )
                if created:
                    self.stdout.write(f'Created Volunteer: {player}')
                else:
                    self.stdout.write(f'Updated Volunteer: {player}')
        self.stdout.write('Volunteer import completed.')

    def class_import(self, csv_file_path):
        self.stdout.write('Starting class import...')
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                try:
                    teacher_name = row['teacher']
                    co_teacher_name = row.get('co_teacher')

                    teacher = Player.objects.get(first_name=teacher_name)
                    co_teacher = Player.objects.get(first_name=co_teacher_name) if co_teacher_name else None

                    lesson_class, created = LessonClass.objects.get_or_create(
                        name=row['name'],
                        defaults={'teacher': teacher, 'co_teacher': co_teacher}
                    )

                    if created:
                        self.stdout.write(f'Created class: {lesson_class.name}')
                    else:
                        self.stdout.write(f'Class already exists: {lesson_class.name}')

                except Player.DoesNotExist:
                    self.stdout.write(f"Teacher or co-teacher not found for class {row['name']}")
                except Exception as e:
                    self.stdout.write(f"Error importing class {row['name']}: {str(e)}")

    def player_import(self, csv_file_path):
        self.stdout.write('Starting player import...')
        with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')
            for row in reader:
                user, _ = User.objects.get_or_create(
                    username=row.get('modified_by', 'import'),  # Default to 'import' if not specified
                    defaults={'password': 'defaultpassword'}  # Set a default password, adjust as needed
                )

                lesson_class = None
                if row.get('lesson_class'):
                    try:
                        lesson_class = LessonClass.objects.get(teacher__first_name=row['lesson_class'])
                    except LessonClass.DoesNotExist:
                        self.stdout.write(
                            f"LessonClass with identifier {row['lesson_class']} not found, skipping player {row['first_name']} {row['last_name']}.")
                        continue  # Skip to the next player if LessonClass is not found

                player, created = Player.objects.update_or_create(
                    last_name=row['last_name'],
                    first_name=row['first_name'],
                    defaults={
                        'rating': row.get('rating', 100),  # Default to 100 if not provided
                        'beginning_rating': row.get('beginning_rating'),
                        'grade': row.get('grade'),
                        'lesson_class': lesson_class,  # Assign the related LessonClass object
                        'active_member': row.get('active_member', 'True').lower() == 'true',
                        'is_volunteer': row.get('is_volunteer', 'False').lower() == 'true',
                        'parent_or_guardian_name': row.get('parent_or_guardian_name'),
                        'email': row.get('email'),
                        'phone': row.get('phone'),
                        'additional_info': row.get('additional_info'),
                        'modified_by': User.objects.get(username='root'),
                        'is_active': row.get('is_active', 'True').lower() == 'true',
                        'end_at': row.get('end_at')
                    }
                )

                if created:
                    self.stdout.write(f'Created: {player}')
                else:
                    self.stdout.write(f'Updated: {player}')
        self.stdout.write('Player import completed.')
