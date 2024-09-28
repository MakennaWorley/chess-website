import csv
from django.core.management.base import BaseCommand
from chess.models import Player, LessonClass
from django.contrib.auth.models import User
from django.utils import timezone


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
        pass
        self.stdout.write('Starting volunteer import...')
        with open(csv_file_path, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')

            for row in reader:
                beginning_rating = row.get('beginning_rating')
                if beginning_rating in ['', 'NULL', 'None']:
                    beginning_rating = None

                player, created = Player.objects.update_or_create(
                    last_name=row['last_name'].strip(),
                    first_name=row['first_name'].strip(),
                    defaults={
                        'rating': row.get('rating', 100),
                        'beginning_rating': beginning_rating,
                        'active_member': row.get('active_member', 'True').lower() == 'true',
                        'is_volunteer': True,

                        'parent_or_guardian': row.get('parent_or_guardian'),
                        'email': row.get('email'),
                        'phone': row.get('phone'),

                        'modified_by': User.objects.get(username='root'),
                        'is_active': True,
                    }
                )

                if created:
                    player.created_at = timezone.now()
                    player.save()
                    self.stdout.write(f'Created Volunteer: {player}')
                else:
                    self.stdout.write(f'Updated Volunteer: {player}')

        self.stdout.write('Volunteer import completed.')

    def class_import(self, csv_file_path):
        self.stdout.write('Starting class import...')
        with open(csv_file_path, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')

            for row in reader:
                try:
                    teacher_name = row['teacher']
                    co_teacher_name = row.get('co_teacher')

                    teacher = Player.objects.get(first_name__iexact=teacher_name)
                    co_teacher = Player.objects.get(first_name__iexact=co_teacher_name) if co_teacher_name else None

                    if co_teacher:
                        name = str(teacher.first_name + ' & ' + co_teacher.first_name)
                    else:
                        name = teacher.first_name

                    lesson_class, created = LessonClass.objects.get_or_create(
                        name=name,
                        teacher=teacher,
                        co_teacher=co_teacher,
                        defaults={
                            'modified_by': User.objects.get(username='root'),
                            'is_active': True,
                        }
                    )

                    if created:
                        self.stdout.write(f'Created class: {lesson_class.name}')
                        lesson_class.created_at = timezone.now()
                        lesson_class.save()
                    else:
                        self.stdout.write(f'Class already exists: {lesson_class.name}')

                except Player.DoesNotExist:
                    self.stdout.write(f"Teacher or co-teacher not found for class {row.get('name', 'unknown')} (Teacher: {teacher_name}, Co-teacher: {co_teacher_name})")
                except Exception as e:
                    self.stdout.write(f"Error importing class {row.get('name', 'unknown')}: {str(e)}")
        self.stdout.write('Class import completed.')

    def player_import(self, csv_file_path):
        self.stdout.write('Starting player import...')
        with open(csv_file_path, newline='', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')

            for row in reader:
                if row.get('lesson_class'):
                    try:
                        lesson_class = LessonClass.objects.get(teacher__first_name=row['lesson_class'])
                    except LessonClass.DoesNotExist:
                        self.stdout.write(
                            f"LessonClass with identifier {row['lesson_class']} not found, skipping player {row['first_name']} {row['last_name']}.")
                        lesson_class = None

                player, created = Player.objects.update_or_create(
                    last_name=row['last_name'],
                    first_name=row['first_name'],
                    defaults={
                        'rating': row.get('rating', 100),
                        'beginning_rating': row.get('beginning_rating', 100),
                        'grade': row.get('grade'),
                        'lesson_class': lesson_class,
                        'active_member': row.get('active_member', 'True').lower() == 'true',
                        'is_volunteer': row.get('is_volunteer', 'False').lower() == 'true',

                        'parent_or_guardian_name': row.get('parent_or_guardian_name'),
                        'email': row.get('email'),
                        'phone': row.get('phone'),
                        'additional_info': row.get('additional_info'),

                        'modified_by': User.objects.get(username='root'),
                        'is_active': True,
                    }
                )

                if created:
                    player.created_at = timezone.now()
                    player.save()
                    self.stdout.write(f'Created: {player}')
                else:
                    self.stdout.write(f'Updated: {player}')
        self.stdout.write('Player import completed.')
