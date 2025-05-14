from django.urls import path, re_path
from django.contrib import admin
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('carlist/', views.car_list, name='car_list'),
    path('createOrder/', views.order_created, name='order_create'),

    re_path(r'^(?P<id>\d+)/edit/$', views.car_update, name='car_edit'),
    re_path(r'^(?P<id>\d+)/$', views.car_detail, name='car_detail'),
    re_path(r'^detail/(?P<id>\d+)/$', views.order_detail, name='order_detail'),

    re_path(r'^(?P<id>\d+)/delete/$', views.car_delete, name='car_delete'),
    re_path(r'^(?P<id>\d+)/deleteOrder/$', views.order_delete, name='order_delete'),

    path('contact/', views.contact, name='contact'),
    path('newcar/', views.newcar, name='newcar'),
    re_path(r'^(?P<id>\d+)/like/$', views.like_update, name='like'),
    path('popularcar/', views.popular_car, name='popularcar'),
]



