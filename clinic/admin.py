from django.contrib import admin
from .models import (
    Admission,
    Appointment,
    Doctor,
    Medicine,
    MedicineStockMovement,
    Patient,
    Prescription,
    PrescriptionMedicine,
    Room,
    Treatment,
)


@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = (
        "medicine_id",
        "name",
        "category",
        "batch_number",
        "stock_quantity",
        "min_stock_threshold",
        "selling_price",
        "expiry_date",
        "stock_status",
        "expiry_status",
    )
    list_filter = ("category", "expiry_date")
    search_fields = ("name", "batch_number", "manufacturer")


@admin.register(MedicineStockMovement)
class MedicineStockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "movement_id",
        "medicine",
        "movement_type",
        "quantity_change",
        "resulting_stock",
        "created_at",
        "created_by",
    )
    list_filter = ("movement_type", "created_at")
    search_fields = ("medicine__name", "medicine__batch_number", "notes")


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ("patient_id", "name", "phone_no", "blood_group")
    search_fields = ("name", "phone_no")


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("doctor_id", "name", "specialization", "phone_no", "email")
    search_fields = ("name", "specialization", "phone_no")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        "appointment_id",
        "patient",
        "doctor",
        "appointment_date",
        "appointment_time",
        "status",
    )
    list_filter = ("status", "appointment_date", "doctor")
    search_fields = ("patient__name", "doctor__name", "reason_for_visit")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = (
        "room_id",
        "room_number",
        "room_type",
        "bed_capacity",
        "charges_per_day",
        "status",
    )
    list_filter = ("room_type", "status")
    search_fields = ("room_number",)


@admin.register(Admission)
class AdmissionAdmin(admin.ModelAdmin):
    list_display = (
        "admission_id",
        "patient",
        "room",
        "admission_date",
        "discharge_date",
        "status",
    )
    list_filter = ("status", "admission_date", "room__room_type")
    search_fields = ("patient__name", "room__room_number", "reason_for_admission")


@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = (
        "treatment_id",
        "patient",
        "doctor",
        "diagnosis",
        "treatment_date",
    )
    list_filter = ("treatment_date", "doctor")
    search_fields = ("patient__name", "doctor__name", "diagnosis", "description")


class PrescriptionMedicineInline(admin.TabularInline):
    model = PrescriptionMedicine
    extra = 1


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    inlines = [PrescriptionMedicineInline]
    list_display = (
        "prescription_id",
        "patient",
        "doctor",
        "prescription_date",
    )
    list_filter = ("prescription_date", "doctor")
    search_fields = (
        "patient__name",
        "doctor__name",
        "medicines__medicine_name",
        "instructions",
    )
