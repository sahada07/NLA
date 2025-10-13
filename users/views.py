# users/views.py
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.contrib.auth import login
from .models import User, UserProfile
from .serializers import (UserRegistrationSerializer, UserLoginSerializer, 
                         UserProfileSerializer, ChangePasswordSerializer)
from rest_framework.permissions import IsAuthenticated
# from pymongo import MongoClient
# from datetime import timedelta

class UserRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'auth'
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()

             # Profile is auto-created by signal, but we can ensure it exists
            # if not hasattr(user, 'profile'):
            #     UserProfile.objects.create(user=user)
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'User registered successfully',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = 'auth'
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Reset failed attempts on successful login
            profile = user.profile
            profile.failed_login_attempts = 0
            profile.account_locked_until = None
            profile.save()
            
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'Login successful',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
        
        # Increment failed login attempts
        username = request.data.get('username')
        try:
            user = User.objects.get(username=username)
            profile = user.profile
            profile.failed_login_attempts += 1
            
            # Lock account after 5 failed attempts for 30 minutes
            if profile.failed_login_attempts >= 5:
                profile.account_locked_until = timezone.now() + timezone.timedelta(minutes=30)
                profile.save()
                return Response({
                    'error': 'Account temporarily locked due to too many failed attempts. Try again in 30 minutes.'
                }, status=status.HTTP_423_LOCKED)
                
            profile.save()
        except User.DoesNotExist:
            pass
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({'message': 'Password updated successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdateProfileView(APIView):
    permission_classes=[IsAuthenticated]

    def put (self,request):
        serializer=UserProfileSerializer(request.user,data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
             

class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logout successful'}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            print("logout error:",e)
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)
        

        
# client = MongoClient('mongodb+srv://<username>:<password>@<atlas cluster>/<myFirstDatabase>?retryWrites=true&w=majority')
# db = client['sample_medicines']
# collection = db['medicinedetails']
# # Perform CRUD operations
# collection.insert_one({"medicine_id": "RR000123456", "common_name": "Paracetamol"})