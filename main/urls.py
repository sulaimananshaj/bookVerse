from django.urls import path
from . import views

urlpatterns = [
    path('',                            views.home,             name='home'),
    path('register/',                   views.register_view,    name='register'),
    path('login/',                      views.login_view,       name='login'),
    path('logout/',                     views.logout_view,      name='logout'),
    path('dashboard/',                  views.dashboard,        name='dashboard'),

    # Books
    path('books/',                      views.book_list,        name='book_list'),
    path('books/upload/',               views.upload_book,      name='upload_book'),

    # Admin
    path('admin-panel/',                views.admin_login,      name='admin_login'),
    path('admin-panel/dashboard/',      views.admin_dashboard,  name='admin_dashboard'),
    path('admin-panel/approve/<int:book_id>/', views.approve_book, name='approve_book'),
    path('admin-panel/reject/<int:book_id>/',  views.reject_book,  name='reject_book'),
]