
from django.db import models
from users.models import User
from django.core.validators import MinValueValidator,MaxValueValidator
from decimal import Decimal
import json
from django.utils import timezone
from django.db import models



# betting/models.py - UPDATED GameType model
class GameType(models.Model):
    """Main game types (e.g., Monday Special, VAG Monday, etc.)"""
    
    GAME_CHOICES = [
        # NLA 5/90 Games
        ('NLA 5/90', 'NLA 5/90'),
        ('Monday Special', 'Monday Special'),
        ('Lucky Tuesday', 'Lucky Tuesday'),
        ('Midweek', 'Midweek'),
        ('Fortune Thursday', 'Fortune Thursday'),
        ('Friday Bonanza', 'Friday Bonanza'),
        ('National Weekly', 'National Weekly'),
        ('Sunday Aseda', 'Sunday Aseda'),
        
        # VAG Games
        ('VAG Games', 'VAG Games'),
        ('VAG Monday', 'VAG Monday'),
        ('VAG Tuesday', 'VAG Tuesday'),
        ('VAG Wednesday', 'VAG Wednesday'),
        ('VAG Thursday', 'VAG Thursday'),
        ('VAG Friday', 'VAG Friday'),
        ('VAG Saturday', 'VAG Saturday'),
        ('VAG Sunday', 'VAG Sunday'),

        # Noon Rush
        ('Noon Rush', 'Noon Rush'),
        ('Noon Monday', 'Noon Monday'),
        ('Noon Tuesday', 'Noon Tuesday'),
        ('Noon Wednesday', 'Noon Wednesday'),
        ('Noon Thursday', 'Noon Thursday'),
        ('Noon Friday', 'Noon Friday'),
        ('Noon Saturday', 'Noon Saturday'),

        # Other
        ('Quick 5/11', 'Quick 5/11')
    ]
    
    CATEGORY_CHOICES = [
        ('nla_590', 'NLA 5/90'),
        ('vag_games', 'VAG Games'),
        ('noon_rush', 'Noon Rush'),
        ('other_games', 'Other Games'),
    ]
    
    NOTIFICATION_FREQUENCIES = [
        ('instant', 'Instant'),
        ('daily', 'Daily Digest'),
        ('weekly', 'Weekly Digest'),
    ]
    
    name = models.CharField(max_length=100, choices=GAME_CHOICES)
    code = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=100, choices=CATEGORY_CHOICES, default='nla_590')
    description = models.TextField()
    
    # Game Configuration
    min_numbers = models.IntegerField(default=1, help_text="Minimum numbers to pick")
    max_numbers = models.IntegerField(default=5, help_text="Maximum numbers to pick")
    number_range_start = models.IntegerField(default=1, help_text="Starting number")
    number_range_end = models.IntegerField(default=90, help_text="Ending number")
    
    # Stake Configuration
    min_stake = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('1.00'),
        help_text="Minimum stake amount"
    )
    max_stake = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('1000.00'),
        help_text="Maximum stake amount"
    )
    
    # Draw Configuration
    draw_time = models.TimeField(null=True, blank=True, help_text="Time of draw")
    draw_days = models.CharField(
        max_length=100,
        help_text="Comma-separated days (e.g., 'Monday,Wednesday,Friday')"
    )
    
    # Subscription Configuration
    notification_frequency = models.CharField(
        max_length=20,
        choices=NOTIFICATION_FREQUENCIES,
        default='instant',
        help_text="How often to send notifications"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'game_types'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.category})"
    
class BetType(models.Model):
    """Different ways to bet (e.g., Direct, Permutation, Banker, etc.)"""
    
    BET_TYPE_CHOICES = [
        ('direct', 'Direct'),           # All numbers must match in exact order
        ('perm', 'Permutation'),        # Numbers can be in any order
        ('banker', 'Banker'),           # One number guaranteed + others
        ('against', 'Against'),         # Bet that number WON'T appear
        ('machine', 'Machine Pick'),    # Random numbers
    ]
    
    name = models.CharField(max_length=50, choices=BET_TYPE_CHOICES, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField()
    
    # Odds Configuration
    base_odds = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Base payout multiplier (e.g., 180000 for 5/90)"
    )
    
    # Requirements
    min_numbers_required = models.IntegerField(default=1)
    max_numbers_allowed = models.IntegerField(default=5)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
     db_table = 'bet_type'
    
    def __str__(self):
        return self.display_name
    
    def calculate_payout(self, stake_amount, numbers_matched):
        """Calculate winnings based on stake and matched numbers"""
        # This is simplified - real calculation is more complex
        if numbers_matched >= self.min_numbers_required:
            return stake_amount * self.base_odds
        return Decimal('0.00')

class GameOdds(models.Model):
    """Payout odds for different number combinations"""
    
    game_type = models.ForeignKey(GameType, on_delete=models.CASCADE, related_name='odds')
    bet_type = models.ForeignKey(BetType, on_delete=models.CASCADE, related_name='odds')
    
    numbers_count = models.IntegerField(
        help_text="How many numbers in the bet (e.g., 2, 3, 5)"
    )
    numbers_matched = models.IntegerField(
        help_text="How many numbers must match to win"
    )
    
    payout_multiplier = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Multiply stake by this to get winnings"
    )
    
    class Meta:
        db_table = 'game_odds'
        unique_together = ['game_type', 'bet_type', 'numbers_count', 'numbers_matched']
    
    def __str__(self):
        return f"{self.game_type.name} - {self.bet_type.name} - {self.numbers_matched}/{self.numbers_count}"

class Draw(models.Model):
    """A specific draw/game instance"""
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('open', 'Open for Betting'),
        ('closed', 'Betting Closed'),
        ('drawing', 'Draw in Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    game_type = models.ForeignKey(GameType, on_delete=models.CASCADE)
    draw_number = models.CharField(max_length=50, unique=True)
    draw_date = models.DateField()
    draw_time = models.TimeField()
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Betting Window
    betting_opens_at = models.DateTimeField()
    betting_closes_at = models.DateTimeField()
    
    # Results
    winning_numbers = models.JSONField(
        null=True, 
        blank=True,
        help_text="Array of winning numbers e.g., [5, 12, 23, 45, 67]"
    )
    machine_number = models.CharField(max_length=50, blank=True)
    
    # Statistics
    total_bets = models.IntegerField(default=0)
    total_stake_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_payout_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'draws'
        ordering = ['-draw_date', '-draw_time']
    
    def __str__(self):
        return f"{self.game_type.name} - {self.draw_number}"
    
    def is_betting_open(self):
        """Check if betting is currently open"""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.status == 'open' and
            self.betting_opens_at <= now <= self.betting_closes_at
        )

class Bet(models.Model):
    """A user's bet on a specific draw"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('won', 'Won'),
        ('lost', 'Lost'),
        ('cancelled', 'Cancelled'),
        ('paid', 'Paid Out'),
    ]
    
    # Relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bets')
    draw = models.ForeignKey(Draw, on_delete=models.CASCADE, related_name='bets')
    bet_type = models.ForeignKey(BetType, on_delete=models.PROTECT, related_name='bets')
    
    # Bet Details
    bet_number = models.CharField(max_length=50, unique=True)
    selected_numbers = models.JSONField(
        help_text="Array of numbers selected e.g., [5, 12, 23]"
    )
    
    # Financial
    stake_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    potential_winnings = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    actual_winnings = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        help_text="Actual amount won (0 if lost)"
    )
    
    # Status & Timestamps
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    placed_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Agent Information (if bet placed by agent)
    agent = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='agent_bets',
        limit_choices_to={'user_type': 'agent'}
    )
    agent_commission = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Commission earned by agent"
    )
    
    class Meta:
        db_table = 'bets'
        ordering = ['-placed_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['draw', 'status']),
            models.Index(fields=['bet_number']),
        ]
    
    def __str__(self):
        return f"{self.bet_number} - {self.user.username} - GH₵{self.stake_amount}"
    
    def calculate_potential_winnings(self):
        """Calculate how much the user could win"""
        # Get the odds for this bet type and game
        try:
            odds = GameOdds.objects.get(
                game_type=self.draw.game_type,
                bet_type=self.bet_type,
                numbers_count=len(self.selected_numbers)
            )
            self.potential_winnings = self.stake_amount * odds.payout_multiplier
        except GameOdds.DoesNotExist:
            # Use base odds from bet type
            self.potential_winnings = self.stake_amount * self.bet_type.base_odds
        
        self.save()
        return self.potential_winnings
    
    def check_win(self):
        """Check if this bet won after draw results are published"""
        if not self.draw.winning_numbers:
            return False
        
        winning_set = set(self.draw.winning_numbers)
        selected_set = set(self.selected_numbers)
        
        if self.bet_type.name == 'direct':
            # All numbers must match in exact order
            won = self.selected_numbers == self.draw.winning_numbers[:len(self.selected_numbers)]
        elif self.bet_type.name == 'perm':
            # Numbers can be in any order
            won = selected_set.issubset(winning_set)
        elif self.bet_type.name == 'against':
            # Bet that number WON'T appear
            won = selected_set.isdisjoint(winning_set)
        else:
            # Default: check if any numbers match
            won = len(selected_set.intersection(winning_set)) >= self.bet_type.min_numbers_required
        
        if won:
            self.status = 'won'
            self.actual_winnings = self.potential_winnings
            
            # Update user balance
            self.user.account_balance += self.actual_winnings
            self.user.save()
        else:
            self.status = 'lost'
            self.actual_winnings = Decimal('0.00')
        
        self.processed_at = timezone.now()
        self.save()
 
        return won

class BetTransaction(models.Model):
    """Financial transaction for a bet"""
    
    TRANSACTION_TYPES = [
        ('stake', 'Stake Payment'),
        ('win', 'Winnings Payout'),
        ('refund', 'Refund'),
        ('commission', 'Agent Commission'),
    ]
    
    bet = models.ForeignKey(Bet, on_delete=models.CASCADE, related_name='transactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bet_transactions')
    
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    balance_before = models.DecimalField(max_digits=10, decimal_places=2)
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    
    reference = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'bet_transactions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_type} - GH₵{self.amount} - {self.user.username}"
   
class UserSubscription(models.Model):
    """User subscriptions to game types for notifications"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    game_type = models.ForeignKey(GameType, on_delete=models.CASCADE, related_name='subscribers')
    
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'user_subscriptions'
        unique_together = ['user', 'game_type']
    
    def __str__(self):
        return f"{self.user.username} - {self.game_type.name}"


class Notification(models.Model):
    """Notifications sent to users"""
    
    NOTIFICATION_TYPES = [
        ('game_update', 'Game Update'),
        ('draw_result', 'Draw Result'),
        ('bet_won', 'Bet Won'),
        ('bet_lost', 'Bet Lost'),
        ('new_game', 'New Game'),
        ('promotion', 'Promotion'),
        ('system', 'System Alert'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    game_type = models.ForeignKey(
        GameType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    bet = models.ForeignKey(
        Bet,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


from django.utils import timezone
import uuid

def generate_bet_number():
    """Generate unique bet number"""
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    random_part = str(uuid.uuid4().hex)[:6].upper()
    return f"BET{timestamp}{random_part}"


def generate_transaction_reference():
    """Generate unique transaction reference"""
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    random_part = str(uuid.uuid4().hex)[:8].upper()
    return f"TXN{timestamp}{random_part}"

