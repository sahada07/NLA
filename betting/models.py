
from django.db import models
from users.models import User

class GameType(models.Model):
    GAME_CHOICES = [
        ('NLA 5/90','NLA 5/90'),
        ('Monday Special', 'Monday Special'),
        ('Lucky Tuesday', 'Lucky Tuesday'),
        ('Midweek', 'Midweek'),
        ('Fortune Thursday', 'Fortune Thursday'),
        ('Friday Bonanza', 'Friday Bonanza'),
        ('National Weekly', 'National Weekly'),
        ('Sunday Aseda', 'Sunday Aseda'),
        
        ('VAG Games','VAG Games'),
        ('VAG Monday', 'VAG Monday'),
        ('VAG Tuesday', 'VAG Tuesday'),
        ('VAG Wednesday', 'VAG Wednesday'),
        ('VAG Thursday', 'VAG Thursday'),
        ('VAG Friday', 'VAG Friday'),
        ('VAG Saturdayy', 'VAG Saturdayy'),
        ('VAG Sunday', 'VAG Sunday'),

        ('Noon Rush','Noon Rush'),
        ('Noon Monday', 'Noon Monday'),
        ('Noon Tuesday', 'Noon Tuesday'),
        ('Noon Wednesday', 'Noon Wednesday'),
        ('Noon Thursday', 'Noon Thursday'),
        ('Noon Friday', 'Noon Friday'),
        ('Noon Saturday', 'Noon Saturday'),

        ('Quick 5,11','Quick 5/11')
    ]
    
    name = models.CharField(max_length=100,choices=GAME_CHOICES)
    code = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=100,
    choices=[
        ('nla 5/90','NLA 5/90'),
        ('vag games','VAG Games'),
        ('noon rush','Noon Rush'),
        ('other games','Other Games'),
    ],
     default='nla 5/90'
     ) 

    description = models.TextField()
    is_active = models.BooleanField(default=True) 
    notification_frequency = models.CharField(
        max_length=20,
        choices=[
            ('instant', 'Instant'),
            ('daily', 'Daily Digest'),
            ('weekly', 'Weekly Digest')
        ],
        default='instant'
    )
    
    class Meta:
        db_table= 'game_types'
    
    def __str__(self):
        return self.name

class UserSubscription(models.Model):
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='subscriptions'
    )
    game_type = models.ForeignKey(
        GameType, 
        on_delete=models.CASCADE,
        related_name='subscribers'
    )
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribe_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'user_subscriptions'
        unique_together = ['user', 'game_type']
    
    def __str__(self):
        return f"{self.user.username} - {self.game_type.name}"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('game_update', 'Game Update'),
        ('draw_result', 'Draw Result'),
        ('new_game', 'New Game'),
        ('promotion', 'Promotion'),
        ('system', 'System Alert'),
    )
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    game_type = models.ForeignKey(
        GameType, 
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    notification_type = models.CharField(
        max_length=20, 
        choices=NOTIFICATION_TYPES
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"