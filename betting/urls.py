from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    GameTypeViewSet, DrawViewSet, BetViewSet,
    SubscriptionViewSet, NotificationViewSet, StatisticsViewSet
)

router = DefaultRouter()
router.register(r'games-types', GameTypeViewSet, basename='game')
router.register(r'draws', DrawViewSet, basename='draw')
router.register(r'bets', BetViewSet, basename='bet')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'statistics', StatisticsViewSet, basename='statistics')

urlpatterns = [
    path('', include(router.urls)),
]