# # test_direct_one.py
# # Run this in Django shell: python manage.py shell < test_direct_one.py

# from betting.models import Bet, Draw, BetType, GameType, User
# from decimal import Decimal
# from django.utils import timezone

# def test_direct_one_bets():
#     """
#     Test Direct One bet logic with various scenarios
#     """
#     print("\n" + "="*40
#     )
#     print("TESTING DIRECT ONE BET LOGIC")
#     print("="*40
#      + "\n")
    
#     # Get or create test data
#     try:
#         game_type = GameType.objects.filter(is_active=True).first()
#         bet_type = BetType.objects.get(name='direct_one')
#         user = User.objects.filter(is_superuser=False).first()
        
#         if not all([game_type, bet_type, user]):
#             print("❌ Missing required data. Please ensure you have:")
#             print("   - Active GameType")
#             print("   - BetType with name 'direct_one'")
#             print("   - At least one User")
#             return
        
#         print(f"✅ Found test data:")
#         print(f"   Game Type: {game_type.name}")
#         print(f"   Bet Type: {bet_type.display_name}")
#         print(f"   User: {user.username}")
#         print()
        
#     except Exception as e:
#         print(f"❌ Error getting test data: {e}")
#         return
    
#     # Create a test draw with completed status
#     draw = Draw.objects.create(
#         game_type=game_type,
#         draw_number=f"TEST-{timezone.now().strftime('%Y%m%d%H%M%S')}",
#         draw_date=timezone.now().date(),
#         draw_time=timezone.now().time(),
#         status='completed',
#         betting_opens_at=timezone.now() - timezone.timedelta(hours=2),
#         betting_closes_at=timezone.now() - timezone.timedelta(hours=1),
#         winning_numbers=[42, 17, 88, 23, 5]  # Test winning numbers
#     )
    
#     print(f"✅ Created test draw: {draw.draw_number}")
#     print(f"   Winning Numbers: {draw.winning_numbers}")
#     print()
    
#     # Test scenarios
#     test_cases = [
#         {
#             'name': 'WIN - Number matches first position',
#             'selected': [42],
#             'should_win': True,
#             'description': 'User selected 42, which matches first winning number'
#         },
#         {
#             'name': 'LOSE - Number in wrong position',
#             'selected': [17],
#             'should_win': False,
#             'description': 'User selected 17, but it\'s in 2nd position, not 1st'
#         },
#         {
#             'name': 'LOSE - Number not in winning numbers',
#             'selected': [99],
#             'should_win': False,
#             'description': 'User selected 99, which is not in winning numbers at all'
#         },
#         {
#             'name': 'LOSE - Number in last position',
#             'selected': [5],
#             'should_win': False,
#             'description': 'User selected 5, which is in 5th position, not 1st'
#         }
#     ]
    
#     # Save original balance
#     original_balance = user.account_balance
    
#     print("RUNNING TEST CASES:")
#     print("-" * 40
#     )
    
#     for i, test_case in enumerate(test_cases, 1):
#         print(f"\nTest {i}: {test_case['name']}")
#         print(f"Description: {test_case['description']}")
#         print(f"Selected: {test_case['selected']}")
#         print(f"Expected: {'WIN' if test_case['should_win'] else 'LOSE'}")
        
#         # Create bet
#         bet = Bet.objects.create(
#             user=user,
#             draw=draw,
#             bet_type=bet_type,
#             bet_number=f"TEST-BET-{i}",
#             selected_numbers=test_case['selected'],
#             stake_amount=Decimal('10.00'),
#             status='active'
#         )
        
#         # Calculate potential winnings
#         bet.calculate_potential_winnings()
#         print(f"Potential Winnings: GH₵{bet.potential_winnings}")
        
#         # Check win
#         result = bet.check_win()
        
#         # Verify result
#         passed = result == test_case['should_win']
#         status_icon = "✅" if passed else "❌"
        
#         print(f"Actual: {bet.status.upper()}")
#         print(f"Actual Winnings: GH₵{bet.actual_winnings}")
#         print(f"{status_icon} Test {'PASSED' if passed else 'FAILED'}")
#         print("-" * 40)
        
#         # Restore balance for next test
#         user.account_balance = original_balance
#         user.save()
    
#     # Cleanup
#     print("\n🧹 Cleaning up test data...")
#     Bet.objects.filter(bet_number__startswith='TEST-BET-').delete()
#     draw.delete()
    
#     print("✅ Cleanup complete")
#     print("\n" + "="*40
#     )
#     print("TESTING COMPLETE")
#     print("="*40
#      + "\n")

# if __name__ == "__main__":
#     test_direct_one_bets()