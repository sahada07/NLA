# betting/management/commands/test_betting_system.py
# Create this file: betting/management/commands/test_betting_system.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from betting.models import GameType, BetType, Draw, Bet, GameOdds
from users.models import User
import json


class Command(BaseCommand):
    help = 'Comprehensive test of betting system'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-data',
            action='store_true',
            help='Create test data first',
        )
        parser.add_argument(
            '--username',
            type=str,
            default='testuser',
            help='Username to test with',
        )
    
    def handle(self, *args, **options):
        username = options['username']
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("🧪 COMPREHENSIVE BETTING SYSTEM TEST"))
        self.stdout.write("="*70 + "\n")
        
        # Step 1: Check if we need to create data
        if options['create_data']:
            self.create_test_data()
        
        # Step 2: Verify all components exist
        self.stdout.write("\n📋 Step 1: Verifying System Components...")
        if not self.verify_components():
            self.stdout.write(self.style.ERROR("\n❌ System components missing!"))
            self.stdout.write(self.style.WARNING("Run with --create-data flag\n"))
            return
        
        # Step 3: Check user
        self.stdout.write("\n👤 Step 2: Checking User...")
        user = self.check_user(username)
        if not user:
            self.stdout.write(self.style.ERROR("\n❌ User check failed!"))
            self.stdout.write(self.style.WARNING("Run with --create-data flag\n"))
            return
        
        # Step 4: Check draws
        self.stdout.write("\n🎰 Step 3: Checking Draws...")
        draw = self.check_draws()
        if not draw:
            self.stdout.write(self.style.ERROR("\n❌ No draws available!"))
            self.stdout.write(self.style.WARNING("Run with --create-data flag\n"))
            return
        
        # Step 5: Create a test bet
        self.stdout.write("\n💰 Step 4: Creating Test Bet...")
        bet = self.create_test_bet(user, draw)
        if not bet:
            self.stdout.write(self.style.ERROR("\n❌ Bet creation failed!\n"))
            return
        
        # Step 6: Test API queryset
        self.stdout.write("\n🔍 Step 5: Testing API Queryset...")
        bets = self.test_api_queryset(user)
        
        # Step 7: Test serialization
        self.stdout.write("\n📦 Step 6: Testing Serialization...")
        self.test_serialization(user)
        
        # Step 8: Summary
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("✅ TEST COMPLETE!"))
        self.stdout.write("="*70)
        
        # Show API test command
        self.stdout.write("\n📡 Test API with PowerShell:")
        self.stdout.write("="*70)
        self.stdout.write("""
$loginBody = @{
    username = "%s"
    password = "TestPass123!"
} | ConvertTo-Json

$response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login/" -Method POST -Body $loginBody -ContentType "application/json"
$token = $response.tokens.access

$headers = @{ "Authorization" = "Bearer $token" }
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/betting/bets/" -Method GET -Headers $headers
        """ % username)
        self.stdout.write("="*70 + "\n")
    
    def create_test_data(self):
        """Create all necessary test data"""
        self.stdout.write(self.style.WARNING("\n🔧 Creating test data..."))
        
        # Create user
        user, created = User.objects.get_or_create(
            username='testuser',
            defaults={
                'email': 'test@example.com',
                'first_name': 'Test',
                'last_name': 'User',
                'date_of_birth': '2000-01-01',
                'phone_number': '+233501234567',
                'account_balance': Decimal('1000.00'),
                'user_type': 'player'
            }
        )
        if created:
            user.set_password('TestPass123!')
            user.save()
            self.stdout.write(self.style.SUCCESS(f"  ✓ Created user: {user.username}"))
        else:
            # Update balance if user exists
            user.account_balance = Decimal('1000.00')
            user.save()
            self.stdout.write(self.style.WARNING(f"  ⚠ User exists: {user.username} (balance updated)"))
        
        # Create bet type
        bet_type, created = BetType.objects.get_or_create(
            name='direct',
            defaults={
                'display_name': 'Direct',
                'description': 'All numbers must match in exact order',
                'base_odds': Decimal('180000.00'),
                'min_numbers_required': 5,
                'max_numbers_allowed': 5,
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"  ✓ Created bet type: {bet_type.display_name}"))
        else:
            self.stdout.write(self.style.WARNING(f"  ⚠ Bet type exists: {bet_type.display_name}"))
        
        # Create game type
        game, created = GameType.objects.get_or_create(
            code='MON_SPECIAL',
            defaults={
                'name': 'Monday Special',
                'category': 'nla_590',
                'description': 'Weekly Monday lottery draw',
                'min_numbers': 5,
                'max_numbers': 5,
                'number_range_start': 1,
                'number_range_end': 90,
                'min_stake': Decimal('1.00'),
                'max_stake': Decimal('1000.00'),
                'draw_time': '18:30:00',
                'draw_days': 'Monday',
                'is_active': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"  ✓ Created game: {game.name}"))
        else:
            self.stdout.write(self.style.WARNING(f"  ⚠ Game exists: {game.name}"))
        
        # Create game odds
        odds, created = GameOdds.objects.get_or_create(
            game_type=game,
            bet_type=bet_type,
            numbers_count=5,
            numbers_matched=5,
            defaults={
                'payout_multiplier': Decimal('180000.00')
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"  ✓ Created odds: 5/5"))
        else:
            self.stdout.write(self.style.WARNING(f"  ⚠ Odds exist: 5/5"))
        
        # Create open draw
        tomorrow = timezone.now() + timedelta(days=1)
        draw_number = f'MON{tomorrow.strftime("%Y%m%d")}'
        draw, created = Draw.objects.get_or_create(
            draw_number=draw_number,
            defaults={
                'game_type': game,
                'draw_date': tomorrow.date(),
                'draw_time': '18:30:00',
                'status': 'open',
                'betting_opens_at': timezone.now(),
                'betting_closes_at': tomorrow.replace(hour=18, minute=0, second=0, microsecond=0)
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"  ✓ Created draw: {draw.draw_number}"))
        else:
            self.stdout.write(self.style.WARNING(f"  ⚠ Draw exists: {draw.draw_number}"))
        
        self.stdout.write(self.style.SUCCESS("\n✅ Test data creation complete!\n"))
    
    def verify_components(self):
        """Verify all system components exist"""
        
        # Check Game Types
        games = GameType.objects.filter(is_active=True)
        self.stdout.write(f"  Game Types: {games.count()}")
        for game in games:
            self.stdout.write(f"    - {game.name} ({game.code})")
        
        # Check Bet Types
        bet_types = BetType.objects.filter(is_active=True)
        self.stdout.write(f"  Bet Types: {bet_types.count()}")
        for bt in bet_types:
            self.stdout.write(f"    - {bt.display_name} (Odds: {bt.base_odds})")
        
        # Check Draws
        draws = Draw.objects.all()
        self.stdout.write(f"  Total Draws: {draws.count()}")
        open_draws = draws.filter(status='open')
        self.stdout.write(f"  Open Draws: {open_draws.count()}")
        
        if games.count() == 0 or bet_types.count() == 0:
            return False
        
        return True
    
    def check_user(self, username):
        """Check if user exists and has balance"""
        try:
            user = User.objects.get(username=username)
            self.stdout.write(self.style.SUCCESS(f"  ✓ User found: {user.username}"))
            self.stdout.write(f"    Email: {user.email}")
            self.stdout.write(f"    Balance: GH₵{user.account_balance}")
            self.stdout.write(f"    User Type: {user.user_type}")
            
            if user.account_balance < Decimal('1.00'):
                self.stdout.write(self.style.WARNING("    ⚠ Low balance! Adding funds..."))
                user.account_balance = Decimal('1000.00')
                user.save()
                self.stdout.write(self.style.SUCCESS(f"    ✓ Balance updated to GH₵{user.account_balance}"))
            
            return user
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"  ❌ User '{username}' not found!"))
            return None
    
    def check_draws(self):
        """Check available draws"""
        open_draws = Draw.objects.filter(status='open')
        
        if open_draws.count() == 0:
            self.stdout.write(self.style.ERROR("  ❌ No open draws available!"))
            return None
        
        draw = open_draws.first()
        self.stdout.write(self.style.SUCCESS(f"  ✓ Found open draw: {draw.draw_number}"))
        self.stdout.write(f"    Game: {draw.game_type.name}")
        self.stdout.write(f"    Date: {draw.draw_date}")
        self.stdout.write(f"    Status: {draw.status}")
        self.stdout.write(f"    Betting Open: {draw.is_betting_open()}")
        self.stdout.write(f"    Total Bets: {draw.total_bets}")
        
        return draw
    
    def create_test_bet(self, user, draw):
        """Create a test bet"""
        from betting.models import generate_bet_number
        
        bet_type = BetType.objects.filter(is_active=True).first()
        
        # Create bet
        bet = Bet.objects.create(
            user=user,
            draw=draw,
            bet_type=bet_type,
            bet_number=generate_bet_number(),
            selected_numbers=[5, 12, 23, 45, 67],
            stake_amount=Decimal('2.00'),
            status='active'
        )
        
        # Calculate potential winnings
        bet.calculate_potential_winnings()
        
        self.stdout.write(self.style.SUCCESS(f"  ✓ Bet created successfully!"))
        self.stdout.write(f"    Bet Number: {bet.bet_number}")
        self.stdout.write(f"    Bet ID: {bet.id}")
        self.stdout.write(f"    User: {bet.user.username}")
        self.stdout.write(f"    Draw: {bet.draw.draw_number}")
        self.stdout.write(f"    Numbers: {bet.selected_numbers}")
        self.stdout.write(f"    Stake: GH₵{bet.stake_amount}")
        self.stdout.write(f"    Potential Win: GH₵{bet.potential_winnings}")
        self.stdout.write(f"    Status: {bet.status}")
        
        return bet
    
    def test_api_queryset(self, user):
        """Test the API queryset logic"""
        self.stdout.write("  Testing queryset filters...")
        
        # Test 1: All user's bets
        all_bets = Bet.objects.filter(user=user)
        self.stdout.write(f"    All bets for {user.username}: {all_bets.count()}")
        
        # Test 2: With select_related
        optimized_bets = Bet.objects.filter(user=user).select_related(
            'draw', 'draw__game_type', 'bet_type'
        )
        self.stdout.write(f"    Optimized query count: {optimized_bets.count()}")
        
        # Test 3: Active bets only
        active_bets = Bet.objects.filter(user=user, status='active')
        self.stdout.write(f"    Active bets: {active_bets.count()}")
        
        # Test 4: Print bet details
        if all_bets.exists():
            self.stdout.write(self.style.SUCCESS("\n  ✓ Bets found in database!"))
            self.stdout.write("\n  📋 Bet Details:")
            for bet in all_bets[:5]:  # Show first 5
                self.stdout.write(f"\n    Bet #{bet.id}:")
                self.stdout.write(f"      Number: {bet.bet_number}")
                self.stdout.write(f"      User: {bet.user.username if bet.user else 'NULL'}")
                self.stdout.write(f"      Draw: {bet.draw.draw_number if bet.draw else 'NULL'}")
                self.stdout.write(f"      Game: {bet.draw.game_type.name if bet.draw and bet.draw.game_type else 'NULL'}")
                self.stdout.write(f"      Bet Type: {bet.bet_type.display_name if bet.bet_type else 'NULL'}")
                self.stdout.write(f"      Status: {bet.status}")
                self.stdout.write(f"      Stake: GH₵{bet.stake_amount}")
        else:
            self.stdout.write(self.style.ERROR("  ❌ No bets found in database!"))
        
        return all_bets
    
    def test_serialization(self, user):
        """Test bet serialization"""
        from betting.serializers import BetSerializer, BetDetailSerializer
        
        bets = Bet.objects.filter(user=user).select_related(
            'draw', 'draw__game_type', 'bet_type'
        )
        
        if not bets.exists():
            self.stdout.write(self.style.ERROR("  ❌ No bets to serialize"))
            return
        
        # Test BetSerializer (list view)
        self.stdout.write("  Testing BetSerializer...")
        serializer = BetSerializer(bets, many=True)
        data = serializer.data
        
        self.stdout.write(f"    Database count: {bets.count()}")
        self.stdout.write(f"    Serialized count: {len(data)}")
        
        if len(data) == 0:
            self.stdout.write(self.style.ERROR("\n  ❌ ISSUE FOUND: Serializer returns EMPTY array!"))
            self.stdout.write("     Even though bets exist in database.\n")
            
            # Debug first bet
            bet = bets.first()
            self.stdout.write("  🔍 Debugging first bet:")
            self.stdout.write(f"     Bet ID: {bet.id}")
            self.stdout.write(f"     Bet Number: {bet.bet_number}")
            self.stdout.write(f"     User: {bet.user}")
            self.stdout.write(f"     Draw: {bet.draw}")
            self.stdout.write(f"     Draw Game Type: {bet.draw.game_type if bet.draw else 'NULL'}")
            self.stdout.write(f"     Bet Type: {bet.bet_type}")
            
            # Try serializing single bet
            self.stdout.write("\n  Testing single bet serialization...")
            single_serializer = BetSerializer(bet)
            single_data = single_serializer.data
            
            if single_data:
                self.stdout.write(self.style.SUCCESS("  ✓ Single bet serialized!"))
                self.stdout.write(f"     Data: {json.dumps(single_data, indent=6)}")
            else:
                self.stdout.write(self.style.ERROR("  ❌ Single bet also returns empty!"))
                self.stdout.write("     This indicates a serializer field issue.")
        else:
            self.stdout.write(self.style.SUCCESS("\n  ✅ Serializer working correctly!"))
            self.stdout.write("\n  📦 Sample Serialized Data:")
            sample = data[0]
            self.stdout.write(f"{json.dumps(sample, indent=6, default=str)}")
            
            # Check for common issues
            self.stdout.write("\n  🔍 Checking serialized fields...")
            required_fields = ['id', 'bet_number', 'stake_amount', 'status']
            for field in required_fields:
                if field in sample:
                    self.stdout.write(self.style.SUCCESS(f"      ✓ Field '{field}': {sample[field]}"))
                else:
                    self.stdout.write(self.style.ERROR(f"      ❌ Field '{field}': MISSING"))