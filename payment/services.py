# import requests
# from django.conf import settings
# from decimal import Decimal

# class PaystackService:
#     """Paystack payment integration"""
    
#     BASE_URL = "https://api.paystack.co"
    
#     def __init__(self):
#         self.secret_key = settings.PAYSTACK_SECRET_KEY
#         self.headers = {
#             'Authorization': f'Bearer {self.secret_key}',
#             'Content-Type': 'application/json'
#         }
    
#     def initialize_payment(self, email, amount, reference, callback_url=None):
#         """
#         Initialize a payment
        
#         Args:
#             email: User's email
#             amount: Amount in kobo (multiply by 100)
#             reference: Unique transaction reference
#             callback_url: URL to redirect after payment
        
#         Returns:
#             dict: Payment initialization response
#         """
#         url = f"{self.BASE_URL}/transaction/initialize"
        
#         # Convert amount to kobo (Paystack uses smallest currency unit)
#         amount_kobo = int(float(amount) * 100)
        
#         payload = {
#             'email': email,
#             'amount': amount_kobo,
#             'reference': reference,
#             'callback_url': callback_url or settings.PAYSTACK_CALLBACK_URL,
#             'currency': 'GHS',  # Ghana Cedis
#         }
        
#         response = requests.post(url, json=payload, headers=self.headers)
#         return response.json()
    
#     def verify_payment(self, reference):
#         """Verify a payment transaction"""
#         url = f"{self.BASE_URL}/transaction/verify/{reference}"
        
#         response = requests.get(url, headers=self.headers)
#         return response.json()
    
#     def create_transfer_recipient(self, account_number, bank_code, account_name):
#         """Create a transfer recipient for withdrawals"""
#         url = f"{self.BASE_URL}/transferrecipient"
        
#         payload = {
#             'type': 'nuban',
#             'name': account_name,
#             'account_number': account_number,
#             'bank_code': bank_code,
#             'currency': 'GHS'
#         }
        
#         response = requests.post(url, json=payload, headers=self.headers)
#         return response.json()
    
#     def initiate_transfer(self, recipient_code, amount, reference, reason='Withdrawal'):
#         """Initiate a transfer (withdrawal)"""
#         url = f"{self.BASE_URL}/transfer"
        
#         # Convert to kobo
#         amount_kobo = int(float(amount) * 100)
        
#         payload = {
#             'source': 'balance',
#             'reason': reason,
#             'amount': amount_kobo,
#             'recipient': recipient_code,
#             'reference': reference
#         }
        
#         response = requests.post(url, json=payload, headers=self.headers)
#         return response.json()
    
#     def get_banks(self):
#         """Get list of banks"""
#         url = f"{self.BASE_URL}/bank?country=ghana"
        
#         response = requests.get(url, headers=self.headers)
#         return response.json()


# class FlutterwaveService:
#     """Flutterwave payment integration"""
    
#     BASE_URL = "https://api.flutterwave.com/v3"
    
#     def __init__(self):
#         self.secret_key = settings.FLUTTERWAVE_SECRET_KEY
#         self.headers = {
#             'Authorization': f'Bearer {self.secret_key}',
#             'Content-Type': 'application/json'
#         }
    
#     def initialize_payment(self, email, amount, reference, phone_number=None):
#         """Initialize Flutterwave payment"""
#         url = f"{self.BASE_URL}/payments"
        
#         payload = {
#             'tx_ref': reference,
#             'amount': str(amount),
#             'currency': 'GHS',
#             'redirect_url': settings.PAYSTACK_CALLBACK_URL,  # Reuse callback
#             'payment_options': 'card,mobilemoneyghana',
#             'customer': {
#                 'email': email,
#                 'phonenumber': phone_number or '',
#             },
#             'customizations': {
#                 'title': 'NLA Betting',
#                 'description': 'Account Top-up',
#                 'logo': 'https://your-logo-url.com/logo.png'
#             }
#         }
        
#         response = requests.post(url, json=payload, headers=self.headers)
#         return response.json()
    
#     def verify_payment(self, transaction_id):
#         """Verify Flutterwave payment"""
#         url = f"{self.BASE_URL}/transactions/{transaction_id}/verify"
        
#         response = requests.get(url, headers=self.headers)
#         return response.json()

