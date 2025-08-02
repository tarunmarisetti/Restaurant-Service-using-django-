from django.urls import path
from .import views

urlpatterns=[
    path('menu-items', views.MenuItemsView.as_view()),                 # /api/menu-items
    path('menu-items/<int:pk>', views.SingleMenuItemView.as_view()), 
    path('groups/manager/users', views.ManagerGroupView.as_view()),                 # GET & POST
    path('groups/manager/users/<int:user_id>', views.ManagerGroupView.as_view()),   # DELETE
    path('groups/delivery-crew/users', views.DeliveryCrewGroupView.as_view()),      # GET & POST
    path('groups/delivery-crew/users/<int:user_id>', views.DeliveryCrewGroupView.as_view()),  # DELETE
    path('cart/menu-items', views.CartView.as_view()),
    path('orders', views.OrdersView.as_view()),            
    path('orders/<int:pk>', views.SingleOrderView.as_view()),
]