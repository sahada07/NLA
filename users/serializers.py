
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, UserProfile
from django.utils import timezone

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    date_of_birth = serializers.DateField(required=True)
    region = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'password_confirm', 
                 'first_name', 'last_name','id_type','id_number','region','date_of_birth', 'phone_number', 'user_type')
    
    

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        
        from datetime import date

        # Age verification (18+ for betting)
        # age = (date.today() - attrs['date_of_birth']).days // 365
        date_of_birth =attrs['date_of_birth']
        today=date.today()
        age= today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day)) 
        
        if age < 18:
            raise serializers.ValidationError({"date_of_birth": "You must be 18 years or older to register."})
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        date_of_birth= validated_data.pop('date_of_birth')
        phone_number= validated_data.pop('phone_number')
        user_type= validated_data.pop('user_type','player')
        id_type= validated_data.pop('id_type','ghana-card')
        id_number = validated_data.pop('id_number','000-0000-0000-0')
        region=validated_data.pop('region','Greater Accra-Accra')
        user = User.objects.create_user(**validated_data)

        user.date_of_birth=date_of_birth
        user.phone_number=phone_number
        user.user_type=user_type
        user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            
            # Check if account is locked
            # profile = user.profile
            # if profile.account_locked_until and profile.account_locked_until > timezone.now():
            #     raise serializers.ValidationError('Account temporarily locked due to too many failed attempts')
                
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include "username" and "password"')

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name','id_type','id_number',
                  'region','date_of_birth', 'phone_number', 'user_type', 'account_balance')

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is not correct")
        return value