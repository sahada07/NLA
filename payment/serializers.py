# from rest_framework import serializers
# from django.core.validators import MinValueValidator
# from decimal import Decimal
# from .models import Transaction, PaymentMethod, Wallet
# from users.models import User

# class PaymentMethodSerializer(serializers.ModelSerializer):
#     """Serializer for payment methods"""
    
#     class Meta:
#         model = PaymentMethod
#         fields = [
#             'id', 'code', 'name', 'display_name', 'description',
#             'is_active', 'supports_deposit', 'supports_withdrawal',
#             'min_amount', 'max_amount', 'deposit_fee_percent', 
#             'deposit_fee_fixed', 'withdrawal_fee_percent', 'withdrawal_fee_fixed'
#         ]

# class InitiateDepositSerializer(serializers.Serializer):
#     """Serializer for initiating deposits"""
    
#     amount = serializers.DecimalField(
#         max_digits=10, 
#         decimal_places=2,
#         validators=[MinValueValidator(Decimal('0.01'))]
#     )
#     payment_method = serializers.CharField(max_length=50)
#     phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    
#     def validate(self, attrs):
#         amount = attrs['amount']
#         payment_method_code = attrs['payment_method']
        
#         # Validate payment method
#         try:
#             payment_method = PaymentMethod.objects.get(
#                 code=payment_method_code, 
#                 is_active=True,
#                 supports_deposit=True
#             )
#         except PaymentMethod.DoesNotExist:
#             raise serializers.ValidationError({
#                 'payment_method': 'Payment method not available for deposits'
#             })
        
#         # Validate amount limits
#         if amount < payment_method.min_amount:
#             raise serializers.ValidationError({
#                 'amount': f'Minimum deposit amount is GH₵{payment_method.min_amount}'
#             })
        
#         if amount > payment_method.max_amount:
#             raise serializers.ValidationError({
#                 'amount': f'Maximum deposit amount is GH₵{payment_method.max_amount}'
#             })
        
#         attrs['payment_method_obj'] = payment_method
#         return attrs

# class InitiateWithdrawalSerializer(serializers.Serializer):
#     """Serializer for initiating withdrawals"""
    
#     amount = serializers.DecimalField(
#         max_digits=10, 
#         decimal_places=2,
#         validators=[MinValueValidator(Decimal('0.01'))]
#     )
#     payment_method = serializers.CharField(max_length=50)
    
#     # Bank details (for bank transfers)
#     bank_name = serializers.CharField(required=False, allow_blank=True)
#     account_number = serializers.CharField(required=False, allow_blank=True)
#     account_name = serializers.CharField(required=False, allow_blank=True)
#     bank_code = serializers.CharField(required=False, allow_blank=True)
    
#     # Mobile money details
#     phone_number = serializers.CharField(required=False, allow_blank=True)
#     network = serializers.CharField(required=False, allow_blank=True)
    
#     def validate(self, attrs):
#         user = self.context['request'].user
#         amount = attrs['amount']
#         payment_method_code = attrs['payment_method']
        
#         # Check user balance
#         if user.account_balance < amount:
#             raise serializers.ValidationError({
#                 'amount': 'Insufficient balance for withdrawal'
#             })
        
#         # Validate payment method
#         try:
#             payment_method = PaymentMethod.objects.get(
#                 code=payment_method_code, 
#                 is_active=True,
#                 supports_withdrawal=True
#             )
#         except PaymentMethod.DoesNotExist:
#             raise serializers.ValidationError({
#                 'payment_method': 'Payment method not available for withdrawals'
#             })
        
#         # Validate amount limits
#         if amount < payment_method.min_amount:
#             raise serializers.ValidationError({
#                 'amount': f'Minimum withdrawal amount is GH₵{payment_method.min_amount}'
#             })
        
#         if amount > payment_method.max_amount:
#             raise serializers.ValidationError({
#                 'amount': f'Maximum withdrawal amount is GH₵{payment_method.max_amount}'
#             })
        
#         # Validate required fields based on payment method
#         if payment_method_code == 'bank_transfer':
#             if not all([attrs.get('bank_name'), attrs.get('account_number'), attrs.get('account_name')]):
#                 raise serializers.ValidationError({
#                     'bank_details': 'Bank name, account number, and account name are required for bank transfers'
#                 })
        
#         elif payment_method_code in ['mtn_momo', 'vodafone_cash', 'airtel_money']:
#             if not attrs.get('phone_number'):
#                 raise serializers.ValidationError({
#                     'phone_number': 'Phone number is required for mobile money withdrawals'
#                 })
        
#         attrs['payment_method_obj'] = payment_method
#         return attrs

# class TransactionSerializer(serializers.ModelSerializer):
#     """Serializer for transaction history"""
    
#     payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
#     status_display = serializers.CharField(source='get_status_display', read_only=True)
#     type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    
#     class Meta:
#         model = Transaction
#         fields = [
#             'id', 'reference', 'transaction_type', 'type_display',
#             'payment_method', 'payment_method_display',
#             'amount', 'fee', 'total_amount', 'currency',
#             'status', 'status_display',
#             'gateway_reference', 'description',
#             'created_at', 'updated_at', 'completed_at'
#         ]
#         read_only_fields = [
#             'id', 'reference', 'fee', 'total_amount', 'status',
#             'gateway_reference', 'created_at', 'updated_at', 'completed_at'
#         ]

# class WalletSerializer(serializers.ModelSerializer):
#     """Serializer for user wallet"""
    
#     user = serializers.StringRelatedField(read_only=True)
    
#     class Meta:
#         model = Wallet
#         fields = [
#             'user', 'account_balance', 'available_balance', 'locked_balance',
#             'total_deposited', 'total_withdrawn', 'total_won',
#             'updated_at'
#         ]
#         read_only_fields = ['user', 'updated_at']

# class VerifyTransactionSerializer(serializers.Serializer):
#     """Serializer for verifying transactions"""
    
#     reference = serializers.CharField(max_length=100)