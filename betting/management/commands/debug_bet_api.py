# betting/management/commands/debug_bet_api.py
# Create this file: betting/management/commands/debug_bet_api.py

from django.core.management.base import BaseCommand
from django.test import RequestFactory
from rest_framework.test import force_authenticate
from betting.views import BetViewSet
from betting.models import Bet
from users.models import User
import json


class Command(BaseCommand):
    help = 'Debug the Bet API endpoint to find why it returns empty array'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='testuser',
            help='Username to test with',
        )
    
    def handle(self, *args, **options):
        username = options['username']
        
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("🐛 DEBUGGING BET API ENDPOINT"))
        self.stdout.write("="*70 + "\n")
        
        # Get user
        try:
            user = User.objects.get(username=username)
            self.stdout.write(self.style.SUCCESS(f"✓ Testing with user: {user.username}"))
            self.stdout.write(f"  ID: {user.id}")
            self.stdout.write(f"  Email: {user.email}\n")
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ User '{username}' not found!"))
            self.stdout.write(self.style.WARNING("Run: python manage.py test_betting_system --create-data\n"))
            return
        
        # Check database bets
        self.stdout.write("📊 Step 1: Checking Database...")
        db_bets = Bet.objects.filter(user=user)
        self.stdout.write(f"  Bets in database: {db_bets.count()}")
        
        if db_bets.count() == 0:
            self.stdout.write(self.style.ERROR("  ❌ No bets in database for this user!"))
            self.stdout.write(self.style.WARNING("  Create a bet first or run with --create-data\n"))
            return
        
        # Show bet details
        for bet in db_bets[:3]:
            self.stdout.write(f"\n  Bet #{bet.id}:")
            self.stdout.write(f"    Number: {bet.bet_number}")
            self.stdout.write(f"    Status: {bet.status}")
            self.stdout.write(f"    Stake: GH₵{bet.stake_amount}")
            self.stdout.write(f"    Draw: {bet.draw}")
            self.stdout.write(f"    Bet Type: {bet.bet_type}")
        
        # Test ViewSet queryset
        self.stdout.write("\n\n🔍 Step 2: Testing ViewSet Queryset...")
        factory = RequestFactory()
        request = factory.get('/api/betting/bets/')
        force_authenticate(request, user=user)
        
        viewset = BetViewSet()
        viewset.request = request
        viewset.format_kwarg = None
        
        queryset = viewset.get_queryset()
        self.stdout.write(f"  ViewSet queryset count: {queryset.count()}")
        
        if queryset.count() != db_bets.count():
            self.stdout.write(self.style.ERROR("  ❌ Queryset count mismatch!"))
            self.stdout.write(f"    Database: {db_bets.count()}")
            self.stdout.write(f"    ViewSet: {queryset.count()}")
        else:
            self.stdout.write(self.style.SUCCESS("  ✓ Queryset count matches database"))
        
        # Test serializer
        self.stdout.write("\n📦 Step 3: Testing Serializer...")
        serializer_class = viewset.get_serializer_class()
        self.stdout.write(f"  Serializer class: {serializer_class.__name__}")
        
        serializer = serializer_class(queryset, many=True)
        data = serializer.data
        
        self.stdout.write(f"  Serialized data length: {len(data)}")
        
        if len(data) == 0:
            self.stdout.write(self.style.ERROR("\n  ❌ PROBLEM FOUND: Serializer returns EMPTY!"))
            self.stdout.write("     Bets exist but serializer produces empty array.\n")
            
            # Test single bet
            self.stdout.write("  🔬 Testing single bet serialization...")
            bet = queryset.first()
            single_serializer = serializer_class(bet)
            single_data = single_serializer.data
            
            if single_data:
                self.stdout.write(self.style.SUCCESS("    ✓ Single bet serialized successfully!"))
                self.stdout.write(f"    Data keys: {list(single_data.keys())}")
                self.stdout.write(f"\n    Full data:")
                self.stdout.write(f"    {json.dumps(single_data, indent=6, default=str)}")
            else:
                self.stdout.write(self.style.ERROR("    ❌ Single bet also empty!"))
                self.stdout.write("    This is a serializer configuration issue.")
                
                # Check Meta fields
                self.stdout.write(f"\n    Serializer Meta fields: {serializer_class.Meta.fields}")
                
                # Check bet attributes
                self.stdout.write(f"\n    Bet attributes:")
                self.stdout.write(f"      ID: {bet.id}")
                self.stdout.write(f"      bet_number: {bet.bet_number}")
                self.stdout.write(f"      user: {bet.user}")
                self.stdout.write(f"      draw: {bet.draw}")
                self.stdout.write(f"      bet_type: {bet.bet_type}")
                self.stdout.write(f"      status: {bet.status}")
        else:
            self.stdout.write(self.style.SUCCESS("  ✓ Serializer working correctly!"))
            self.stdout.write(f"\n  Sample serialized bet:")
            self.stdout.write(f"  {json.dumps(data[0], indent=4, default=str)}")
        
        # Test full API endpoint
        self.stdout.write("\n\n🌐 Step 4: Testing Full API Response...")
        view = BetViewSet.as_view({'get': 'list'})
        response = view(request)
        
        self.stdout.write(f"  Response status: {response.status_code}")
        self.stdout.write(f"  Response type: {type(response.data)}")
        
        if response.status_code == 200:
            if isinstance(response.data, list):
                self.stdout.write(f"  Response length: {len(response.data)}")
                
                if len(response.data) == 0:
                    self.stdout.write(self.style.ERROR("\n  ❌ API RETURNS EMPTY ARRAY!"))
                    self.stdout.write("     This is the issue you're experiencing.")
                else:
                    self.stdout.write(self.style.SUCCESS("\n  ✓ API returns data successfully!"))
            else:
                self.stdout.write(self.style.ERROR(f"  ❌ Unexpected response type: {type(response.data)}"))
        else:
            self.stdout.write(self.style.ERROR(f"  ❌ API error: {response.status_code}"))
            self.stdout.write(f"  Response: {response.data}")
        
        # Summary
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("📊 DIAGNOSTIC SUMMARY"))
        self.stdout.write("="*70)
        
        self.stdout.write(f"\n  Database bets: {db_bets.count()}")
        self.stdout.write(f"  ViewSet queryset: {queryset.count()}")
        self.stdout.write(f"  Serialized count: {len(data)}")
        self.stdout.write(f"  API response count: {len(response.data) if isinstance(response.data, list) else 'N/A'}")
        
        if db_bets.count() > 0 and len(data) == 0:
            self.stdout.write(self.style.ERROR("\n  ❌ ROOT CAUSE: Serializer issue"))
            self.stdout.write("     Bets exist but serializer returns empty.")
            self.stdout.write("\n  💡 SOLUTIONS:")
            self.stdout.write("     1. Check BetSerializer fields")
            self.stdout.write("     2. Check for missing related objects (draw, bet_type)")
            self.stdout.write("     3. Try using SimpleBetSerializer")
            self.stdout.write("     4. Check for serializer method field errors")
        elif db_bets.count() > 0 and len(data) > 0:
            self.stdout.write(self.style.SUCCESS("\n  ✅ Everything working correctly!"))
        else:
            self.stdout.write(self.style.WARNING("\n  ⚠ No bets to test"))
        
        self.stdout.write("\n" + "="*70 + "\n")