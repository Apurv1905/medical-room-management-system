from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import (
    AdmissionForm,
    AppointmentForm,
    DischargeForm,
    DoctorForm,
    MedicineForm,
    PatientForm,
    PrescriptionForm,
    PrescriptionMedicineFormSet,
    RoomForm,
    StockAdjustForm,
    StockInForm,
    TreatmentForm,
)
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


@login_required
def dashboard(request):
    """Show the homepage dashboard with live database counts for all modules."""
    today = timezone.localdate()
    current_month = today.replace(day=1)
    month_starts = []
    for months_ago in reversed(range(6)):
        month_index = current_month.year * 12 + current_month.month - 1 - months_ago
        year, month_index = divmod(month_index, 12)
        month_starts.append(date(year, month_index + 1, 1))

    next_month_index = current_month.year * 12 + current_month.month
    next_month_year, next_month_index = divmod(next_month_index, 12)
    next_month = date(next_month_year, next_month_index + 1, 1)
    appointment_counts = {
        (item["appointment_date__year"], item["appointment_date__month"]): item["total"]
        for item in Appointment.objects.filter(
            appointment_date__gte=month_starts[0],
            appointment_date__lt=next_month,
        )
        .values("appointment_date__year", "appointment_date__month")
        .annotate(total=Count("appointment_id"))
    }

    active_admissions = Admission.objects.filter(status="Admitted").count()
    total_beds = Room.objects.aggregate(total=Sum("bed_capacity"))["total"] or 0
    occupied_beds = active_admissions
    available_beds = max(0, total_beds - occupied_beds)

    total_medicines = Medicine.objects.count()
    low_stock_medicines = Medicine.objects.filter(
        stock_quantity__lte=F("min_stock_threshold"), stock_quantity__gt=0
    ).count()
    out_of_stock_medicines = Medicine.objects.filter(stock_quantity=0).count()
    expired_medicines = Medicine.objects.filter(expiry_date__lt=today).count()
    expiring_soon_medicines = Medicine.objects.filter(
        expiry_date__gte=today, expiry_date__lte=today + timedelta(days=30)
    ).count()
    total_stock_units = Medicine.objects.aggregate(total=Sum("stock_quantity"))["total"] or 0
    inventory_alert_medicines = Medicine.objects.filter(
        stock_quantity__lte=F("min_stock_threshold")
    ).order_by("stock_quantity", "name")[:5]
    upcoming_appointments = (
        Appointment.objects.select_related("patient", "doctor")
        .filter(status="Scheduled")
        .filter(
            Q(appointment_date__gt=today)
            | Q(
                appointment_date=today,
                appointment_time__gte=timezone.localtime().time().replace(tzinfo=None),
            )
        )
        .order_by("appointment_date", "appointment_time")[:5]
    )

    context = {
        "total_patients": Patient.objects.count(),
        "total_doctors": Doctor.objects.count(),
        "total_appointments": Appointment.objects.count(),
        "total_rooms": Room.objects.count(),
        "total_admissions": Admission.objects.count(),
        "active_admissions": active_admissions,
        "total_treatments": Treatment.objects.count(),
        "total_prescriptions": Prescription.objects.count(),
        "total_medicines": total_medicines,
        "low_stock_medicines": low_stock_medicines,
        "out_of_stock_medicines": out_of_stock_medicines,
        "expired_medicines": expired_medicines,
        "expiring_soon_medicines": expiring_soon_medicines,
        "appointment_chart_labels": [month.strftime("%b %y") for month in month_starts],
        "appointment_chart_data": [
            appointment_counts.get((month.year, month.month), 0)
            for month in month_starts
        ],
        "total_beds": total_beds,
        "occupied_beds": occupied_beds,
        "available_beds": available_beds,
        "occupancy_percent": min(round(occupied_beds * 100 / total_beds), 100)
        if total_beds
        else 0,
        "availability_percent": round(available_beds * 100 / total_beds) if total_beds else 0,
        "maintenance_rooms": Room.objects.filter(status="Under Maintenance").count(),
        "total_stock_units": total_stock_units,
        "inventory_alert_medicines": inventory_alert_medicines,
        "upcoming_appointments": upcoming_appointments,
        "active_nav": "dashboard",
    }
    return render(request, "clinic/dashboard.html", context)


# ---------------------------------------------------------
# Patient Management Views
# ---------------------------------------------------------

@login_required
def patient_list(request):
    query = request.GET.get("q", "").strip()
    patients = Patient.objects.all().order_by("name")
    if query:
        patients = patients.filter(
            Q(name__icontains=query) | Q(phone_no__icontains=query)
        )
    context = {
        "patients": patients,
        "query": query,
        "active_nav": "patients",
    }
    return render(request, "clinic/patient_list.html", context)


@login_required
def patient_add(request):
    if request.method == "POST":
        form = PatientForm(request.POST)
        if form.is_valid():
            patient = form.save()
            messages.success(request, "Patient added successfully.")
            return redirect("patient_detail", pk=patient.pk)
    else:
        form = PatientForm()
    context = {
        "form": form,
        "form_title": "Add Patient",
        "submit_label": "Save Patient",
        "active_nav": "patients",
    }
    return render(request, "clinic/patient_form.html", context)


@login_required
def patient_detail(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    context = {
        "patient": patient,
        "active_nav": "patients",
    }
    return render(request, "clinic/patient_detail.html", context)


@login_required
def patient_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == "POST":
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            messages.success(request, "Patient details updated successfully.")
            return redirect("patient_detail", pk=patient.pk)
    else:
        form = PatientForm(instance=patient)
    context = {
        "form": form,
        "patient": patient,
        "form_title": "Edit Patient",
        "submit_label": "Update Patient",
        "active_nav": "patients",
    }
    return render(request, "clinic/patient_form.html", context)


@login_required
def patient_delete(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    if request.method == "POST":
        patient.delete()
        messages.success(request, "Patient deleted successfully.")
        return redirect("patient_list")
    context = {
        "patient": patient,
        "active_nav": "patients",
    }
    return render(request, "clinic/patient_confirm_delete.html", context)


# ---------------------------------------------------------
# Doctor Management Views
# ---------------------------------------------------------

@login_required
def doctor_list(request):
    query = request.GET.get("q", "").strip()
    doctors = Doctor.objects.all().order_by("name")
    if query:
        doctors = doctors.filter(
            Q(name__icontains=query) | Q(specialization__icontains=query)
        )
    context = {
        "doctors": doctors,
        "query": query,
        "active_nav": "doctors",
    }
    return render(request, "clinic/doctor_list.html", context)


@login_required
def doctor_add(request):
    if request.method == "POST":
        form = DoctorForm(request.POST)
        if form.is_valid():
            doctor = form.save()
            messages.success(request, "Doctor added successfully.")
            return redirect("doctor_detail", pk=doctor.pk)
    else:
        form = DoctorForm()
    context = {
        "form": form,
        "form_title": "Add Doctor",
        "submit_label": "Save Doctor",
        "active_nav": "doctors",
    }
    return render(request, "clinic/doctor_form.html", context)


@login_required
def doctor_detail(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    context = {
        "doctor": doctor,
        "active_nav": "doctors",
    }
    return render(request, "clinic/doctor_detail.html", context)


@login_required
def doctor_edit(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    if request.method == "POST":
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, "Doctor details updated successfully.")
            return redirect("doctor_detail", pk=doctor.pk)
    else:
        form = DoctorForm(instance=doctor)
    context = {
        "form": form,
        "doctor": doctor,
        "form_title": "Edit Doctor",
        "submit_label": "Update Doctor",
        "active_nav": "doctors",
    }
    return render(request, "clinic/doctor_form.html", context)


@login_required
def doctor_delete(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    if request.method == "POST":
        doctor.delete()
        messages.success(request, "Doctor deleted successfully.")
        return redirect("doctor_list")
    context = {
        "doctor": doctor,
        "active_nav": "doctors",
    }
    return render(request, "clinic/doctor_confirm_delete.html", context)


# ---------------------------------------------------------
# Appointment Management Views
# ---------------------------------------------------------

@login_required
def appointment_list(request):
    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    doctor_filter = request.GET.get("doctor", "").strip()
    date_filter = request.GET.get("date", "").strip()

    appointments = Appointment.objects.select_related("patient", "doctor").all()

    if query:
        appointments = appointments.filter(
            Q(patient__name__icontains=query)
            | Q(doctor__name__icontains=query)
            | Q(doctor__specialization__icontains=query)
            | Q(reason_for_visit__icontains=query)
        )
    if status_filter:
        appointments = appointments.filter(status=status_filter)
    if doctor_filter:
        appointments = appointments.filter(doctor_id=doctor_filter)
    if date_filter:
        appointments = appointments.filter(appointment_date=date_filter)

    appointments = appointments.order_by("-appointment_date", "-appointment_time")
    doctors = Doctor.objects.all().order_by("name")

    context = {
        "appointments": appointments,
        "doctors": doctors,
        "query": query,
        "status_filter": status_filter,
        "doctor_filter": doctor_filter,
        "date_filter": date_filter,
        "status_choices": Appointment.STATUS_CHOICES,
        "active_nav": "appointments",
    }
    return render(request, "clinic/appointment_list.html", context)


@login_required
def appointment_add(request):
    has_patients = Patient.objects.exists()
    has_doctors = Doctor.objects.exists()

    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save()
            messages.success(request, "Appointment scheduled successfully.")
            return redirect("appointment_detail", pk=appointment.pk)
    else:
        initial = {}
        if request.GET.get("patient"):
            initial["patient"] = request.GET.get("patient")
        if request.GET.get("doctor"):
            initial["doctor"] = request.GET.get("doctor")
        form = AppointmentForm(initial=initial)

    context = {
        "form": form,
        "form_title": "Schedule Appointment",
        "submit_label": "Save Appointment",
        "has_prerequisites": has_patients and has_doctors,
        "active_nav": "appointments",
    }
    return render(request, "clinic/appointment_form.html", context)


@login_required
def appointment_detail(request, pk):
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "doctor"),
        pk=pk,
    )
    context = {
        "appointment": appointment,
        "active_nav": "appointments",
    }
    return render(request, "clinic/appointment_detail.html", context)


@login_required
def appointment_edit(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, "Appointment details updated successfully.")
            return redirect("appointment_detail", pk=appointment.pk)
    else:
        form = AppointmentForm(instance=appointment)

    context = {
        "form": form,
        "appointment": appointment,
        "form_title": "Edit Appointment",
        "submit_label": "Update Appointment",
        "has_prerequisites": True,
        "active_nav": "appointments",
    }
    return render(request, "clinic/appointment_form.html", context)


@login_required
def appointment_delete(request, pk):
    appointment = get_object_or_404(
        Appointment.objects.select_related("patient", "doctor"),
        pk=pk,
    )
    if request.method == "POST":
        appointment.delete()
        messages.success(request, "Appointment deleted successfully.")
        return redirect("appointment_list")
    context = {
        "appointment": appointment,
        "active_nav": "appointments",
    }
    return render(request, "clinic/appointment_confirm_delete.html", context)


# ---------------------------------------------------------
# Room Management Views
# ---------------------------------------------------------

@login_required
def room_list(request):
    query = request.GET.get("q", "").strip()
    type_filter = request.GET.get("type", "").strip()
    status_filter = request.GET.get("status", "").strip()

    rooms = Room.objects.all().prefetch_related("admissions")

    if query:
        rooms = rooms.filter(room_number__icontains=query)
    if type_filter:
        rooms = rooms.filter(room_type=type_filter)
    if status_filter:
        if status_filter == "Under Maintenance":
            rooms = rooms.filter(status="Under Maintenance")
        elif status_filter == "Available":
            rooms = [r for r in rooms if r.status != "Under Maintenance" and not r.is_full]
        elif status_filter == "Full":
            rooms = [r for r in rooms if r.status != "Under Maintenance" and r.is_full]

    context = {
        "rooms": rooms,
        "query": query,
        "type_filter": type_filter,
        "status_filter": status_filter,
        "room_types": Room.ROOM_TYPE_CHOICES,
        "room_statuses": ["Available", "Full", "Under Maintenance"],
        "active_nav": "rooms",
    }
    return render(request, "clinic/room_list.html", context)


@login_required
def room_add(request):
    if request.method == "POST":
        form = RoomForm(request.POST)
        if form.is_valid():
            room = form.save()
            messages.success(request, f"Room {room.room_number} added successfully.")
            return redirect("room_detail", pk=room.pk)
    else:
        form = RoomForm()

    context = {
        "form": form,
        "form_title": "Add New Room",
        "submit_label": "Save Room",
        "active_nav": "rooms",
    }
    return render(request, "clinic/room_form.html", context)


@login_required
def room_detail(request, pk):
    room = get_object_or_404(Room.objects.prefetch_related("admissions__patient"), pk=pk)
    active_admissions = room.admissions.filter(status="Admitted").select_related("patient")
    past_admissions = room.admissions.filter(status="Discharged").select_related("patient")

    context = {
        "room": room,
        "active_admissions": active_admissions,
        "past_admissions": past_admissions,
        "active_nav": "rooms",
    }
    return render(request, "clinic/room_detail.html", context)


@login_required
def room_edit(request, pk):
    room = get_object_or_404(Room, pk=pk)
    if request.method == "POST":
        form = RoomForm(request.POST, instance=room)
        if form.is_valid():
            form.save()
            messages.success(request, f"Room {room.room_number} updated successfully.")
            return redirect("room_detail", pk=room.pk)
    else:
        form = RoomForm(instance=room)

    context = {
        "form": form,
        "room": room,
        "form_title": f"Edit Room {room.room_number}",
        "submit_label": "Update Room",
        "active_nav": "rooms",
    }
    return render(request, "clinic/room_form.html", context)


@login_required
def room_delete(request, pk):
    room = get_object_or_404(Room, pk=pk)
    active_admissions_count = room.active_admissions_count

    if active_admissions_count > 0:
        messages.error(
            request,
            f"Cannot delete Room {room.room_number} because it currently has {active_admissions_count} active admitted patient(s). Please discharge or transfer all patients before deleting.",
        )
        return redirect("room_detail", pk=room.pk)

    if request.method == "POST":
        room_number = room.room_number
        room.delete()
        messages.success(request, f"Room {room_number} deleted successfully.")
        return redirect("room_list")

    context = {
        "room": room,
        "active_nav": "rooms",
    }
    return render(request, "clinic/room_confirm_delete.html", context)


# ---------------------------------------------------------
# Admission Management Views
# ---------------------------------------------------------

@login_required
def admission_list(request):
    query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    room_filter = request.GET.get("room", "").strip()
    date_filter = request.GET.get("date", "").strip()

    admissions = Admission.objects.select_related("patient", "room").all()

    if query:
        admissions = admissions.filter(
            Q(patient__name__icontains=query)
            | Q(room__room_number__icontains=query)
            | Q(reason_for_admission__icontains=query)
        )
    if status_filter:
        admissions = admissions.filter(status=status_filter)
    if room_filter:
        admissions = admissions.filter(room_id=room_filter)
    if date_filter:
        admissions = admissions.filter(admission_date=date_filter)

    admissions = admissions.order_by("-admission_date", "-admission_id")
    rooms = Room.objects.all().order_by("room_number")

    total_active = Admission.objects.filter(status="Admitted").count()
    total_discharged = Admission.objects.filter(status="Discharged").count()

    context = {
        "admissions": admissions,
        "rooms": rooms,
        "query": query,
        "status_filter": status_filter,
        "room_filter": room_filter,
        "date_filter": date_filter,
        "total_active": total_active,
        "total_discharged": total_discharged,
        "status_choices": Admission.STATUS_CHOICES,
        "active_nav": "admissions",
    }
    return render(request, "clinic/admission_list.html", context)


@login_required
def admission_add(request):
    has_patients = Patient.objects.exists()
    has_rooms = Room.objects.exists()

    if request.method == "POST":
        form = AdmissionForm(request.POST)
        if form.is_valid():
            admission = form.save()
            messages.success(
                request,
                f"Patient {admission.patient.name} successfully admitted to Room {admission.room.room_number}.",
            )
            return redirect("admission_detail", pk=admission.pk)
    else:
        initial = {
            "admission_date": timezone.localdate(),
            "status": "Admitted",
        }
        if request.GET.get("patient"):
            initial["patient"] = request.GET.get("patient")
        if request.GET.get("room"):
            initial["room"] = request.GET.get("room")
        form = AdmissionForm(initial=initial)

    context = {
        "form": form,
        "form_title": "Admit New Patient",
        "submit_label": "Admit Patient",
        "has_prerequisites": has_patients and has_rooms,
        "active_nav": "admissions",
    }
    return render(request, "clinic/admission_form.html", context)


@login_required
def admission_detail(request, pk):
    admission = get_object_or_404(
        Admission.objects.select_related("patient", "room"),
        pk=pk,
    )
    # Calculate length of stay and cost
    end_date = admission.discharge_date or timezone.localdate()
    days_admitted = max(1, (end_date - admission.admission_date).days)
    estimated_charges = days_admitted * admission.room.charges_per_day

    context = {
        "admission": admission,
        "days_admitted": days_admitted,
        "estimated_charges": estimated_charges,
        "active_nav": "admissions",
    }
    return render(request, "clinic/admission_detail.html", context)


@login_required
def admission_edit(request, pk):
    admission = get_object_or_404(Admission, pk=pk)
    if request.method == "POST":
        form = AdmissionForm(request.POST, instance=admission)
        if form.is_valid():
            form.save()
            messages.success(request, "Admission details updated successfully.")
            return redirect("admission_detail", pk=admission.pk)
    else:
        form = AdmissionForm(instance=admission)

    context = {
        "form": form,
        "admission": admission,
        "form_title": f"Edit Admission #{admission.admission_id}",
        "submit_label": "Update Admission",
        "has_prerequisites": True,
        "active_nav": "admissions",
    }
    return render(request, "clinic/admission_form.html", context)


@login_required
def admission_discharge(request, pk):
    admission = get_object_or_404(
        Admission.objects.select_related("patient", "room"),
        pk=pk,
    )

    if admission.status == "Discharged":
        messages.info(
            request,
            f"Patient {admission.patient.name} has already been discharged on {admission.discharge_date}.",
        )
        return redirect("admission_detail", pk=admission.pk)

    if request.method == "POST":
        form = DischargeForm(admission, request.POST)
        if form.is_valid():
            admission.status = "Discharged"
            admission.discharge_date = form.cleaned_data["discharge_date"]
            admission.save()
            messages.success(
                request,
                f"Patient {admission.patient.name} successfully discharged from Room {admission.room.room_number}.",
            )
            return redirect("admission_detail", pk=admission.pk)
    else:
        form = DischargeForm(admission)

    context = {
        "form": form,
        "admission": admission,
        "active_nav": "admissions",
    }
    return render(request, "clinic/admission_discharge.html", context)


@login_required
def admission_delete(request, pk):
    admission = get_object_or_404(
        Admission.objects.select_related("patient", "room"),
        pk=pk,
    )
    if request.method == "POST":
        admission.delete()
        messages.success(request, "Admission record deleted successfully.")
        return redirect("admission_list")

    context = {
        "admission": admission,
        "active_nav": "admissions",
    }
    return render(request, "clinic/admission_confirm_delete.html", context)



# ---------------------------------------------------------
# Treatment Management Views
# ---------------------------------------------------------

@login_required
def treatment_list(request):
    query = request.GET.get("q", "").strip()
    doctor_filter = request.GET.get("doctor", "").strip()
    date_filter = request.GET.get("date", "").strip()

    treatments = Treatment.objects.select_related("patient", "doctor").all()

    if query:
        treatments = treatments.filter(
            Q(patient__name__icontains=query)
            | Q(doctor__name__icontains=query)
            | Q(diagnosis__icontains=query)
            | Q(description__icontains=query)
        )
    if doctor_filter:
        treatments = treatments.filter(doctor_id=doctor_filter)
    if date_filter:
        treatments = treatments.filter(treatment_date=date_filter)

    treatments = treatments.order_by("-treatment_date", "-treatment_id")
    doctors = Doctor.objects.all().order_by("name")

    context = {
        "treatments": treatments,
        "doctors": doctors,
        "query": query,
        "doctor_filter": doctor_filter,
        "date_filter": date_filter,
        "active_nav": "treatments",
    }
    return render(request, "clinic/treatment_list.html", context)


@login_required
def treatment_add(request):
    has_patients = Patient.objects.exists()
    has_doctors = Doctor.objects.exists()

    if request.method == "POST":
        form = TreatmentForm(request.POST)
        if form.is_valid():
            treatment = form.save()
            messages.success(request, "Treatment record added successfully.")
            return redirect("treatment_detail", pk=treatment.pk)
    else:
        initial = {}
        if request.GET.get("patient"):
            initial["patient"] = request.GET.get("patient")
        if request.GET.get("doctor"):
            initial["doctor"] = request.GET.get("doctor")
        initial.setdefault("treatment_date", timezone.localdate())
        form = TreatmentForm(initial=initial)

    context = {
        "form": form,
        "form_title": "Add Treatment Record",
        "submit_label": "Save Treatment",
        "has_prerequisites": has_patients and has_doctors,
        "active_nav": "treatments",
    }
    return render(request, "clinic/treatment_form.html", context)


@login_required
def treatment_detail(request, pk):
    treatment = get_object_or_404(
        Treatment.objects.select_related("patient", "doctor"),
        pk=pk,
    )
    context = {
        "treatment": treatment,
        "active_nav": "treatments",
    }
    return render(request, "clinic/treatment_detail.html", context)


@login_required
def treatment_edit(request, pk):
    treatment = get_object_or_404(Treatment, pk=pk)
    if request.method == "POST":
        form = TreatmentForm(request.POST, instance=treatment)
        if form.is_valid():
            form.save()
            messages.success(request, "Treatment record updated successfully.")
            return redirect("treatment_detail", pk=treatment.pk)
    else:
        form = TreatmentForm(instance=treatment)

    context = {
        "form": form,
        "treatment": treatment,
        "form_title": f"Edit Treatment #{treatment.treatment_id}",
        "submit_label": "Update Treatment",
        "has_prerequisites": True,
        "active_nav": "treatments",
    }
    return render(request, "clinic/treatment_form.html", context)


@login_required
def treatment_delete(request, pk):
    treatment = get_object_or_404(
        Treatment.objects.select_related("patient", "doctor"),
        pk=pk,
    )
    if request.method == "POST":
        treatment.delete()
        messages.success(request, "Treatment record deleted successfully.")
        return redirect("treatment_list")

    context = {
        "treatment": treatment,
        "active_nav": "treatments",
    }
    return render(request, "clinic/treatment_confirm_delete.html", context)


# ---------------------------------------------------------
# Prescription Management Views
# ---------------------------------------------------------

@login_required
def prescription_list(request):
    query = request.GET.get("q", "").strip()
    doctor_filter = request.GET.get("doctor", "").strip()
    date_filter = request.GET.get("date", "").strip()

    prescriptions = Prescription.objects.select_related("patient", "doctor").prefetch_related("medicines").all()

    if query:
        prescriptions = prescriptions.filter(
            Q(patient__name__icontains=query)
            | Q(doctor__name__icontains=query)
            | Q(medicines__medicine_name__icontains=query)
            | Q(instructions__icontains=query)
        ).distinct()
    if doctor_filter:
        prescriptions = prescriptions.filter(doctor_id=doctor_filter)
    if date_filter:
        prescriptions = prescriptions.filter(prescription_date=date_filter)

    prescriptions = prescriptions.order_by("-prescription_date", "-prescription_id")
    doctors = Doctor.objects.all().order_by("name")

    context = {
        "prescriptions": prescriptions,
        "doctors": doctors,
        "query": query,
        "doctor_filter": doctor_filter,
        "date_filter": date_filter,
        "active_nav": "prescriptions",
    }
    return render(request, "clinic/prescription_list.html", context)


@login_required
def prescription_add(request):
    has_patients = Patient.objects.exists()
    has_doctors = Doctor.objects.exists()

    if request.method == "POST":
        form = PrescriptionForm(request.POST)
        formset = PrescriptionMedicineFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            prescription = form.save()
            formset.instance = prescription
            formset.save()
            messages.success(request, "Prescription created successfully.")
            return redirect("prescription_detail", pk=prescription.pk)
    else:
        initial = {}
        if request.GET.get("patient"):
            initial["patient"] = request.GET.get("patient")
        if request.GET.get("doctor"):
            initial["doctor"] = request.GET.get("doctor")
        initial.setdefault("prescription_date", timezone.localdate())
        form = PrescriptionForm(initial=initial)
        formset = PrescriptionMedicineFormSet()

    context = {
        "form": form,
        "formset": formset,
        "form_title": "New Prescription",
        "submit_label": "Save Prescription",
        "has_prerequisites": has_patients and has_doctors,
        "active_nav": "prescriptions",
    }
    return render(request, "clinic/prescription_form.html", context)


@login_required
def prescription_detail(request, pk):
    prescription = get_object_or_404(
        Prescription.objects.select_related("patient", "doctor").prefetch_related("medicines"),
        pk=pk,
    )
    context = {
        "prescription": prescription,
        "medicines": prescription.medicines.all(),
        "active_nav": "prescriptions",
    }
    return render(request, "clinic/prescription_detail.html", context)


@login_required
def prescription_edit(request, pk):
    prescription = get_object_or_404(Prescription, pk=pk)
    if request.method == "POST":
        form = PrescriptionForm(request.POST, instance=prescription)
        formset = PrescriptionMedicineFormSet(request.POST, instance=prescription)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, "Prescription updated successfully.")
            return redirect("prescription_detail", pk=prescription.pk)
    else:
        form = PrescriptionForm(instance=prescription)
        formset = PrescriptionMedicineFormSet(instance=prescription)

    context = {
        "form": form,
        "formset": formset,
        "prescription": prescription,
        "form_title": f"Edit Prescription #{prescription.prescription_id}",
        "submit_label": "Update Prescription",
        "has_prerequisites": True,
        "active_nav": "prescriptions",
    }
    return render(request, "clinic/prescription_form.html", context)


@login_required
def prescription_delete(request, pk):
    prescription = get_object_or_404(
        Prescription.objects.select_related("patient", "doctor"),
        pk=pk,
    )
    if request.method == "POST":
        prescription.delete()
        messages.success(request, "Prescription deleted successfully.")
        return redirect("prescription_list")

    context = {
        "prescription": prescription,
        "active_nav": "prescriptions",
    }
    return render(request, "clinic/prescription_confirm_delete.html", context)


@login_required
def prescription_dispense(request, pk):
    """Explicitly dispense prescribed medicines and deduct inventory stock.

    Validates stock availability and prevents negative stock.
    Stock is never deducted automatically upon prescription creation.
    """
    prescription = get_object_or_404(
        Prescription.objects.select_related("patient", "doctor").prefetch_related("medicines__medicine"),
        pk=pk,
    )

    if request.method != "POST":
        return redirect("prescription_detail", pk=prescription.pk)

    pending_items = list(prescription.medicines.filter(medicine__isnull=False, is_dispensed=False))

    if not pending_items:
        messages.info(
            request,
            "No pending inventory items to dispense for this prescription.",
        )
        return redirect("prescription_detail", pk=prescription.pk)

    # Validate stock availability and expiry for all pending medicines before deducting anything
    errors = []
    for item in pending_items:
        med = item.medicine
        if med.stock_quantity < item.quantity:
            errors.append(
                f"Insufficient stock for '{med.name}' (Batch: {med.batch_number}). "
                f"Required: {item.quantity}, Available: {med.stock_quantity}."
            )
        elif med.is_expired:
            errors.append(
                f"Medicine '{med.name}' (Batch: {med.batch_number}) expired on {med.expiry_date}. "
                "Cannot dispense expired stock."
            )

    if errors:
        for err in errors:
            messages.error(request, err)
        return redirect("prescription_detail", pk=prescription.pk)

    # Perform atomic deduction
    with transaction.atomic():
        for item in pending_items:
            med = item.medicine
            med.stock_quantity -= item.quantity
            med.save()

            item.is_dispensed = True
            item.dispensed_at = timezone.now()
            item.save()

            MedicineStockMovement.objects.create(
                medicine=med,
                movement_type="Dispensed",
                quantity_change=-item.quantity,
                resulting_stock=med.stock_quantity,
                notes=f"Dispensed for Prescription #{prescription.prescription_id} (Patient: {prescription.patient.name})",
                created_by=request.user,
            )

    messages.success(
        request,
        f"Medicines successfully dispensed for Prescription #{prescription.prescription_id}. Inventory stock deducted.",
    )
    return redirect("prescription_detail", pk=prescription.pk)


# ---------------------------------------------------------
# Medicine Inventory Management Views
# ---------------------------------------------------------

@login_required
def medicine_list(request):
    today = timezone.localdate()
    query = request.GET.get("q", "").strip()
    category_filter = request.GET.get("category", "").strip()
    status_filter = request.GET.get("status", "").strip()

    medicines = Medicine.objects.all()

    if query:
        medicines = medicines.filter(
            Q(name__icontains=query)
            | Q(batch_number__icontains=query)
            | Q(manufacturer__icontains=query)
        )

    if category_filter:
        medicines = medicines.filter(category=category_filter)

    if status_filter == "low_stock":
        medicines = medicines.filter(
            stock_quantity__lte=F("min_stock_threshold"), stock_quantity__gt=0
        )
    elif status_filter == "out_of_stock":
        medicines = medicines.filter(stock_quantity=0)
    elif status_filter == "in_stock":
        medicines = medicines.filter(stock_quantity__gt=F("min_stock_threshold"))
    elif status_filter == "expired":
        medicines = medicines.filter(expiry_date__lt=today)
    elif status_filter == "expiring_soon":
        medicines = medicines.filter(
            expiry_date__gte=today, expiry_date__lte=today + timedelta(days=30)
        )

    medicines = medicines.order_by("name", "batch_number")

    total_count = Medicine.objects.count()
    low_stock_count = Medicine.objects.filter(
        stock_quantity__lte=F("min_stock_threshold"), stock_quantity__gt=0
    ).count()
    out_of_stock_count = Medicine.objects.filter(stock_quantity=0).count()
    expired_count = Medicine.objects.filter(expiry_date__lt=today).count()
    expiring_soon_count = Medicine.objects.filter(
        expiry_date__gte=today, expiry_date__lte=today + timedelta(days=30)
    ).count()

    context = {
        "medicines": medicines,
        "categories": [c[0] for c in Medicine.CATEGORY_CHOICES],
        "query": query,
        "category_filter": category_filter,
        "status_filter": status_filter,
        "total_count": total_count,
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "expired_count": expired_count,
        "expiring_soon_count": expiring_soon_count,
        "active_nav": "medicines",
    }
    return render(request, "clinic/medicine_list.html", context)


@login_required
def medicine_add(request):
    if request.method == "POST":
        form = MedicineForm(request.POST)
        if form.is_valid():
            medicine = form.save()
            if medicine.stock_quantity > 0:
                MedicineStockMovement.objects.create(
                    medicine=medicine,
                    movement_type="Initial Stock",
                    quantity_change=medicine.stock_quantity,
                    resulting_stock=medicine.stock_quantity,
                    notes="Initial stock quantity recorded upon creation.",
                    created_by=request.user,
                )
            messages.success(
                request,
                f"Medicine '{medicine.name}' (Batch: {medicine.batch_number}) added successfully.",
            )
            return redirect("medicine_detail", pk=medicine.pk)
    else:
        form = MedicineForm()

    context = {
        "form": form,
        "form_title": "Add New Medicine",
        "submit_label": "Save Medicine",
        "active_nav": "medicines",
    }
    return render(request, "clinic/medicine_form.html", context)


@login_required
def medicine_detail(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    recent_movements = medicine.stock_movements.select_related("created_by")[:15]
    recent_prescriptions = (
        medicine.prescription_items.select_related("prescription", "prescription__patient", "prescription__doctor")
        .order_by("-prescription__prescription_date", "-id")[:10]
    )

    context = {
        "medicine": medicine,
        "recent_movements": recent_movements,
        "recent_prescriptions": recent_prescriptions,
        "active_nav": "medicines",
    }
    return render(request, "clinic/medicine_detail.html", context)


@login_required
def medicine_edit(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    old_stock = medicine.stock_quantity

    if request.method == "POST":
        form = MedicineForm(request.POST, instance=medicine)
        if form.is_valid():
            medicine = form.save()
            if medicine.stock_quantity != old_stock:
                diff = medicine.stock_quantity - old_stock
                MedicineStockMovement.objects.create(
                    medicine=medicine,
                    movement_type="Adjustment",
                    quantity_change=diff,
                    resulting_stock=medicine.stock_quantity,
                    notes="Stock quantity adjusted during record edit.",
                    created_by=request.user,
                )
            messages.success(
                request,
                f"Medicine '{medicine.name}' updated successfully.",
            )
            return redirect("medicine_detail", pk=medicine.pk)
    else:
        form = MedicineForm(instance=medicine)

    context = {
        "form": form,
        "medicine": medicine,
        "form_title": f"Edit Medicine: {medicine.name}",
        "submit_label": "Update Medicine",
        "active_nav": "medicines",
    }
    return render(request, "clinic/medicine_form.html", context)


@login_required
def medicine_delete(request, pk):
    medicine = get_object_or_404(Medicine, pk=pk)
    if request.method == "POST":
        name = medicine.name
        batch = medicine.batch_number
        medicine.delete()
        messages.success(request, f"Medicine '{name}' (Batch: {batch}) deleted successfully.")
        return redirect("medicine_list")

    context = {
        "medicine": medicine,
        "active_nav": "medicines",
    }
    return render(request, "clinic/medicine_confirm_delete.html", context)


@login_required
def medicine_stock_in(request, pk):
    """Receive newly purchased inventory stock for an existing medicine."""
    medicine = get_object_or_404(Medicine, pk=pk)

    if request.method == "POST":
        form = StockInForm(request.POST)
        if form.is_valid():
            quantity_to_add = form.cleaned_data["quantity"]
            purchase_price = form.cleaned_data.get("purchase_price")
            selling_price = form.cleaned_data.get("selling_price")
            notes = (form.cleaned_data.get("notes") or "").strip()

            medicine.stock_quantity += quantity_to_add
            if purchase_price:
                medicine.purchase_price = purchase_price
            if selling_price:
                medicine.selling_price = selling_price
            medicine.save()

            note_text = notes or "Newly purchased stock received."
            MedicineStockMovement.objects.create(
                medicine=medicine,
                movement_type="Stock In",
                quantity_change=quantity_to_add,
                resulting_stock=medicine.stock_quantity,
                notes=note_text,
                created_by=request.user,
            )

            messages.success(
                request,
                f"Added {quantity_to_add} units to '{medicine.name}'. New stock: {medicine.stock_quantity}.",
            )
            return redirect("medicine_detail", pk=medicine.pk)
    else:
        form = StockInForm()

    context = {
        "form": form,
        "medicine": medicine,
        "form_title": f"Stock In: {medicine.name}",
        "submit_label": "Confirm Stock In",
        "active_nav": "medicines",
    }
    return render(request, "clinic/medicine_stock_in.html", context)


@login_required
def medicine_stock_adjust(request, pk):
    """Perform a stock reconciliation adjustment with strict validation."""
    medicine = get_object_or_404(Medicine, pk=pk)

    if request.method == "POST":
        form = StockAdjustForm(medicine.stock_quantity, request.POST)
        if form.is_valid():
            action = form.cleaned_data["action"]
            quantity = form.cleaned_data["quantity"]
            reason = form.cleaned_data["reason"]
            notes = (form.cleaned_data.get("notes") or "").strip()

            old_stock = medicine.stock_quantity
            if action == "ADD":
                new_stock = old_stock + quantity
                diff = quantity
            elif action == "DEDUCT":
                new_stock = old_stock - quantity
                diff = -quantity
            elif action == "SET":
                new_stock = quantity
                diff = quantity - old_stock

            medicine.stock_quantity = new_stock
            medicine.save()

            note_text = f"Adjustment [{reason}]: {notes}".strip(" :")
            MedicineStockMovement.objects.create(
                medicine=medicine,
                movement_type="Adjustment",
                quantity_change=diff,
                resulting_stock=new_stock,
                notes=note_text,
                created_by=request.user,
            )

            messages.success(
                request,
                f"Stock adjusted for '{medicine.name}'. Previous: {old_stock}, Current: {new_stock}.",
            )
            return redirect("medicine_detail", pk=medicine.pk)
    else:
        form = StockAdjustForm(medicine.stock_quantity)

    context = {
        "form": form,
        "medicine": medicine,
        "form_title": f"Adjust Stock: {medicine.name}",
        "submit_label": "Apply Stock Adjustment",
        "active_nav": "medicines",
    }
    return render(request, "clinic/medicine_stock_adjust.html", context)
