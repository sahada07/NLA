# betting/management/commands/create_subscription_data.py
from django.core.management.base import BaseCommand
from betting.models import GameType
from datetime import time
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create default game types for subscription system'
    
    def handle(self, *args, **options):
        game_types = [
            {
                'name': 'Monday Special',
                'code': 'MON_SPECIAL',
                'category': 'nla_590',
                'description': 'Weekly Monday lottery draw with big jackpots',
                'min_numbers': 5,
                'max_numbers': 5,
                'number_range_start': 1,
                'number_range_end': 90,
                'min_stake': Decimal('1.00'),
                'max_stake': Decimal('1000.00'),
                'draw_time': time(18, 30, 0),  # 6:30 PM
                'draw_days': 'Monday',
                'notification_frequency': 'instant'
            },
            {
                'name': 'Lucky Tuesday',
                'code': 'LUCKY_TUE',
                'category': 'nla_590',
                'description': 'Tuesday lottery draws',
                'min_numbers': 5,
                'max_numbers': 5,
                'number_range_start': 1,
                'number_range_end': 90,
                'min_stake': Decimal('1.00'),
                'max_stake': Decimal('1000.00'),
                'draw_time': time(18, 30, 0),
                'draw_days': 'Tuesday',
                'notification_frequency': 'instant'
            },
            {
                'name': 'VAG Monday',
                'code': 'VAG_MON',
                'category': 'vag_games',
                'description': 'VAG Monday virtual games',
                'min_numbers': 3,
                'max_numbers': 5,
                'number_range_start': 1,
                'number_range_end': 90,
                'min_stake': Decimal('0.50'),
                'max_stake': Decimal('500.00'),
                'draw_time': time(20, 0, 0),  # 8:00 PM
                'draw_days': 'Monday',
                'notification_frequency': 'daily'
            },
            {
                'name': 'Noon Monday',
                'code': 'NOON_MON',
                'category': 'noon_rush',
                'description': 'Monday noon instant games',
                'min_numbers': 2,
                'max_numbers': 5,
                'number_range_start': 1,
                'number_range_end': 90,
                'min_stake': Decimal('0.50'),
                'max_stake': Decimal('200.00'),
                'draw_time': time(12, 0, 0),  # 12:00 PM
                'draw_days': 'Monday',
                'notification_frequency': 'weekly'
            }
        ]
        
        created_count = 0
        for game_data in game_types:
            game_type, created = GameType.objects.get_or_create(
                code=game_data['code'],
                defaults=game_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Created {game_type.name}')
                )
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️ {game_type.name} already exists')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'🎯 Created {created_count} game types for subscriptions')
        )