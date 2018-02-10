from rest_framework import permissions


# Permission to limit api object edit to its owner. 
class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user


# Permission to limit api objet edit to the bot user.
class IsBot(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.bot == request.user
