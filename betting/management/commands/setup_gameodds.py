from django.core.management.base import BaseCommand
from betting.models import GameType, BetType, GameOdds
from decimal import Decimal

class Command(BaseCommand):
    help = 'Setup game odds for all bet types'
    
    def handle(self, *args, **options):
        self.stdout.write('Setting up game odds...')
        
        # Clear existing odds
        GameOdds.objects.all().delete()
        
        # Get all game types and bet types
        game_types = GameType.objects.all()
        bet_types = BetType.objects.all()
        
        # Odds configuration
        odds_config = {
            'direct_one': {
                'numbers_count': 1,
                'numbers_matched': 1,
                'payout_multiplier': Decimal('40.00')  # 40x for Direct One
            },
            'direct_two': {
                'numbers_count': 2,
                'numbers_matched': 2, 
                'payout_multiplier': Decimal('240.00')  # 90x for Direct Two
            },
            'direct_three': {
                'numbers_count': 3,
                'numbers_matched': 3,
                'payout_multiplier': Decimal('2100.00')  # 800x for Direct Three
            },
            'direct_four': {
                'numbers_count': 4, 
                'numbers_matched': 4,
                'payout_multiplier': Decimal('6000.00')  # 7500x for Direct Four
            },
            'direct_five': {
                'numbers_count': 5,
                'numbers_matched': 5, 
                'payout_multiplier': Decimal('44000.00')  # 180,000x for Direct Five
            },
            'perm_two': {
                'numbers_count': 2,
                'numbers_matched': 2,
                'payout_multiplier': Decimal('240.00')  # 45x for Perm Two
            },
            'perm_three': {
                'numbers_count': 3,
                'numbers_matched': 3,
                'payout_multiplier': Decimal('2100.00')  # 130x for Perm Three
            },
            'banker': {
                'numbers_count': 1,
                'numbers_matched': 0,  # For against, we want 0 matches
                'payout_multiplier': Decimal('1.20')  # 1.2x for Against
            }
        }
        
        created_count = 0
        
        for game_type in game_types:
            for bet_type in bet_types:
                if bet_type.name in odds_config:
                    config = odds_config[bet_type.name]
                    
                    # Create GameOdds entry
                    game_odds, created = GameOdds.objects.get_or_create(
                        game_type=game_type,
                        bet_type=bet_type,
                        numbers_count=config['numbers_count'],
                        numbers_matched=config['numbers_matched'],
                        defaults={
                            'payout_multiplier': config['payout_multiplier']
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(
                            f'Created: {game_type.name} - {bet_type.display_name} - '
                            f'{config["numbers_matched"]}/{config["numbers_count"]} - '
                            f'{config["payout_multiplier"]}x'
                        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} game odds entries!')
        )