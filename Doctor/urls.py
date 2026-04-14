from django.contrib import admin
from django.conf.urls.static import static
from django.conf import settings
from django.urls import include, path

from accounts.views import RegisterApi, VerifyOtp
from . import views, DoctorViews, LabViews, UserViews, api_views


urlpatterns = [

    # ==========================
    # ADMIN PANEL
    # ==========================
    path('admin/', admin.site.urls),


    # ==========================
    # AUTH SYSTEM
    # ==========================
    path('register/', RegisterApi.as_view(), name='register'),
    path('verify/', VerifyOtp.as_view(), name='verify'),


    # ==========================
    # HOME PAGE
    # ==========================
    path('', views.home, name='home'),


    # ==========================
    # APPOINTMENT SYSTEM (PATIENT SIDE)
    # ==========================
    path("appointments/", include("appointments.urls")),


    # ==========================
    # USER PANEL
    # ==========================
    


    # ==========================
    # DOCTOR PUBLIC PAGES
    # ==========================
    path('doctors/', DoctorViews.doctor_page, name='doctor_page'),
    path('doctor/<int:id>/', DoctorViews.doctor_detail, name='doctor_detail'),


    # ==========================
    # DOCTOR AUTH
    # ==========================
    path('register-doctor/', DoctorViews.register_doctor, name='doctor_register'),
    path('verify-otp/', DoctorViews.verify_otp_page, name='verify_otp_page'),
    path('doctor-login/', DoctorViews.doctor_login, name='doctor_login'),
    path('doctor-login-submit/', DoctorViews.do_doctor_login, name='do_doctor_login'),
    path('doctor/patient/<int:appointment_id>/',DoctorViews.patient,name='doctor_patient'),
    path('doctor/add-prescription/<int:appointment_id>/',DoctorViews.add_prescription,name='add_prescription'),
     


    # ==========================
    # DOCTOR PORTAL
    # ==========================
    path('doctor/dashboard/', DoctorViews.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/availability/', DoctorViews.set_doctor_availability, name='doctor_availability'),
    path('doctor/appointments/', DoctorViews.doctor_appointments, name='doctor_appointments'),

    path('doctor/approve/<int:appointment_id>/', DoctorViews.approve_appointment, name='approve_appointment'),
    path('doctor/reject/<int:appointment_id>/', DoctorViews.reject_appointment, name='reject_appointment'),
    path('doctor/complete/<int:appointment_id>/', DoctorViews.complete_appointment, name='complete_appointment'),

    path('doctor/patients/', DoctorViews.doctor_patients, name='doctor_patients'),
    path('doctor/add-prescription/<int:appointment_id>/', DoctorViews.add_prescription, name='add_prescription'),

    path('doctor/lab-reports/', DoctorViews.doctor_lab_reports, name='doctor_lab_reports'),
    path('doctor/payments/', DoctorViews.doctor_payments, name='doctor_payments'),
    path('doctor/notifications/', DoctorViews.doctor_notifications, name='doctor_notifications'),
    path('doctor/settings/', DoctorViews.doctor_settings, name='doctor_settings'),
    path("doctor/profile/edit/", DoctorViews.doctor_profile_edit, name="doctor_profile_edit"),
    path('doctor/logout/', DoctorViews.doctor_logout, name='doctor_logout'),
    path("doctor/check-appointments/", DoctorViews.check_new_appointments, name="check_appointments"),

    path('doctor/live-status/<int:doctor_id>/', DoctorViews.doctor_live_status, name='doctor_live_status'),

    # ==========================
    # LAB SYSTEM
    # ==========================

    path('register-lab/', LabViews.lab_registration, name='lab_registration'),
    path('verify-lab-otp/', LabViews.verify_lab_otp, name='verify_lab_otp'),
    path('add-lab-tests/', LabViews.add_lab_tests, name='add_lab_tests'),

    path('labs/', LabViews.lab_list, name='lab_list'),
    path('lab-success/', LabViews.lab_success, name='lab_success'),

    path('lab/<int:lab_id>/tests/', LabViews.view_lab_tests, name='view_lab_tests'),

# DASHBOARD
    path('lab/dashboard/', LabViews.lab_dashboard, name='lab_dashboard'),

# BOOKINGS
    path('lab/bookings/', LabViews.lab_bookings, name='lab_bookings'),

    path('lab/approve/<int:appointment_id>/', LabViews.approve_lab_appointment, name='approve_lab_appointment'),

# REPORTS
    path('lab/reports/', LabViews.lab_reports, name='lab_reports'),

    path('lab/upload-report/<int:appointment_id>/', LabViews.upload_lab_report, name='upload_lab_report'),

# SERVICES
    path('lab/services/', LabViews.lab_services, name='lab_services'),

# PROFILE
    path('lab/profile/', LabViews.lab_profile, name='lab_profile'),

# LOGIN SYSTEM
    path('lab/login/', LabViews.lab_login, name='lab_login'),
    path('lab/login-submit/', LabViews.do_lab_login, name='do_lab_login'),
    path('lab/logout/', LabViews.lab_logout, name='lab_logout'),
    path('lab/edit-profile/',LabViews.lab_edit_profile,name='lab_edit_profile'),
    path('Lab/<int:lab_id>/', LabViews.lab_detail, name='lab_detail'),
    path("lab/availability/",LabViews.lab_availability,name="lab_availability"),
    path("lab/toggle-availability/",LabViews.toggle_lab_availability,name="toggle_lab_availability"),
    path('lab/dashboard/', LabViews.lab_dashboard, name="lab_dashboard"),

    path('lab/appointments/', LabViews.lab_appointments, name="lab_appointments"),

    path('lab/appointment/approve/<int:appointment_id>/', LabViews.approve_lab_appointment, name="approve_lab_appointment"),

    path('lab/appointment/reject/<int:appointment_id>/', LabViews.reject_lab_appointment, name="reject_lab_appointment"),

    path('lab/appointment/complete/<int:appointment_id>/', LabViews.complete_lab_appointment, name="complete_lab_appointment"),

    path('lab/appointment/upload-report/<int:appointment_id>/', LabViews.upload_lab_report, name="upload_lab_report"),
    path('lab/update-test/<int:id>/', LabViews.update_test_price, name='update_test_price'),
    path('lab/toggle-test/<int:id>/', LabViews.toggle_test, name='toggle_test'),


    # ==========================
    # API
    # ==========================
    path('api/send-otp/', api_views.send_otp, name='send_otp'),
    path('api/verify-otp/', api_views.verify_otp, name='verify_otp'),
    
    # ==========================
    # patient 
    # ==========================
    
    # ================= AUTH =================
    path('patient/register/', UserViews.register_patient, name='patient_register'),
    path('patient/verify-otp/', UserViews.patient_verify_otp, name='patient_verify_otp'),
    path('patient/login/', UserViews.patient_login, name='patient_login'),
    path('patient/do-login/', UserViews.do_patient_login, name='do_patient_login'),

    # ================= HOME =================
    path('user/', UserViews.user_home, name='user_home'),

    # ================= DASHBOARD =================
    path('user/dashboard/', UserViews.user_dashboard, name='patient_dashboard'),

    # ================= DOCTORS & LABS =================
    path('doctors/', UserViews.user_doctors, name='user_doctors'),
    path('labs/', UserViews.user_labs, name='user_labs'),

    # ================= BOOKINGS =================
    path('my-bookings/', UserViews.my_bookings, name='my_bookings'),

    # ================= PAST =================
    path('past-appointments/', UserViews.past_appointments, name='past_appointments'),

    # ================= CANCEL =================
    path('cancel/<str:type>/<int:id>/', UserViews.cancel_appointment, name='cancel_booking'),

    # ================= LAB =================
    path('lab/book/<int:lab_id>/', UserViews.book_lab_test, name='book_lab_test'),

    # ================= REPORTS (FIXED 🔥) =================
    path('reports/', UserViews.patient_reports, name='patient_reports'),

    # ================= PROFILE =================
    path('user/profile/', UserViews.user_profile, name='user_profile'),
    
    path('profile/', UserViews.user_profile, name='user_profile'),

    # ================= LOGOUT =================
    path('logout/', UserViews.user_logout, name='user_logout'),
    path('cancel-appointment/<str:type>/<int:id>/',UserViews.cancel_appointment,name='cancel_appointment'),

]


# ==========================
# MEDIA FILES (Development)
# ==========================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)