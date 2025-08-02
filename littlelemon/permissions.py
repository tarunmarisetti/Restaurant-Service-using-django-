from rest_framework.permissions import BasePermission

class IsManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name='Manager').exists()

class IsCustomer(BasePermission):
    """
    Customer = authenticated user NOT in Manager or Delivery crew groups.
    """
    def has_permission(self, request, view):
        u = request.user
        if not u.is_authenticated:
            return False
        in_manager = u.groups.filter(name='Manager').exists()
        in_delivery = u.groups.filter(name='Delivery crew').exists()
        return not (in_manager or in_delivery)
    
class IsDeliveryCrew(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name='Delivery crew').exists()