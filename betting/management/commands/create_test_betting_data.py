from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from datetime import timedelta, datetime, time
from decimal import Decimal

from betting.models import (
    GameType, BetType, GameOdds, Draw, Bet,
    Notification, BetTransaction, generate_bet_number,
    generate_transaction_reference
)
from users.models import User


class Command(BaseCommand):
    help = 'Create small set of test betting data for local testing (idempotent)'

    def handle(self, *args, **options):
        self.stdout.write('Creating test betting data...')

        with transaction.atomic():
            # Ensure test user
            user, created = User.objects.get_or_create(
                username='testuser',
                defaults={
                    'email': 'testuser@example.com',
                    'user_type': 'player'
                }
            )
            if created:
                user.set_password('password')
                user.account_balance = Decimal('100.00')
                user.save()

            # GameType - pick an existing choice name from model choices
            game_type, _ = GameType.objects.get_or_create(
                code='TEST_GAME',
                defaults={
                    'name': 'Quick 5/11',
                    'category': 'other_games',
                    'description': 'Test game type for local testing',
                    'min_numbers': 1,
                    'max_numbers': 5,
                    'number_range_start': 1,
                    'number_range_end': 90,
                    'min_stake': Decimal('1.00'),
                    'max_stake': Decimal('100.00'),
                    'draw_time': time(hour=12, minute=0),
                    'draw_days': 'Monday,Tuesday,Wednesday,Thursday,Friday'
                }
            )

            # BetType - use an allowed choice name (e.g., 'direct')
            bet_type, _ = BetType.objects.get_or_create(
                name='direct',
                defaults={
                    'display_name': 'Direct',
                    'description': 'Direct bet - exact order',
                    'base_odds': Decimal('100.00'),
                    'min_numbers_required': 1,
                    'max_numbers_allowed': 5,
                    'is_active': True,
                }
            )

            # GameOdds
            odds, _ = GameOdds.objects.get_or_create(
                game_type=game_type,
                bet_type=bet_type,
                numbers_count=5,
                numbers_matched=5,
                defaults={
                    'payout_multiplier': Decimal('100.00')
                }
            )

            # Draw - upcoming draw
            draw_date = timezone.localdate()
            draw_time = time(hour=12, minute=0)
            naive_close = datetime.combine(draw_date, time(hour=13, minute=0))
            betting_closes_at = timezone.make_aware(naive_close, timezone.get_current_timezone())
            betting_opens_at = betting_closes_at - timedelta(hours=1)

            draw_number = f"TEST-{timezone.now().strftime('%Y%m%d%H%M%S')}"
            draw, created_draw = Draw.objects.get_or_create(
                draw_number=draw_number,
                defaults={
                    'game_type': game_type,
                    'draw_date': draw_date,
                    'draw_time': draw_time,
                    'status': 'open',
                    'betting_opens_at': betting_opens_at,
                    'betting_closes_at': betting_closes_at,
                }
            )

            # Bet - create a single bet and calculate potential winnings
            bet_number = generate_bet_number()
            selected_numbers = [1, 2, 3, 4, 5][:bet_type.max_numbers_allowed]
            bet, created_bet = Bet.objects.get_or_create(
                bet_number=bet_number,
                defaults={
                    'user': user,
                    'draw': draw,
                    'bet_type': bet_type,
                    'selected_numbers': selected_numbers,
                    'stake_amount': Decimal('1.00'),
                    'status': 'active'
                }
            )
            # Ensure potential winnings are calculated
            bet.calculate_potential_winnings()

            # Notification
            Notification.objects.get_or_create(
                user=user,
                title='Test Notification',
                defaults={
                    'notification_type': 'system',
                    'message': 'This is a test notification created by management command.'
                }
            )

            # Transaction - a sample stake transaction record
            BetTransaction.objects.get_or_create(
                bet=bet,
                user=user,
                reference=generate_transaction_reference(),
                defaults={
                    'transaction_type': 'stake',
                    'amount': bet.stake_amount,
                    'balance_before': user.account_balance - bet.stake_amount,
                    'balance_after': user.account_balance,
                    'description': 'Test stake transaction'
                }
            )

        # Summary output
        self.stdout.write(self.style.SUCCESS('Test data creation complete'))
        counts = {
            'users': User.objects.filter(username='testuser').count(),
            'game_types': GameType.objects.filter(code='TEST_GAME').count(),
            'bet_types': BetType.objects.filter(name='direct').count(),
            'game_odds': GameOdds.objects.filter(game_type=game_type, bet_type=bet_type).count(),
            'draws': Draw.objects.filter(draw_number=draw_number).count(),
            'bets': Bet.objects.filter(bet_number=bet_number).count(),
            'notifications': Notification.objects.filter(title='Test Notification').count(),
        }

        for k, v in counts.items():
            self.stdout.write(f'{k}: {v}')

        self.stdout.write('You can now run `python manage.py create_test_betting_data` to recreate this data (idempotent).')
