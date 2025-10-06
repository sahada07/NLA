from django.urls import path
from rest_framework_simplejwt.views import (TokenRefreshView,TokenObtainPairView)
from .views import(UserRegistrationView,UserLoginView,
                   UserProfileView,ChangePasswordView,LogoutView)



urlpatterns=[
    path('register/',UserRegistrationView.as_view(), name='register'),
    path('login/',UserLoginView.as_view(), name='login'),
#   path('api/auth/login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/',TokenRefreshView.as_view(), name='token'),
    path('profile/',UserProfileView.as_view(), name='profile'),
    path('change-password/',ChangePasswordView.as_view(), name='change-password'),
    path('logout/',LogoutView.as_view(), name='logout'),
]
  