from django.urls import path,include
from .views import (GameTypeViewSet,SubscriptionViewSet,NotificationViewSet)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register('game-types',GameTypeViewSet,basename='game-types')
router.register('subsscriptions',SubscriptionViewSet,basename='subscriptions')
router.register('notifications',NotificationViewSet,basename='notifications')

urlpatterns=[
    path('',include(router.urls)),
]