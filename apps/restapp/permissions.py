from rest_framework import permissions

from django.contrib.auth import get_user_model
User = get_user_model()


class ObjectOwner(permissions.BasePermission):

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated():
            return False
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.user == request.user


class IsProfileOwner(permissions.BasePermission):

    def has_permission(self, request, view):
        user = User.objects.get(pk=view.kwargs['id'])
        return False


class IsAnonCreate(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ["POST", "GET", "PUT", "DELETE"] and not request.user.is_authenticated():
            return True
        elif not request.user.is_authenticated() and request.method != "POST":
            return False
        elif request.method in permissions.SAFE_METHODS:
            return True

        return False

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated():
            return False
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj.username == request.user.username


class IsCashier(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in ["POST", "PUT", "GET"] and request.user.is_authenticated():
            return True
        elif request.method in permissions.SAFE_METHODS:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        root_cafe_owner = obj.root_cafe.owner
        print(root_cafe_owner.cafe_owner)
        print(obj)
        return True
