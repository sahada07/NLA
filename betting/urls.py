from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GameTypeViewSet, DrawViewSet, BetViewSet,
    SubscriptionViewSet, NotificationViewSet, StatisticsViewSet
)
# from betting.views import debug_bets_view


router = DefaultRouter()
router.register(r'games-types', GameTypeViewSet, basename='game')
router.register(r'draws', DrawViewSet, basename='draw')
router.register(r'bets', BetViewSet, basename='bet')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'statistics', StatisticsViewSet, basename='statistics')

urlpatterns = [
    path('', include(router.urls)),
    # path('debug/bets/', debug_bets_view, name='debug-bets'),
    # path('test-bet/',test_bet_endpoint, name='test-bet')
]