from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", auth_views.LoginView.as_view(template_name="clinic/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    # Patient URLs
    path("patients/", views.patient_list, name="patient_list"),
    path("patients/add/", views.patient_add, name="patient_add"),
    path("patients/<int:pk>/", views.patient_detail, name="patient_detail"),
    path("patients/<int:pk>/edit/", views.patient_edit, name="patient_edit"),
    path("patients/<int:pk>/delete/", views.patient_delete, name="patient_delete"),
    # Doctor URLs
    path("doctors/", views.doctor_list, name="doctor_list"),
    path("doctors/add/", views.doctor_add, name="doctor_add"),
    path("doctors/<int:pk>/", views.doctor_detail, name="doctor_detail"),
    path("doctors/<int:pk>/edit/", views.doctor_edit, name="doctor_edit"),
    path("doctors/<int:pk>/delete/", views.doctor_delete, name="doctor_delete"),
    # Appointment URLs
    path("appointments/", views.appointment_list, name="appointment_list"),
    path("appointments/add/", views.appointment_add, name="appointment_add"),
    path("appointments/<int:pk>/", views.appointment_detail, name="appointment_detail"),
    path("appointments/<int:pk>/edit/", views.appointment_edit, name="appointment_edit"),
    path("appointments/<int:pk>/delete/", views.appointment_delete, name="appointment_delete"),
    # Room URLs
    path("rooms/", views.room_list, name="room_list"),
    path("rooms/add/", views.room_add, name="room_add"),
    path("rooms/<int:pk>/", views.room_detail, name="room_detail"),
    path("rooms/<int:pk>/edit/", views.room_edit, name="room_edit"),
    path("rooms/<int:pk>/delete/", views.room_delete, name="room_delete"),
    # Admission URLs
    path("admissions/", views.admission_list, name="admission_list"),
    path("admissions/add/", views.admission_add, name="admission_add"),
    path("admissions/<int:pk>/", views.admission_detail, name="admission_detail"),
    path("admissions/<int:pk>/edit/", views.admission_edit, name="admission_edit"),
    path("admissions/<int:pk>/discharge/", views.admission_discharge, name="admission_discharge"),
    path("admissions/<int:pk>/delete/", views.admission_delete, name="admission_delete"),
    # Treatment URLs
    path("treatments/", views.treatment_list, name="treatment_list"),
    path("treatments/add/", views.treatment_add, name="treatment_add"),
    path("treatments/<int:pk>/", views.treatment_detail, name="treatment_detail"),
    path("treatments/<int:pk>/edit/", views.treatment_edit, name="treatment_edit"),
    path("treatments/<int:pk>/delete/", views.treatment_delete, name="treatment_delete"),
    # Prescription URLs
    path("prescriptions/", views.prescription_list, name="prescription_list"),
    path("prescriptions/add/", views.prescription_add, name="prescription_add"),
    path("prescriptions/<int:pk>/", views.prescription_detail, name="prescription_detail"),
    path("prescriptions/<int:pk>/edit/", views.prescription_edit, name="prescription_edit"),
    path("prescriptions/<int:pk>/delete/", views.prescription_delete, name="prescription_delete"),
    path("prescriptions/<int:pk>/dispense/", views.prescription_dispense, name="prescription_dispense"),
    # Medicine Inventory URLs
    path("medicines/", views.medicine_list, name="medicine_list"),
    path("medicines/add/", views.medicine_add, name="medicine_add"),
    path("medicines/<int:pk>/", views.medicine_detail, name="medicine_detail"),
    path("medicines/<int:pk>/edit/", views.medicine_edit, name="medicine_edit"),
    path("medicines/<int:pk>/delete/", views.medicine_delete, name="medicine_delete"),
    path("medicines/<int:pk>/stock-in/", views.medicine_stock_in, name="medicine_stock_in"),
    path("medicines/<int:pk>/stock-adjust/", views.medicine_stock_adjust, name="medicine_stock_adjust"),
]
