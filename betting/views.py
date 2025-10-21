# betting/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import permission_classes
from rest_framework import permissions
from rest_framework.viewsets import GenericViewSet,ModelViewSet
from rest_framework.mixins import ListModelMixin,RetrieveModelMixin
from .models import GameType,UserSubscription,Notification
from .serializers import (GameTypeSerializer,UserSubscriptionSerializer,SubscribeSerializer,NotificationSerializer)
from django.utils import timezone
from rest_framework.decorators import action


class GameTypeViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = GameType.objects.filter(is_active=True)
    serializer_class = GameTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

class SubscriptionViewSet(ModelViewSet):
    serializer_class = UserSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserSubscription.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def toggle_subscription(self, request):
        """Subscribe or unsubscribe from a game type"""
        serializer = SubscribeSerializer(data=request.data)
        if serializer.is_valid():
            game_type_id = serializer.validated_data['game_type_id']
            subscribe = serializer.validated_data['subscribe']
            
            try:
                game_type = GameType.objects.get(id=game_type_id)
                
                if subscribe:
                    # Subscribe
                    subscription, created = UserSubscription.objects.get_or_create(
                        user=request.user,
                        game_type=game_type,
                        defaults={'is_active': True}
                    )
                    if not created:
                        subscription.is_active = True
                        subscription.unsubscribe_at = None
                        subscription.save()
                    
                    message = f"Subscribed to {game_type.name} successfully"
                    status_code = status.HTTP_201_CREATED
                else:
                    # Unsubscribe
                    subscription = UserSubscription.objects.get(
                        user=request.user,
                        game_type=game_type
                    )
                    subscription.is_active = False
                    subscription.unsubscribe_at = timezone.now()
                    subscription.save()
                    
                    message = f"Unsubscribed from {game_type.name} successfully"
                    status_code = status.HTTP_200_OK
                
                return Response({
                    'status': 'success',
                    'message': message,
                    'subscription': UserSubscriptionSerializer(subscription).data
                }, status=status_code)
                
            except GameType.DoesNotExist:
                return Response({
                    'error': 'Game type not found'
                }, status=status.HTTP_404_NOT_FOUND)
            except UserSubscription.DoesNotExist:
                return Response({
                    'error': 'Subscription not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_subscriptions(self, request):
        """Get current user's active subscriptions"""
        subscriptions = self.get_queryset().filter(is_active=True)
        serializer = self.get_serializer(subscriptions, many=True)
        return Response(serializer.data)

class NotificationViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        updated = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).update(is_read=True)
        
        return Response
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark a specific notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        
        return Response({
            'message': 'Notification marked as read'
        })
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """Get count of unread notifications"""
        count = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
        
        return Response({'unread_count': count})
