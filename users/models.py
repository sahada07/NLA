from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver





class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('player', 'Player'),
        ('agent', 'Agent'),
        ('admin', 'Administrator'),
    )

    ID_TYPE_CHOICES=(
        ('ghana_card','Ghana Card'),
        ('voters_id','Voters Id')

    )

    REGION_CHOICES=(
        ('Greater Accra-Accra','Greater Accra-Accra'),
        ('Ashanti Region','Ashanti Region - Kumasi'),
        ('Western Region','Western Region - Sekondi-Takoradi'),
        ('Eastern Region','Eastern Region - Koforidua'),
        ('Central Region','Central Region - Cape Coast'),
        ('Northern Region','Northern Region - Tamale'),
        ('Upper East Region','Upper East Region - Bolgatanga'),
        ('Upper West Region','Upper West Region - Wa'),
        ('Bono Region','Bono Region - Sunyani'),
        ('Bono East Region','Bono East Region - Techiman'),
        ('Ahafo Region','Ahafo Region - Goaso'),
        ('Western North','Western North Region - Sefwi Wiawso'),
        ('Oti Region','Oti Region - Dambai'),
        ('Volta Region','Volta Region - Ho'),
        ('North East Region','North East Region - Nalerigu'),
        ('Savannah Regio','Savannah Region - Damango'),
    )

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='player')
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    id_type=models.CharField(max_length=20, choices=ID_TYPE_CHOICES,default='ghana_card')
    id_number=models.CharField(max_length=30, default='000-0000-0000-0')
    region=models.CharField(max_length=20, choices=REGION_CHOICES,default='Greater Accra-Accra')
    id_verified = models.BooleanField(default=False)
    account_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    security_question = models.CharField(max_length=255)
    security_answer = models.CharField(max_length=255)
    failed_login_attempts = models.IntegerField(default=0)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.username} Profile"


# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created,**kwargs):
#     if created:
#         UserProfile.objects.create(user=instance)

        # Signal to create user profile automatically


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance,'profile'):
     instance.profile.save()
