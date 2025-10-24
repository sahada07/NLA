# betting/management/commands/create_test_data.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from betting.models import Draw, GameOdds, BetType, GameType
from datetime import datetime, time, timedelta
from decimal import Decimal

class Command(BaseCommand):
    help = 'Create test data for betting system'

    def handle(self, *args, **options):
        self.stdout.write('Creating test data...\n')
        
        # Create Bet Types
        self.stdout.write('Creating bet types...')
        bet_types_data = [
            {
                'name': 'direct',
                'display_name': 'Direct',
                'description': 'All numbers must match in exact order',
                'base_odds': Decimal('180000.00'),
                'min_numbers_required': 5,
                'max_numbers_allowed': 5
            },
            {
                'name': 'perm',
                'display_name': 'Permutation',
                'description': 'Numbers can match in any order',
                'base_odds': Decimal('90000.00'),
                'min_numbers_required': 3,
                'max_numbers_allowed': 5
            },
            {
                'name': 'banker',
                'display_name': 'Banker',
                'description': 'One guaranteed number plus others',
                'base_odds': Decimal('50000.00'),
                'min_numbers_required': 2,
                'max_numbers_allowed': 5
            },
        ]
        
        for data in bet_types_data:
            bet_type, created = BetType.objects.get_or_create(
                name=data['name'],
                defaults=data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Created {bet_type.display_name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️ Already exists: {bet_type.display_name}')
                )
        
        # Create Game Types if they don't exist
        self.stdout.write('\nCreating game types...')
        games_data = [
            {
                'name': 'Monday Special',
                'code': 'MON_SPECIAL',
                'category': 'nla_590',
                'description': 'Weekly Monday lottery draw',
                'min_numbers': 5,
                'max_numbers': 5,
                'number_range_start': 1,
                'number_range_end': 90,
                'min_stake': Decimal('1.00'),
                'max_stake': Decimal('1000.00'),
                'draw_time': time(18, 30, 0),  # FIXED: Use time object
                'draw_days': 'Monday',
                'notification_frequency': 'instant'
            },
            {
                'name': 'VAG Monday',
                'code': 'VAG_MON',
                'category': 'vag_games',
                'description': 'VAG Monday games',
                'min_numbers': 3,
                'max_numbers': 5,
                'number_range_start': 1,
                'number_range_end': 90,
                'min_stake': Decimal('0.50'),
                'max_stake': Decimal('500.00'),
                'draw_time': time(20, 0, 0),  # FIXED: Use time object
                'draw_days': 'Monday',
                'notification_frequency': 'daily'
            },
        ]
        
        for data in games_data:
            game, created = GameType.objects.get_or_create(
                code=data['code'],
                defaults=data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Created {game.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️ Already exists: {game.name}')
                )
        
        # Create Game Odds
        self.stdout.write('\nCreating game odds...')
        try:
            game_monday = GameType.objects.get(code='MON_SPECIAL')
            bet_direct = BetType.objects.get(name='direct')
            
            odds_data = [
                {
                    'game_type': game_monday,
                    'bet_type': bet_direct,
                    'numbers_count': 5,
                    'numbers_matched': 5,
                    'payout_multiplier': Decimal('180000.00')
                },
                {
                    'game_type': game_monday,
                    'bet_type': bet_direct,
                    'numbers_count': 5,
                    'numbers_matched': 4,
                    'payout_multiplier': Decimal('5000.00')
                },
                {
                    'game_type': game_monday,
                    'bet_type': bet_direct,
                    'numbers_count': 5,
                    'numbers_matched': 3,
                    'payout_multiplier': Decimal('500.00')
                },
            ]
            
            for data in odds_data:
                odds, created = GameOdds.objects.get_or_create(
                    game_type=data['game_type'],
                    bet_type=data['bet_type'],
                    numbers_count=data['numbers_count'],
                    numbers_matched=data['numbers_matched'],
                    defaults={'payout_multiplier': data['payout_multiplier']}
                )
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Created odds: {data["numbers_matched"]}/{data["numbers_count"]} = {data["payout_multiplier"]}x'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  ⚠️ Odds already exist: {data["numbers_matched"]}/{data["numbers_count"]}'
                        )
                    )
        except (GameType.DoesNotExist, BetType.DoesNotExist) as e:
            self.stdout.write(
                self.style.ERROR(f'  ❌ Error creating odds: {e}')
            )
        
        # Create upcoming draws
        self.stdout.write('\nCreating draws...')
        try:
            game_monday = GameType.objects.get(code='MON_SPECIAL')
            tomorrow = timezone.now() + timedelta(days=1)
            draw_date = tomorrow.date()

            # Build betting_closes_at as an aware datetime at 18:00 on the draw date
            naive_close_dt = datetime.combine(draw_date, time(hour=18, minute=0))
            betting_closes_at = timezone.make_aware(naive_close_dt, timezone.get_current_timezone())

            draw, created = Draw.objects.get_or_create(
                draw_number=f'MON{draw_date.strftime("%Y%m%d")}',
                defaults={
                    'game_type': game_monday,
                    'draw_date': draw_date,
                    'draw_time': time(18, 30, 0),  # FIXED: Use time object
                    'status': 'open',
                    'betting_opens_at': timezone.now(),
                    'betting_closes_at': betting_closes_at
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Created draw {draw.draw_number}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️ Draw already exists: {draw.draw_number}')
                )
                
        except GameType.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f'  ❌ Error creating draw: {e}')
            )
        
        self.stdout.write(
            self.style.SUCCESS('\n✅ Test data created successfully!')
        )