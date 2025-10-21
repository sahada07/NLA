from rest_framework import serializers
from .models import GameType,UserSubscription,Notification



class GameTypeSerializer(serializers.ModelSerializer):
    subscriber_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    
    class Meta:
        model = GameType
        fields = ('id', 'name', 'code', 'category', 'description', 
                 'is_active', 'notification_frequency', 
                 'subscriber_count', 'is_subscribed')
    
    def get_subscriber_count(self, obj):
        return obj.subscribers.filter(is_active=True).count()
    
    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.subscribers.filter(
                user=request.user, 
                is_active=True
            ).exists()
        return False

class UserSubscriptionSerializer(serializers.ModelSerializer):
    game_type_name = serializers.CharField(source='game_type.name', read_only=True)
    game_type_category = serializers.CharField(source='game_type.category', read_only=True)
    
    class Meta:
        model = UserSubscription
        fields = ('id', 'game_type', 'game_type_name', 'game_type_category',
                 'is_active', 'subscribed_at', 'unsubscribe_at')
        read_only_fields = ('subscribed_at', 'unsubscribe_at')

class SubscribeSerializer(serializers.Serializer):
    game_type_id = serializers.IntegerField()
    subscribe = serializers.BooleanField(default=True)
    
    def validate_game_type_id(self, value):
        try:
            game_type = GameType.objects.get(id=value, is_active=True)
            return value
        except GameType.DoesNotExist:
            raise serializers.ValidationError("Invalid game type")

class NotificationSerializer(serializers.ModelSerializer):
    game_type_name = serializers.CharField(
        source='game_type.name', 
        read_only=True, 
        allow_null=True
    )
    
    class Meta:
        model = Notification
        fields = ('id', 'game_type', 'game_type_name', 'notification_type',
                 'title', 'message', 'is_read', 'created_at', 'sent_at')
        read_only_fields = ('created_at', 'sent_at')