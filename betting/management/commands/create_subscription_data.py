# betting/management/commands/create_subscription_data.py
from django.core.management.base import BaseCommand
from betting.models import GameType

class Command(BaseCommand):
    help = 'Create default game types for subscription system'
    
    def handle(self, *args, **options):
        game_types = [
            {
                'name': 'Monday Special',
                'code': 'POWERBALL',
                'category': 'NLA 5/90',
                'description': 'National Powerball lottery draws',
                'notification_frequency': 'instant'
            },
            {
                'name': 'Lucky Tuesday',
                'code': 'MEGA_MILLIONS',
                'category': 'NLA 5/90',
                'description': 'Mega Millions lottery draws',
                'notification_frequency': 'instant'
            },
            {
                'name': 'Midweek',
                'code': 'SPORTS_BET',
                'category': 'NLA 5/90',
                'description': 'Football, Basketball, and other sports betting',
                'notification_frequency': 'instant'
            },
            {
                'name': 'VAG Monday',
                'code': 'VIRTUAL_GAMES',
                'category': 'VAG Games',
                'description': 'Virtual sports and number games',
                'notification_frequency': 'daily'
            },
            {
                'name': 'Noon Monday',
                'code': 'INSTANT_WIN',
                'category': 'Noon Rush',
                'description': 'Scratch cards and instant win games',
                'notification_frequency': 'weekly'
            }
        ]
        
        for game_data in game_types:
            game_type, created = GameType.objects.get_or_create(
                code=game_data['code'],
                defaults=game_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created {game_type.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'{game_type.name} already exists')
                )