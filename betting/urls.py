from django.urls import path,include
from .views import (GameTypeViewSet,SubscriptionViewSet,NotificationViewSet,
                    DrawViewSet,BetViewSet,StatisticsViewSet)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register('types/',GameTypeViewSet,basename='game-types')
router.register(r'draws',DrawViewSet,basename='draw')
router.register(r'bets',BetViewSet,basename='bet')
router.register(r'subscriptions',SubscriptionViewSet,basename='subscriptions')
router.register(r'notifications',NotificationViewSet,basename='notifications')
router.register(r'statistics',StatisticsViewSet,basename='statistic')

urlpatterns=[
    path('',include(router.urls)),
]