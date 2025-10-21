
from django.utils import timezone
from .models import Notification, UserSubscription, GameType

class NotificationService:
    @staticmethod
    def send_game_update_notification(game_type, title, message):
        """Send notification to all subscribers of a game type"""
        active_subscriptions = UserSubscription.objects.filter(
            game_type=game_type,
            is_active=True
        ).select_related('user')
        
        notifications = []
        for subscription in active_subscriptions:
            notification = Notification(
                user=subscription.user,
                game_type=game_type,
                notification_type='game_update',
                title=title,
                message=message,
                sent_at=timezone.now()
            )
            notifications.append(notification)
        
        # Bulk create for efficiency
        Notification.objects.bulk_create(notifications)
        
        return len(notifications)
    
    @staticmethod
    def send_draw_result_notification(draw, winning_numbers):
        """Send draw result notification to subscribers"""
        game_type = draw.game_type  # Assuming draw has game_type field
        title = f"Draw Results: {draw.name}"
        message = f"The winning numbers for {draw.name} are: {winning_numbers}"
        
        return NotificationService.send_game_update_notification(
            game_type, title, message
        )
    
    @staticmethod
    def send_personal_notification(user, title, message, game_type=None):
        """Send personal notification to a specific user"""
        notification = Notification.objects.create(
            user=user,
            game_type=game_type,
            notification_type='system',
            title=title,
            message=message,
            sent_at=timezone.now()
        )
        return notification