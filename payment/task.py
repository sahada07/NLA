# from celery import shared_task
# from .models import Transaction
# from .services import PaystackService
# from django.utils import timezone


# @shared_task
# def verify_pending_payments():
#     """Automatically verify pending payments"""
#     pending_transactions = Transaction.objects.filter(
#         status='pending',
#         payment_method='paystack'
#     )
    
#     paystack = PaystackService()
#     verified_count = 0
    
#     for transaction in pending_transactions:
#         try:
#             # Verify with Paystack
#             result = paystack.verify_payment(transaction.reference)
            
#             if result.get('status') and result['data']['status'] == 'success':
#                 # Payment successful
#                 transaction.status = 'success'
#                 transaction.gateway_response = result
#                 transaction.completed_at = timezone.now()
#                 transaction.save()
                
#                 # Credit user account
#                 transaction.user.account_balance += transaction.amount
#                 transaction.user.save()
                
#                 verified_count += 1
                
#                 # Send notification
#                 from betting.models import Notification
#                 Notification.objects.create(
#                     user=transaction.user,
#                     notification_type='system',
#                     title='Payment Successful',
#                     message=f'Your account has been credited with GH₵{transaction.amount}'
#                 )
#         except Exception as e:
#             print(f"Error verifying {transaction.reference}: {e}")
    
#     return f"Verified {verified_count} transaction(s)"


# @shared_task
# def process_withdrawal(transaction_id):
#     """Process a withdrawal request"""
#     try:
#         transaction = Transaction.objects.get(id=transaction_id)
        
#         if transaction.transaction_type != 'withdrawal':
#             return "Not a withdrawal transaction"
        
#         paystack = PaystackService()
        
#         # Create transfer recipient
#         recipient = paystack.create_transfer_recipient(
#             account_number=transaction.account_number,
#             bank_code=transaction.bank_name,  # Should be bank code
#             account_name=transaction.account_name
#         )
        
#         if recipient.get('status'):
#             recipient_code = recipient['data']['recipient_code']
            
#             # Initiate transfer
#             transfer = paystack.initiate_transfer(
#                 recipient_code=recipient_code,
#                 amount=transaction.amount,
#                 reference=transaction.reference,
#                 reason='Betting Withdrawal'
#             )
            
#             if transfer.get('status'):
#                 transaction.status = 'processing'
#                 transaction.gateway_reference = transfer['data']['reference']
#                 transaction.gateway_response = transfer
#                 transaction.save()
                
#                 return f"Withdrawal initiated: {transaction.reference}"
        
#         transaction.status = 'failed'
#         transaction.save()
#         return "Withdrawal failed"
        
#     except Transaction.DoesNotExist:
#         return "Transaction not found"