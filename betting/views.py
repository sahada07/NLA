# betting/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import permission_classes
from rest_framework import permissions
from rest_framework.viewsets import GenericViewSet,ModelViewSet
from rest_framework.mixins import ListModelMixin,RetrieveModelMixin
from .models import GameType,GameOdds,Draw,UserSubscription,Notification,Bet
from .serializers import (GameTypeSerializer,UserSubscriptionSerializer,DrawListSerializer,DrawDetailSerializer,NotificationSerializer,
                           GameOddsSerializer,SubscribeGameSerializer,BetSerializer,BetDetailSerializer,PlaceBetSerializer,UserStatisticsSerializer   )
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework import viewsets,status,filters
from rest_framework.permissions import IsAuthenticated,AllowAny
from django.db.models import Q,Count,Sum 
from decimal import Decimal


class GameTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing game types
    
    list: Get all active game types
    retrieve: Get details of a specific game type
    """
    
    queryset = GameType.objects.filter(is_active=True)
    serializer_class = GameTypeSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'category']
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get all game categories"""
        categories = GameType.objects.filter(
            is_active=True
        ).values('category').distinct()
        
        return Response({
            'categories': [cat['category'] for cat in categories]
        })
    
    @action(detail=True, methods=['get'])
    def odds(self, request, pk=None):
        """Get odds for a specific game"""
        game_type = self.get_object()
        odds = GameOdds.objects.filter(game_type=game_type)
        serializer = GameOddsSerializer(odds, many=True)
        return Response(serializer.data)

class DrawViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing draws
    
    list: Get all upcoming and recent draws
    retrieve: Get details of a specific draw
    """
    
    queryset = Draw.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['draw_number', 'game_type__name']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DrawDetailSerializer
        return DrawListSerializer
    
    def get_queryset(self):
        queryset = Draw.objects.select_related('game_type').all()
        
        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by game type
        game_type = self.request.query_params.get('game_type', None)
        if game_type:
            queryset = queryset.filter(game_type_id=game_type)
        
        # Filter upcoming
        upcoming = self.request.query_params.get('upcoming', None)
        if upcoming == 'true':
            queryset = queryset.filter(
                draw_date__gte=timezone.now().date(),
                status__in=['scheduled', 'open']
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def open(self, request):
        """Get all draws currently open for betting"""
        draws = Draw.objects.filter(
            status='open',
            betting_opens_at__lte=timezone.now(),
            betting_closes_at__gte=timezone.now()
        )
        serializer = self.get_serializer(draws, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def results(self, request, pk=None):
        """Get results for a specific draw"""
        draw = self.get_object()
        
        if draw.status != 'completed':
            return Response(
                {'error': 'Results not available yet'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'draw_number': draw.draw_number,
            'game_name': draw.game_type.name,
            'draw_date': draw.draw_date,
            'winning_numbers': draw.winning_numbers,
            'machine_number': draw.machine_number,
            'total_bets': draw.total_bets,
            'total_payout': str(draw.total_payout_amount)
        })




class SubscriptionViewSet(ModelViewSet):
    serializer_class = UserSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserSubscription.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def toggle_subscription(self, request):
        """Subscribe or unsubscribe from a game type"""
        serializer = SubscribeGameSerializer(data=request.data)
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

class BetViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing bets
    
    list: Get user's bets
    retrieve: Get details of a specific bet
    create: Place a new bet
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PlaceBetSerializer
        elif self.action == 'retrieve':
            return BetDetailSerializer
        return BetSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Bet.objects.filter(user=user).select_related(
            'draw', 'draw__game_type', 'bet_type'
        )
        
        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        # Filter by game type
        game_type = self.request.query_params.get('game_type', None)
        if game_type:
            queryset = queryset.filter(draw__game_type_id=game_type)
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Place a new bet"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bet = serializer.save()
        
        return Response(
            BetSerializer(bet).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get user's active bets"""
        bets = self.get_queryset().filter(status='active')
        serializer = self.get_serializer(bets, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get user's bet history"""
        bets = self.get_queryset().filter(
            status__in=['won', 'lost', 'paid']
        )
        serializer = self.get_serializer(bets, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def check_result(self, request, pk=None):
        """Check if a bet won or lost"""
        bet = self.get_object()
        
        if bet.draw.status != 'completed':
            return Response({
                'message': 'Draw results not available yet',
                'status': bet.status
            })
        
        # Check if bet already processed
        if bet.status in ['won', 'lost']:
            return Response({
                'bet_number': bet.bet_number,
                'status': bet.status,
                'selected_numbers': bet.selected_numbers,
                'winning_numbers': bet.draw.winning_numbers,
                'winnings': str(bet.actual_winnings)
            })
        
        # Process bet
        won = bet.check_win()
        
        return Response({
            'bet_number': bet.bet_number,
            'status': bet.status,
            'selected_numbers': bet.selected_numbers,
            'winning_numbers': bet.draw.winning_numbers,
            'won': won,
            'winnings': str(bet.actual_winnings)
        })

class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing game subscriptions
    
    list: Get user's subscriptions
    create: Subscribe to a game
    destroy: Unsubscribe from a game
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = UserSubscriptionSerializer
    
    def get_queryset(self):
        return UserSubscription.objects.filter(
            user=self.request.user
        ).select_related('game_type')
    
    def create(self, request, *args, **kwargs):
        """Subscribe to a game"""
        serializer = SubscribeGameSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        subscription = serializer.save()
        
        return Response(
            UserSubscriptionSerializer(subscription).data,
            status=status.HTTP_201_CREATED
        )
    
    def destroy(self, request, *args, **kwargs):
        """Unsubscribe from a game"""
        subscription = self.get_object()
        subscription.is_active = False
        subscription.unsubscribed_at = timezone.now()
        subscription.save()
        
        return Response(
            {'message': 'Successfully unsubscribed'},
            status=status.HTTP_200_OK
        )

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user notifications
    
    list: Get user's notifications
    retrieve: Get specific notification
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).select_related('game_type')
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications"""
        notifications = self.get_queryset().filter(is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        return Response({'message': 'Notification marked as read'})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        """Mark all notifications as read"""
        self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({'message': 'All notifications marked as read'})

class BetViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing user bets
    
    list: Get user's bets
    retrieve: Get specific bet
    create: Place a new bet
    """
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PlaceBetSerializer
        elif self.action == 'retrieve':
            return BetDetailSerializer
        return BetSerializer

class StatisticsViewSet(viewsets.ViewSet):
    """
    API endpoint for user statistics
    """
    
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """Get user's betting statistics"""
        user = request.user
        
        # Get all user's bets
        bets = Bet.objects.filter(user=user)
        
        # Calculate statistics
        total_bets = bets.count()
        total_staked = bets.aggregate(Sum('stake_amount'))['stake_amount__sum'] or Decimal('0')
        won_bets = bets.filter(status='won')
        total_won = won_bets.count()
        total_winnings = won_bets.aggregate(Sum('actual_winnings'))['actual_winnings__sum'] or Decimal('0')
        active_bets = bets.filter(status='active').count()
        
        win_rate = (total_won / total_bets * 100) if total_bets > 0 else Decimal('0')
        
        data = {
            'total_bets': total_bets,
            'total_staked': total_staked,
            'total_won': total_won,
            'total_winnings': total_winnings,
            'win_rate': round(win_rate, 2),
            'active_bets': active_bets,
            'account_balance': user.account_balance
        }
        
        serializer = UserStatisticsSerializer(data)
        return Response(serializer.data)

   