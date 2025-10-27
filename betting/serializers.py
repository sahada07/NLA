from rest_framework import serializers
from django.utils import timezone
from decimal import Decimal
from .models import (
    GameType, BetType, GameOdds, Draw, Bet, 
    BetTransaction, UserSubscription, Notification,
    generate_bet_number, generate_transaction_reference
)
from users.models import User


class GameTypeSerializer(serializers.ModelSerializer):
    """List and detail view of game types"""
    
    class Meta:
        model = GameType
        fields = [
            'id', 'name', 'code', 'category', 'description',
            'min_numbers', 'max_numbers', 'number_range_start', 'number_range_end',
            'min_stake', 'max_stake', 'draw_time', 'draw_days', 'is_active'
        ]
        read_only_fields = ['id']

class BetTypeSerializer(serializers.ModelSerializer):
    """Available bet types"""
    
    class Meta:
        model = BetType
        fields = [
            'id', 'name', 'display_name', 'description',
            'base_odds', 'min_numbers_required', 'max_numbers_allowed'
        ]
        read_only_fields = ['id']

class GameOddsSerializer(serializers.ModelSerializer):
    """Payout odds for different combinations"""
    
    game_name = serializers.CharField(source='game_type.name', read_only=True)
    bet_type_name = serializers.CharField(source='bet_type.display_name', read_only=True)
    
    class Meta:
        model = GameOdds
        fields = [
            'id', 'game_type', 'game_name', 'bet_type', 'bet_type_name',
            'numbers_count', 'numbers_matched', 'payout_multiplier'
        ]
        read_only_fields = ['id']


class DrawListSerializer(serializers.ModelSerializer):
    """List view of draws"""
    
    game_name = serializers.CharField(source='game_type.name', read_only=True)
    is_betting_open = serializers.SerializerMethodField()
    time_until_close = serializers.SerializerMethodField()
    
    class Meta:
        model = Draw
        fields = [
            'id', 'game_type', 'game_name', 'draw_number',
            'draw_date', 'draw_time', 'status',
            'betting_opens_at', 'betting_closes_at',
            'is_betting_open', 'time_until_close',
            'total_bets', 'total_stake_amount'
        ]
        read_only_fields = ['id']
    
    def get_is_betting_open(self, obj):
        return obj.is_betting_open()
    
    def get_time_until_close(self, obj):
        if obj.status != 'open':
            return None
        now = timezone.now()
        if now > obj.betting_closes_at:
            return "Closed"
        delta = obj.betting_closes_at - now
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    
class DrawDetailSerializer(DrawListSerializer):
    """Detailed view of a draw including results"""
    
    winning_numbers = serializers.JSONField(read_only=True)
    machine_number = serializers.CharField(read_only=True)
    
    class Meta(DrawListSerializer.Meta):
        fields = DrawListSerializer.Meta.fields + [
            'winning_numbers', 'machine_number', 
            'total_payout_amount', 'created_at', 'updated_at'
        ]
# BET SERIALIZERS
class PlaceBetSerializer(serializers.Serializer):
    """Serializer for placing a new bet"""
    
    draw_id = serializers.IntegerField()
    bet_type_id = serializers.IntegerField()
    selected_numbers = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=90),
        min_length=1,
        max_length=10
    )
    stake_amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01')
    )
    
    def validate(self, attrs):
        # Validate draw exists and is open
        try:
            draw = Draw.objects.get(id=attrs['draw_id'])
        except Draw.DoesNotExist:
            raise serializers.ValidationError({"draw_id": "Draw not found"})
        
        if not draw.is_betting_open():
            raise serializers.ValidationError({"draw_id": "Betting is closed for this draw"})
        
        # Validate bet type
        try:
            bet_type = BetType.objects.get(id=attrs['bet_type_id'])
        except BetType.DoesNotExist:
            raise serializers.ValidationError({"bet_type_id": "Bet type not found"})
        
        # Validate number count
        numbers_count = len(attrs['selected_numbers'])
        if numbers_count < bet_type.min_numbers_required:
            raise serializers.ValidationError({
                "selected_numbers": f"Minimum {bet_type.min_numbers_required} numbers required"
            })
        if numbers_count > bet_type.max_numbers_allowed:
            raise serializers.ValidationError({
                "selected_numbers": f"Maximum {bet_type.max_numbers_allowed} numbers allowed"
            })
        
        # Validate numbers are within game range
        game = draw.game_type
        for num in attrs['selected_numbers']:
            if num < game.number_range_start or num > game.number_range_end:
                raise serializers.ValidationError({
                    "selected_numbers": f"Numbers must be between {game.number_range_start} and {game.number_range_end}"
                })
        
        # Check for duplicate numbers
        if len(attrs['selected_numbers']) != len(set(attrs['selected_numbers'])):
            raise serializers.ValidationError({
                "selected_numbers": "Duplicate numbers are not allowed"
            })
        
        # Validate stake amount
        if attrs['stake_amount'] < game.min_stake:
            raise serializers.ValidationError({
                "stake_amount": f"Minimum stake is GH₵{game.min_stake}"
            })
        if attrs['stake_amount'] > game.max_stake:
            raise serializers.ValidationError({
                "stake_amount": f"Maximum stake is GH₵{game.max_stake}"
            })
        
        # Check user has sufficient balance
        user = self.context['request'].user
        if user.account_balance < attrs['stake_amount']:
            raise serializers.ValidationError({
                "stake_amount": f"Insufficient balance. Your balance: GH₵{user.account_balance}"
            })
        
        attrs['draw'] = draw
        attrs['bet_type'] = bet_type
        attrs['game'] = game
        
        return attrs
    
    def create(self, validated_data):
        user = self.context['request'].user
        draw = validated_data['draw']
        bet_type = validated_data['bet_type']
        stake_amount = validated_data['stake_amount']
        selected_numbers = validated_data['selected_numbers']
        
        # Create bet
        bet = Bet.objects.create(
            user=user,
            draw=draw,
            bet_type=bet_type,
            bet_number=generate_bet_number(),
            selected_numbers=selected_numbers,
            stake_amount=stake_amount,
            status='active'
        )
        
        # Calculate potential winnings
        bet.calculate_potential_winnings()
        
        # Deduct stake from user balance
        user.account_balance -= stake_amount
        user.save()
        
        # Create transaction record
        BetTransaction.objects.create(
            bet=bet,
            user=user,
            transaction_type='stake',
            amount=stake_amount,
            balance_before=user.account_balance + stake_amount,
            balance_after=user.account_balance,
            reference=generate_transaction_reference(),
            description=f"Stake for bet {bet.bet_number}"
        )
        
        # Update draw statistics
        draw.total_bets += 1
        draw.total_stake_amount += stake_amount
        draw.save()
        
        # Send notification
        Notification.objects.create(
            user=user,
            game_type=draw.game_type,
            bet=bet,
            notification_type='game_update',
            title='Bet Placed Successfully',
            message=f'Your bet {bet.bet_number} for {draw.game_type.name} has been placed. Good luck!'
        )
        
        return bet

class BetSerializer(serializers.ModelSerializer):
    """Serializer for bet details"""
    
    game_name = serializers.CharField(source='draw.game_type.name', read_only=True)
    bet_type_name = serializers.CharField(source='bet_type.display_name', read_only=True)
    draw_number = serializers.CharField(source='draw.draw_number', read_only=True)
    draw_date = serializers.DateField(source='draw.draw_date', read_only=True)
    
    class Meta:
        model = Bet
        fields = [
            'id', 'bet_number', 'game_name', 'bet_type_name',
            'draw_number', 'draw_date', 'selected_numbers',
            'stake_amount', 'potential_winnings', 'actual_winnings',
            'status', 'placed_at', 'processed_at'
        ]
        read_only_fields = ['id', 'bet_number', 'status', 'placed_at', 'processed_at']



class BetDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for single bet retrieval"""
    game_name = serializers.CharField(source='draw.game_type.name', read_only=True)
    bet_type_name = serializers.CharField(source='bet_type.display_name', read_only=True)
    draw_number = serializers.CharField(source='draw.draw_number', read_only=True)
    draw_date = serializers.DateField(source='draw.draw_date', read_only=True)
    winning_numbers = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Bet
        fields = [
            'id', 'bet_number', 'game_name', 'bet_type_name',
            'draw_number', 'draw_date', 'selected_numbers',
            'stake_amount', 'potential_winnings', 'actual_winnings',
            'status', 'placed_at', 'processed_at', 'paid_at',
            'winning_numbers', 'agent'
        ]
    
    def get_winning_numbers(self, obj):
        return obj.draw.winning_numbers if obj.draw.winning_numbers else None

class BetTransactionSerializer(serializers.ModelSerializer):
    """Transaction history for bets"""
    
    class Meta:
        model = BetTransaction
        fields = [
            'id', 'transaction_type', 'amount',
            'balance_before', 'balance_after',
            'reference', 'description', 'created_at'
        ]
        read_only_fields = ['id']

# SUBSCRIPTION SERIALIZERS

class UserSubscriptionSerializer(serializers.ModelSerializer):
    """User's game subscriptions"""
    
    game_name = serializers.CharField(source='game_type.name', read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'game_type', 'game_name',
            'is_active', 'subscribed_at', 'unsubscribed_at'
        ]
        read_only_fields = ['id', 'subscribed_at', 'unsubscribed_at']


class SubscribeGameSerializer(serializers.Serializer):
    """Subscribe to a game type"""
    
    game_type_id = serializers.IntegerField()
    
    def validate_game_type_id(self, value):
        try:
            game_type = GameType.objects.get(id=value, is_active=True)
        except GameType.DoesNotExist:
            raise serializers.ValidationError("Game type not found or inactive")
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        game_type = GameType.objects.get(id=validated_data['game_type_id'])
        
        # Get or create subscription
        subscription, created = UserSubscription.objects.get_or_create(
            user=user,
            game_type=game_type,
            defaults={'is_active': True}
        )
        
        # If it existed but was inactive, reactivate it
        if not created and not subscription.is_active:
            subscription.is_active = True
            subscription.unsubscribed_at = None
            subscription.save()
        
        return subscription


class NotificationSerializer(serializers.ModelSerializer):
    """User notifications"""
    
    game_name = serializers.CharField(source='game_type.name', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message',
            'game_name', 'is_read', 'created_at', 'read_at'
        ]
        read_only_fields = ['id', 'created_at']

# STATISTICS SERIALIZERS

class UserStatisticsSerializer(serializers.Serializer):
    """User betting statistics"""
    
    total_bets = serializers.IntegerField()
    total_staked = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_won = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_winnings = serializers.DecimalField(max_digits=15, decimal_places=2)
    win_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    active_bets = serializers.IntegerField()
    account_balance = serializers.DecimalField(max_digits=10, decimal_places=2)

