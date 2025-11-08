from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid
from django.utils import timezone

User = get_user_model()

class Wallet(models.Model):
    """Enhanced User wallet model with multiple wallet types."""
    
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wallets')
    balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    currency = models.CharField(max_length=3, default='GHS')
    
    # Security
    pin_hash = models.CharField(max_length=255, blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'wallets'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - GH₵{self.balance}"
    

    def can_debit(self, amount):
        """Check if wallet has sufficient available balance."""
        return self.available_balance >= Decimal(str(amount)) and self.status == 'active'
    
    @transaction.atomic
    def credit(self, amount, description="", reference="", transaction_type='credit'):
        """Add funds to wallet."""
        amount_decimal = Decimal(str(amount))
        old_balance = self.balance
        self.balance += amount_decimal
        self.save()
        
        # Create transaction record
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type=transaction_type,
            amount=amount_decimal,
            balance_before=old_balance,
            balance_after=self.balance,
            description=description,
            reference=reference
        )
        
        return self.balance
    
    @transaction.atomic
    def debit(self, amount, description="", reference="", transaction_type='debit'):
        """Remove funds from wallet."""
        if not self.can_debit(amount):
            raise ValueError("Insufficient balance or inactive wallet")
        
        amount_decimal = Decimal(str(amount))
        old_balance = self.balance
        self.balance -= amount_decimal
        self.save()
        
        # Create transaction record
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type=transaction_type,
            amount=amount_decimal,
            balance_before=old_balance,
            balance_after=self.balance,
            description=description,
            reference=reference
        )
        
        return self.balance
    
    def transfer_to(self, target_wallet, amount, description=""):
        """Transfer funds to another wallet."""
        if not isinstance(target_wallet, Wallet):
            raise ValueError("Target must be a Wallet instance")
        
        if self.user != target_wallet.user:
            raise ValueError("Can only transfer between own wallets")
        
        reference = f"TRF{timezone.now().strftime('%Y%m%d%H%M%S')}"
        
        with transaction.atomic():
            # Debit from source
            self.debit(
                amount, 
                reference=reference,
                transaction_type='transfer_out'
            )
            
            # Credit to target
            target_wallet.credit(
                amount,
                reference=reference,
                transaction_type='transfer_in'
            )
        
        return reference
    
class WalletTransaction(models.Model):
    """All wallet transactions"""
    
    TRANSACTION_TYPES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),

    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('reverse', 'Reverse'),
        ('cancelled', 'Cancelled'),
    ]
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Balances before and after transaction
    balance_before = models.DecimalField(max_digits=15, decimal_places=2)
    balance_after = models.DecimalField(max_digits=15, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=100, unique=True, db_index=True)
    
    # Payment details (for deposits/withdrawals)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    
    # Related objects
    bet = models.ForeignKey(
        'betting.Bet',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='wallet_transactions'
    )
    
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'wallet_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', 'transaction_type']),
            models.Index(fields=['reference']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.transaction_type} - GH₵{self.amount} - {self.wallet.user.username}"


class PaymentMethod(models.Model):
    """Available payment methods"""
    
    METHOD_TYPES = [
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('card', 'Card Payment'),
        ('cash', 'Cash'),
    ]
    
    PROVIDERS = [
        ('mtn', 'MTN Mobile Money'),
        ('vodafone', 'Vodafone Cash'),
        ('airteltigo', 'AirtelTigo Money'),
        ('bank', 'Bank Transfer'),
        ('visa', 'Visa Card'),
        ('mastercard', 'Mastercard'),
    ]
    
    name = models.CharField(max_length=100)
    method_type = models.CharField(max_length=20, choices=METHOD_TYPES)
    provider = models.CharField(max_length=50, choices=PROVIDERS)
    
    # Limits
    min_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('1.00'))
    max_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('10000.00'))
    min_withdrawal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('10.00'))
    max_withdrawal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('5000.00'))
    
    # Fees
    deposit_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    deposit_fee_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    withdrawal_fee_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    withdrawal_fee_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'payment_methods'
    
    def __str__(self):
        return f"{self.name} ({self.get_method_type_display()})"
    
    def calculate_deposit_fee(self, amount):
        """Calculate deposit fee"""
        percentage_fee = amount * (self.deposit_fee_percentage / 100)
        return percentage_fee + self.deposit_fee_fixed
    
    def calculate_withdrawal_fee(self, amount):
        """Calculate withdrawal fee"""
        percentage_fee = amount * (self.withdrawal_fee_percentage / 100)
        return percentage_fee + self.withdrawal_fee_fixed


class WithdrawalRequest(models.Model):
    """User withdrawal requests"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='withdrawal_requests')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    net_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT)
    
    # Recipient details
    account_name = models.CharField(max_length=200)
    account_number = models.CharField(max_length=100)
    bank_name = models.CharField(max_length=200, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=100, unique=True)
    
    # Related transaction
    transaction = models.OneToOneField(
        WalletTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='withdrawal_request'
    )
    
    # Admin notes
    admin_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'withdrawal_requests'
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"Withdrawal - GH₵{self.amount} - {self.wallet.user.username}"


def generate_transaction_reference():
    """Generate unique transaction reference"""
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    random_part = str(uuid.uuid4().hex)[:8].upper()
    return f"TXN{timestamp}{random_part}"


def generate_withdrawal_reference():
    """Generate unique withdrawal reference"""
    timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
    random_part = str(uuid.uuid4().hex)[:8].upper()
    return f"WD{timestamp}{random_part}"