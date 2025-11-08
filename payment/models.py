# from django.db import models
# from django.utils import timezone
# from decimal import Decimal
# from users.models import User
# import uuid
# from django.utils import timezone
# from django.core.validators import MinValueValidator






# class Transaction(models.Model):
#     """Payment transactions """
    
#     TRANSACTION_TYPES = [
#         ('deposit', 'Deposit'),
#         ('withdrawal', 'Withdrawal'),
#         ('refund', 'Refund'),
#         ('bet_placement', 'Bet Placement'),
#         ('bet_winnings', 'Bet Winnings'),   
#         ('commission', 'Agent Commission'),  
#     ]
    
#     STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('initiated', 'Initiating'),  
#         ('processing', 'Processing'),
#         ('success', 'Success'),
#         ('failed', 'Failed'),
#         ('cancelled', 'Cancelled'),
#         ('refunded', 'Refunded'),  
#     ]
    
#     PAYMENT_METHODS = [
#         ('paystack', 'Paystack'),
#         ('flutterwave', 'Flutterwave'),
#         ('bank_transfer', 'Bank Transfer'),
#         ('mobile_money', 'Mobile Money'),
#         ('mtn_momo', 'MTN Mobile Money'),     
#         ('vodafone_cash', 'Vodafone Cash'),   
#         ('airtel_money', 'Airtel Money'),     
#     ]
    
#     CURRENCIES = [
#         ('GHS', 'Ghana Cedi'),
#         ('USD', 'US Dollar'),
#     ]
    
#     # Core relationships
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
#     reference = models.CharField(max_length=100, unique=True, editable=False)  # Made non-editable
    
#     # Transaction details
#     transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
#     payment_method = models.CharField(max_length=50, choices=PAYMENT_METHODS)
    
#     # Financial details
#     amount = models.DecimalField(
#         max_digits=10, 
#         decimal_places=2,
#         validators=[MinValueValidator(Decimal('0.01'))]  # Added validator
#     )
#     fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2, editable=False)  # Auto-calculated
#     currency = models.CharField(max_length=3, choices=CURRENCIES, default='GHS')
    
#     # Balance tracking (important for financial audit)
#     balance_before = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
#     balance_after = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
#     # Status and timestamps
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     completed_at = models.DateTimeField(null=True, blank=True)
    
#     # Payment gateway details
#     gateway_reference = models.CharField(max_length=200, blank=True)
#     gateway_response = models.JSONField(null=True, blank=True)
#     gateway_url = models.URLField(blank=True)  # Payment URL for redirects
    
#     # Banking details (for withdrawals)
#     bank_name = models.CharField(max_length=100, blank=True)
#     account_number = models.CharField(max_length=50, blank=True)
#     account_name = models.CharField(max_length=200, blank=True)
#     bank_code = models.CharField(max_length=20, blank=True)  # For Paystack integration
    
#     # Phone number (for mobile money)
#     phone_number = models.CharField(max_length=20, blank=True)
#     network = models.CharField(max_length=20, blank=True) 
    
#     # Related objects (for betting context)
#     bet = models.ForeignKey(
#         'betting.Bet',  # Reference to your Bet model
#         on_delete=models.SET_NULL,
#         null=True,
#         blank=True,
#         related_name='transactions'
#     )
    
#     # Metadata
#     description = models.TextField(blank=True)
#     metadata = models.JSONField(null=True, blank=True)  # For additional data
#     ip_address = models.GenericIPAddressField(null=True, blank=True)  # For security
    
#     # Admin
#     is_test = models.BooleanField(default=False)  # Test transactions
    
#     class Meta:
#         db_table = 'transactions'
#         ordering = ['-created_at']
#         indexes = [
#             models.Index(fields=['user', 'status']),
#             models.Index(fields=['reference']),
#             models.Index(fields=['gateway_reference']),
#             models.Index(fields=['created_at']),
#         ]
    
#     def __str__(self):
#         return f"{self.reference} - {self.user.username} - GH₵{self.amount}"
    
#     def save(self, *args, **kwargs):
#         # Generate reference if not set
#         if not self.reference:
#             self.reference = self.generate_reference()
        
#         # Calculate total amount
#         self.calculate_total_amount()
        
#         # Set balance fields on creation
#         if not self.pk and not self.balance_before:
#             self.balance_before = self.user.account_balance
        
#         super().save(*args, **kwargs)
    
#     def generate_reference(self):
#         """Generate unique transaction reference"""
#         timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
#         random_str = str(uuid.uuid4())[:8].upper()
#         return f"TXN{timestamp}{random_str}"
    
#     def calculate_total_amount(self):
#         """Calculate total amount including fees"""
#         if self.transaction_type in ['deposit', 'withdrawal']:
#             if self.transaction_type == 'deposit':
#                 # For deposits, user pays amount + fees
#                 self.total_amount = self.amount + self.fee
#             else:  # withdrawal
#                 # For withdrawals, user receives amount - fees
#                 self.total_amount = self.amount - self.fee
#         else:
#             # For other transactions, total is just the amount
#             self.total_amount = self.amount
    
#     def mark_success(self):
#         """Mark transaction as successful and update user balance"""
#         if self.status != 'success':
#             self.status = 'success'
#             self.completed_at = timezone.now()
            
#             # Update user balance based on transaction type
#             if self.transaction_type == 'deposit':
#                 self.user.account_balance += self.amount
#             elif self.transaction_type == 'withdrawal':
#                 self.user.account_balance -= self.total_amount  # Amount + fees
#             elif self.transaction_type == 'bet_winnings':
#                 self.user.account_balance += self.amount
            
#             self.balance_after = self.user.account_balance
#             self.user.save()
#             self.save()
    
#     def mark_failed(self, reason=""):
#         """Mark transaction as failed"""
#         self.status = 'failed'
#         self.balance_after = self.balance_before  # Balance remains unchanged
#         self.description = f"{self.description} - Failed: {reason}".strip()
#         self.save()
    
#     def get_absolute_url(self):
#         return f"/api/transactions/{self.reference}/"
    
#     # @property decorators ,a python class that turns inside fuction into a read-only

#     @property
#     def is_deposit(self):
#         return self.transaction_type == 'deposit'
    
#     @property
#     def is_withdrawal(self):
#         return self.transaction_type == 'withdrawal'
    
#     @property
#     def can_be_cancelled(self):
#         """Check if transaction can be cancelled"""
#         return self.status in ['pending', 'initiated']
    
#     class Wallet(models.Model):
#      """User wallet for balance management"""
    
#     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    
#     # Balances
#     account_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
#     available_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
#     locked_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)  # For active bets
    
#     # Statistics
#     total_deposited = models.DecimalField(max_digits=15, decimal_places=2, default=0)
#     total_withdrawn = models.DecimalField(max_digits=15, decimal_places=2, default=0)
#     total_won = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         db_table = 'wallets'
    
#     def __str__(self):
#         return f"{self.user.username} - GH₵{self.available_balance}"
    
#     def update_balances(self):
#         """Update available balance"""
#         self.available_balance = self.account_balance - self.locked_balance
#         self.save()
    
#     def can_afford(self, amount):
#         """Check if user can afford an amount"""
#         return self.available_balance >= amount


#     class PaymentMethod(models.Model):
#      """Available payment methods configuration"""
    
#     name = models.CharField(max_length=50)
#     code = models.CharField(max_length=20, unique=True)
#     display_name = models.CharField(max_length=100)
#     description = models.TextField()
    
#     # Configuration
#     is_active = models.BooleanField(default=True)
#     supports_deposit = models.BooleanField(default=True)
#     supports_withdrawal = models.BooleanField(default=False)
    
#     # Limits
#     min_amount = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
#     max_amount = models.DecimalField(max_digits=10, decimal_places=2, default=5000.00)
    
#     # Fees
#     deposit_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
#     deposit_fee_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     withdrawal_fee_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
#     withdrawal_fee_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         db_table = 'payment_methods'
    
#     def __str__(self):
#         return self.display_name
    
#     def calculate_fee(self, amount, transaction_type):
#         """Calculate fee for transaction"""
#         if transaction_type == 'deposit':
#             fee = (amount * self.deposit_fee_percent / 100) + self.deposit_fee_fixed
#         else:  # withdrawal
#             fee = (amount * self.withdrawal_fee_percent / 100) + self.withdrawal_fee_fixed
        
#         return max(fee, Decimal('0.00'))    


