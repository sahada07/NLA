# betting/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import permission_classes
from users.permissions import IsPlayer, IsIdVerified, HasSufficientBalance

class PlaceBetView(APIView):
    permission_classes = [IsPlayer, IsIdVerified, HasSufficientBalance]
    throttle_scope = 'betting'
    
    def post(self, request):
        # Example betting logic
        bet_data = request.data
        
        # Validate bet data
        serializer = BetSerializer(data=bet_data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Process the bet
        try:
            bet = serializer.save(user=request.user)
            return Response({
                'bet_id': bet.id,
                'status': 'success',
                'message': 'Bet placed successfully'
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)