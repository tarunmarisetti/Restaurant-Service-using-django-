from rest_framework import serializers
from .models import MenuItem,CartItem
from .models import Order, OrderItem, MenuItem
from django.contrib.auth import get_user_model

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'inventory']


class CartItemSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='menuitem.title', read_only=True)

    class Meta:
        model = CartItem
        fields = ['id', 'menuitem', 'title', 'quantity', 'unit_price', 'price']
        read_only_fields = ['unit_price', 'price', 'title']

class AddCartItemSerializer(serializers.Serializer):
    menuitem_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1, default=1)

    def validate_menuitem_id(self, value):
        if not MenuItem.objects.filter(id=value).exists():
            raise serializers.ValidationError("Menu item not found.")
        return value


User = get_user_model()

class OrderItemSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='menuitem.title', read_only=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'menuitem', 'title', 'quantity', 'unit_price', 'price']
        read_only_fields = ['unit_price', 'price', 'title']

class OrderSerializer(serializers.ModelSerializer):
    order_items = OrderItemSerializer(many=True, read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    delivery_crew = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(groups__name='Delivery crew'),
        allow_null=True,
        required=False
    )

    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date', 'order_items']
        read_only_fields = ['user', 'total', 'date']