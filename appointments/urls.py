from django.urls import path
from . import views

urlpatterns = [
    path("book/<int:doctor_id>/", views.book_slot, name="book_slot"),
    path("confirm/<int:doctor_id>/<str:slot_time>/", views.confirm_booking, name="confirm_booking"),
    path('payment/<int:appointment_id>/', views.payment_page, name='payment_page'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('lab/<int:lab_id>/test/<int:test_id>/slots/',views.lab_book_slot,name='lab_book_slot'),


    # =========================
    # CONFIRM LAB BOOKING
    # =========================
    path('lab/<int:lab_id>/test/<int:test_id>/confirm/<str:slot_time>/',views.confirm_lab_booking,name='confirm_lab_booking'),

]