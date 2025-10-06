
from rest_framework import permissions

class IsPlayer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'player'

class IsAgent(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'agent'

class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'admin'

class IsIdVerified(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.id_verified

class HasSufficientBalance(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ['POST', 'PUT']:
            # Check if user has sufficient balance for betting
            # This would be implemented based on specific betting logic
            return request.user.account_balance > 0
        return True