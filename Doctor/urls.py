from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.urls import path
from accounts.views import *

from . import views, DoctorViews, LabViews, UserViews, api_views


urlpatterns = [
    
    path('register/', RegisterApi.as_view()),
    path('verify/', VerifyOtp.as_view()),

    # ========== ADMIN ==========
    path('admin/', admin.site.urls),

    # ========== HOME ==========
    path('', views.home, name='home'),

    # ========== USER ==========
    path('user/', UserViews.user_home, name='user_home'),
    path('user/profile/', UserViews.user_profile, name='user_profile'),
    path('user/appointments/', UserViews.user_appointments, name='user_appointments'),
    path('user/labs/', UserViews.user_labs, name='user_labs'),
    path('user/doctors/', UserViews.user_doctors, name='user_doctors'),

    # ========== DOCTOR (PUBLIC) ==========
    path('doctors/', DoctorViews.doctor_page, name='doctor_page'),
    path('doctor/<int:id>/', DoctorViews.doctor_detail, name='doctor_detail'),

    # ========== DOCTOR AUTH ==========
    path('register-doctor/', DoctorViews.register_doctor, name='doctor_register'),
    path('verify-otp/', DoctorViews.verify_otp_page, name='verify_otp_page'),
    path('doctor-login/', DoctorViews.doctor_login, name='doctor_login'),
    path('doctor-login-submit/', DoctorViews.do_doctor_login, name='do_doctor_login'),

    # ========== DOCTOR PORTAL ==========
    path('doctor/dashboard/', DoctorViews.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/availability/', DoctorViews.set_doctor_availability, name='doctor_availability'),
    path('doctor/logout/', DoctorViews.doctor_logout, name='doctor_logout'),

    # ========== APPOINTMENT ==========
    path(
        'book/<path:doctor_name>/<str:specialization>/',
        DoctorViews.book_appointment,
        name='book_appointment'
    ),

    # ========== LAB ==========
    path('register-lab/', LabViews.lab_registration, name='lab_registration'),
    path('verify-lab-otp/', LabViews.verify_lab_otp, name='verify_lab_otp'),
    path('add-lab-tests/', LabViews.add_lab_tests, name='add_lab_tests'),
    path('labs/', LabViews.lab_list, name='lab_list'),
    path('lab-success/', LabViews.lab_success, name='lab_success'),
    path('lab/<int:lab_id>/tests/', LabViews.view_lab_tests, name='view_lab_tests'),
    path('lab/dashboard/', LabViews.lab_dashboard, name='lab_dashboard'),
    path('lab/approve/<int:appointment_id>/', LabViews.approve_lab_appointment, name='approve_lab_appointment'),
    path('lab/upload-report/<int:appointment_id>/', LabViews.upload_lab_report, name='upload_lab_report'),
    path('lab/logout/', LabViews.lab_logout, name='lab_logout'),
    path('lab/login/', LabViews.lab_login, name='lab_login'),
    path('lab/login-submit/', LabViews.do_lab_login, name='do_lab_login'),
    path('lab/logout/', LabViews.lab_logout, name='lab_logout'),
    path('api/send-otp/', api_views.send_otp),
    path('api/verify-otp/', api_views.verify_otp),
    
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
