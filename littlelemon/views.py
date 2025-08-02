# Django & third-party
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, status
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied

from .models import (
    MenuItem,
    CartItem,
    Order,
    OrderItem,
)
from .serializers import (
    MenuItemSerializer,
    CartItemSerializer,
    AddCartItemSerializer,
    OrderSerializer,
)
from .permissions import (
    IsManager,
    IsCustomer,
    IsDeliveryCrew,
)
from .pagination import DefaultPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from .pagination import DefaultPagination
from .filters import MenuItemFilter, OrderFilter
from rest_framework.throttling import ScopedRateThrottle

class MenuItemsView(APIView):
    # throttle scope based
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'menu'
    # filtering and sorting
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_class = MenuItemFilter
    search_fields = ['title']                         # /api/menu-items?search=margh
    ordering_fields = ['price', 'title', 'inventory'] # /api/menu-items?ordering=-price,title
    ordering = ['title']

    def get_permissions(self):
        if self.request.method in ['POST']:
            return [permissions.IsAuthenticated(), IsManager()]
        return [permissions.IsAuthenticated()]  # Customer & Delivery crew can GET

    def get(self, request):
        items = MenuItem.objects.all()
        serializer = MenuItemSerializer(items, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = MenuItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SingleMenuItemView(APIView):
    # throttle scope based
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'menu'

    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated(), IsManager()]
        return [permissions.IsAuthenticated()]  # All authenticated users can GET

    def get(self, request, pk):
        try:
            item = MenuItem.objects.get(pk=pk)
        except MenuItem.DoesNotExist:
            return Response({'error': 'Item Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = MenuItemSerializer(item)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        try:
            item = MenuItem.objects.get(pk=pk)
        except MenuItem.DoesNotExist:
            return Response({'error': 'Item Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = MenuItemSerializer(item, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        try:
            item = MenuItem.objects.get(pk=pk)
        except MenuItem.DoesNotExist:
            return Response({'error': 'Item Not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = MenuItemSerializer(item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        try:
            item = MenuItem.objects.get(pk=pk)
        except MenuItem.DoesNotExist:
            return Response({'error': 'Item Not found'}, status=status.HTTP_404_NOT_FOUND)
        item.delete()
        return Response(status=status.HTTP_200_OK)


User = get_user_model()

class ManagerGroupView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        group = Group.objects.get(name="Manager")
        users = group.user_set.all()
        data = [{"id": u.id, "name": u.name, "email": u.email} for u in users]
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        user_id = request.data.get("user_id")
        user = get_object_or_404(User, id=user_id)
        group = Group.objects.get(name="Manager")
        group.user_set.add(user)
        return Response({"message": "User added to Manager group"}, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        group = Group.objects.get(name="Manager")
        group.user_set.remove(user)
        return Response({"message": "User removed from Manager group"}, status=status.HTTP_200_OK)


class DeliveryCrewGroupView(APIView):
    permission_classes = [IsManager]

    def get(self, request):
        group = Group.objects.get(name="Delivery crew")
        users = group.user_set.all()
        data = [{"id": u.id, "name": u.name, "email": u.email} for u in users]
        return Response(data, status=status.HTTP_200_OK)

    def post(self, request):
        user_id = request.data.get("user_id")
        user = get_object_or_404(User, id=user_id)
        group = Group.objects.get(name="Delivery crew")
        group.user_set.add(user)
        return Response({"message": "User added to Delivery crew group"}, status=status.HTTP_201_CREATED)

    def delete(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        group = Group.objects.get(name="Delivery crew")
        group.user_set.remove(user)
        return Response({"message": "User removed from Delivery crew group"}, status=status.HTTP_200_OK)
    

class CartView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'cart'

    permission_classes = [permissions.IsAuthenticated, IsCustomer]

    # GET /api/cart/menu-items  -> current user's cart
    def get(self, request):
        items = CartItem.objects.filter(user=request.user).select_related('menuitem')
        data = CartItemSerializer(items, many=True).data
        return Response(data, status=status.HTTP_200_OK)

    # POST /api/cart/menu-items  -> add (or increase) an item
    # Body: { "menuitem_id": <int>, "quantity": <int> }
    @transaction.atomic
    def post(self, request):
        serializer = AddCartItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        menuitem = get_object_or_404(MenuItem, id=serializer.validated_data['menuitem_id'])
        qty = serializer.validated_data.get('quantity', 1)

        # unit_price from menu item price
        unit_price = menuitem.price

        # upsert: add or increase quantity
        cart_item, created = CartItem.objects.select_for_update().get_or_create(
            user=request.user, menuitem=menuitem,
            defaults={'quantity': qty, 'unit_price': unit_price, 'price': unit_price * qty}
        )
        if not created:
            cart_item.quantity += qty
            cart_item.unit_price = unit_price
            cart_item.price = unit_price * cart_item.quantity
            cart_item.save()

        return Response(CartItemSerializer(cart_item).data, status=status.HTTP_201_CREATED)

    # DELETE /api/cart/menu-items  -> clear current user's cart
    def delete(self, request):
        CartItem.objects.filter(user=request.user).delete()
        return Response({'message': 'Cart cleared'}, status=status.HTTP_200_OK)
    

class OrdersView(generics.ListCreateAPIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'orders'
    serializer_class = OrderSerializer
    pagination_class = DefaultPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['status', 'user', 'delivery_crew']
    ordering_fields = ['date', 'total', 'status']
    ordering = ['-date']

    def get_queryset(self):
        u = self.request.user
        if u.groups.filter(name='Manager').exists():
            return Order.objects.all().prefetch_related('order_items__menuitem')
        if u.groups.filter(name='Delivery crew').exists():
            return Order.objects.filter(delivery_crew=u).prefetch_related('order_items__menuitem')
        # Customer
        return Order.objects.filter(user=u).prefetch_related('order_items__menuitem')

    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated(), IsCustomer()]
        return [permissions.IsAuthenticated()]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        # Create order from current user's cart, then clear cart
        cart_items = CartItem.objects.select_for_update().filter(user=request.user).select_related('menuitem')
        if not cart_items.exists():
            return Response({'detail': 'Cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(user=request.user, status=0, total=0)
        total = 0
        bulk = []
        for ci in cart_items:
            unit = ci.unit_price
            line_total = ci.price
            total += line_total
            bulk.append(OrderItem(order=order, menuitem=ci.menuitem, quantity=ci.quantity, unit_price=unit, price=line_total))
        OrderItem.objects.bulk_create(bulk)
        order.total = total
        order.save()

        cart_items.delete()

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class SingleOrderView(generics.RetrieveUpdateDestroyAPIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'orders'
    
    queryset = Order.objects.all().prefetch_related('order_items__menuitem')
    serializer_class = OrderSerializer

    def get_permissions(self):
        method = self.request.method
        u = self.request.user
        # Manager: full control
        if u.groups.filter(name='Manager').exists():
            if method in ['DELETE', 'PUT', 'PATCH', 'GET']:
                return [permissions.IsAuthenticated(), IsManager()]
        # Delivery crew: can view assigned orders, and PATCH status only
        if u.groups.filter(name='Delivery crew').exists():
            if method in ['GET', 'PATCH']:
                return [permissions.IsAuthenticated(), IsDeliveryCrew()]
            return [permissions.IsAuthenticated()]  # will 403 on forbidden
        # Customer: can view their own order only
        if method == 'GET':
            return [permissions.IsAuthenticated(), IsCustomer()]
        return [permissions.IsAuthenticated()]  # will 403 later
       
    def get_object(self):
        obj = get_object_or_404(Order, pk=self.kwargs['pk'])
        u = self.request.user

        # Access control: Customer only own, Delivery crew only assigned
        if u.groups.filter(name='Manager').exists():
            return obj
        if u.groups.filter(name='Delivery crew').exists():
            if obj.delivery_crew_id == u.id:
                return obj
            raise PermissionDenied('Forbidden.')
        # Customer
        if obj.user_id != u.id:
            raise PermissionDenied('Forbidden.')
        return obj

    def put(self, request, *args, **kwargs):
        # Manager: can set delivery_crew and status (0/1)
        if not request.user.groups.filter(name='Manager').exists():
            return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
        partial = False
        return self._update_manager(request, partial)

    def patch(self, request, *args, **kwargs):
        u = request.user
        # Manager full patch, Delivery crew status-only
        if u.groups.filter(name='Manager').exists():
            partial = True
            return self._update_manager(request, partial)
        if u.groups.filter(name='Delivery crew').exists():
            order = self.get_object()
            status_val = request.data.get('status', None)
            if status_val not in [0, 1, '0', '1']:
                return Response({'status': ['Must be 0 or 1.']}, status=status.HTTP_400_BAD_REQUEST)
            order.status = int(status_val)
            order.save()
            return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)
        return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

    def _update_manager(self, request, partial):
        order = self.get_object()
        data = request.data.copy()

        # Only allow manager to update: delivery_crew, status
        allowed = {}
        if 'delivery_crew' in data:
            allowed['delivery_crew'] = data.get('delivery_crew')
        if 'status' in data:
            status_val = data.get('status')
            if status_val not in [0, 1, '0', '1']:
                return Response({'status': ['Must be 0 or 1.']}, status=status.HTTP_400_BAD_REQUEST)
            allowed['status'] = int(status_val)

        serializer = OrderSerializer(order, data=allowed, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, *args, **kwargs):
        # Manager only
        if not request.user.groups.filter(name='Manager').exists():
            return Response({'detail': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)
        order = self.get_object()
        order.delete()
        return Response(status=status.HTTP_200_OK)