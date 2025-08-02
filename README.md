Restaurant Service (Django + DRF + Djoser)
A role-based REST API for Little Lemon restaurant. Supports user registration/login, menu management, carts, orders, and delivery workflow — with filtering, sorting, pagination, and throttling.

Features
Auth & Users

Registration & login via Djoser with TokenAuthentication

Current user endpoint

Custom user model (email as login)

Roles (Django Groups)

Manager – full control of menu, orders, and group assignments

Delivery crew – see assigned orders, update status

Customer – browse menu, manage cart, place orders

Menu

CRUD (create/update/delete restricted to Managers)

Filtering, search, sorting, pagination

Cart

Per-customer cart; add items, list, clear

Orders

Customer creates order from cart

Manager assigns delivery crew & updates status

Delivery crew updates status only

Filtering, sorting, pagination

Throttling

Different rates for anonymous vs authenticated users

Optional per-endpoint scopes

Tech Stack
Python, Django, Django REST Framework

Djoser (auth), django-filter

SQLite (dev)


Environment / Defaults
Admin: /admin/

Base API: /api/

Auth: Token (Djoser)

Current user: /api/users/me/ (also exposed as /api/users/users/me/ if you registered the router)


Authentication (Djoser + Token)
Register

POST /api/users/
{
  "name": "Jane",
  "email": "jane@example.com",
  "password": "pass123",
}


Roles & Access
Create two Groups in /admin/ → Groups:

Manager

Delivery crew

Assign users to groups. Unassigned users are Customers.

Permissions (summary):

Customers: view menu, manage own cart, create order, view own orders

Managers: full menu CRUD, view all orders, assign delivery crew, update status, delete orders, manage groups

Delivery crew: view assigned orders, PATCH status only


Endpoints
Users (Djoser)
Method	Endpoint	Role	Purpose
POST	/api/users/	No role	Register user (name, email, password)
GET	/api/users/me/	Any authenticated	Current user
POST	/api/token/login/	Valid email/password	Get auth token
POST	/api/token/logout/	Authenticated	Revoke token

Menu Items
Method	Endpoint	Role	Purpose
GET	/api/menu-items	Customer, Delivery, Manager	List items (filter/search/sort/paginate)
POST	/api/menu-items	Manager only	Create (201)
GET	/api/menu-items/{id}	Customer, Delivery, Manager	Retrieve
PUT/PATCH/DELETE	/api/menu-items/{id}	Manager only	Update/Delete

Filtering / Searching / Sorting / Pagination
Filter: ?min_price=&max_price=&min_inventory=&max_inventory=&title=

Search: ?search=pizza

Sort: ?ordering=price (prefix - for desc, chain e.g. ?ordering=-price,title)

Pagination: ?page=2&page_size=10


Examples
GET /api/menu-items?min_price=5&max_price=20&ordering=-price&page=1&page_size=5
GET /api/menu-items?search=margherita


User Group Management
Method	Endpoint	Role	Purpose
GET	/api/groups/manager/users	Manager	List managers
POST	/api/groups/manager/users	Manager	Add user to Manager ({ "user_id": 3 })
DELETE	/api/groups/manager/users/{userId}	Manager	Remove user from Manager
GET	/api/groups/delivery-crew/users	Manager	List delivery crew
POST	/api/groups/delivery-crew/users	Manager	Add user to Delivery crew ({ "user_id": 5 })
DELETE	/api/groups/delivery-crew/users/{userId}	Manager	Remove user from Delivery crew

Cart (Customer only)
Method	Endpoint	Role	Purpose
GET	/api/cart/menu-items	Customer	Get current user’s cart
POST	/api/cart/menu-items	Customer	Add item: { "menuitem_id": 3, "quantity": 2 } (201)
DELETE	/api/cart/menu-items	Customer	Clear cart

Orders
Method	Endpoint	Role	Purpose
GET	/api/orders	Customer	Own orders
POST	/api/orders	Customer	Create order from cart; empties cart (201)
GET	/api/orders	Manager	All orders
GET	/api/orders	Delivery	Assigned orders
GET	/api/orders/{id}	Customer	Own order only (403 if not owner)
PUT/PATCH	/api/orders/{id}	Manager	Assign delivery_crew and set status (0/1)
PATCH	/api/orders/{id}	Delivery	Update status only (0/1)
DELETE	/api/orders/{id}	Manager	Delete order

Orders filtering / sorting / pagination
Filter:

?status=0|1

?user=<id> (manager only sees all)

?delivery_crew=<id>

?date_after=<ISO8601>&date_before=<ISO8601>

Sort: ?ordering=-date (also total, status)

Pagination: ?page=1&page_size=10

Examples

GET /api/orders?status=1&ordering=-date&page=1&page_size=10
GET /api/orders?date_after=2025-08-01T00:00:00Z&date_before=2025-08-02T23:59:59Z

Status meanings
status = 0 → Out for delivery (when delivery crew is assigned)
status = 1 → Delivered

Throttling
REST_FRAMEWORK.update({
  'DEFAULT_THROTTLE_CLASSES': [
    'rest_framework.throttling.AnonRateThrottle',
    'rest_framework.throttling.UserRateThrottle',
    'rest_framework.throttling.ScopedRateThrottle',
  ],
  'DEFAULT_THROTTLE_RATES': {
    'anon': '15/minute',
    'user': '30/minute',
    'menu': '20/minute',
    'orders': '10/minute',
    'cart': '10/minute',
    'auth': '10/minute',
  },
})


HTTP Status Codes (used consistently)
200 OK – success (GET/PUT/PATCH/DELETE)

201 Created – success (POST)

400 Bad Request – validation errors, empty cart on order create, etc.

401 Unauthorized – no/invalid token

403 Forbidden – role/ownership denied

404 Not Found – non-existing resource

429 Too Many Requests – throttled

Project Structure
littlelemon/
  models.py          # User (custom), MenuItem, CartItem, Order, OrderItem
  views.py           # Menu, Cart, Orders, Group mgmt
  serializers.py     # Serializers for above
  permissions.py     # IsManager, IsCustomer, IsDeliveryCrew
  filters.py         # MenuItemFilter, OrderFilter
  pagination.py      # DefaultPagination
  urls.py            # /api/menu-items, /api/cart/menu-items, /api/orders, /api/groups/...
LittleLemonFinal/
  urls.py            # includes app urls + Djoser urls
