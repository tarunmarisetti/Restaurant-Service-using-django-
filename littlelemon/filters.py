import django_filters
from .models import MenuItem, Order

class MenuItemFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    min_inventory = django_filters.NumberFilter(field_name='inventory', lookup_expr='gte')
    max_inventory = django_filters.NumberFilter(field_name='inventory', lookup_expr='lte')

    class Meta:
        model = MenuItem
        fields = ['title', 'min_price', 'max_price', 'min_inventory', 'max_inventory']

class OrderFilter(django_filters.FilterSet):
    date_after  = django_filters.IsoDateTimeFilter(field_name='date', lookup_expr='gte')
    date_before = django_filters.IsoDateTimeFilter(field_name='date', lookup_expr='lte')
    status      = django_filters.NumberFilter(field_name='status')  # 0 or 1
    user        = django_filters.NumberFilter(field_name='user__id')
    delivery_crew = django_filters.NumberFilter(field_name='delivery_crew__id')

    class Meta:
        model = Order
        fields = ['status', 'user', 'delivery_crew', 'date_after', 'date_before']
