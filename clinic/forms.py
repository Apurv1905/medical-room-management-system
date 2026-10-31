from decimal import Decimal

from django import forms
from django.utils import timezone

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


class PatientForm(forms.ModelForm):
    """Form for adding and editing patients. Extra required checks live here,
    so the database tables do not need to change."""

    GENDER_CHOICES = [
        ("", "Select gender"),
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
    ]
    BLOOD_GROUP_CHOICES = [
        ("", "Select blood group"),
        ("A+", "A+"),
        ("A-", "A-"),
        ("B+", "B+"),
        ("B-", "B-"),
        ("AB+", "AB+"),
        ("AB-", "AB-"),
        ("O+", "O+"),
        ("O-", "O-"),
    ]

    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        error_messages={"required": "Please select a gender."},
    )
    blood_group = forms.ChoiceField(
        choices=BLOOD_GROUP_CHOICES,
        error_messages={"required": "Please select a blood group."},
    )

    class Meta:
        model = Patient
        fields = ["name", "dob", "gender", "phone_no", "address", "blood_group"]
        labels = {
            "name": "Name",
            "dob": "Date of Birth",
            "gender": "Gender",
            "phone_no": "Phone Number",
            "address": "Address",
            "blood_group": "Blood Group",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "dob": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "phone_no": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        error_messages = {
            "name": {"required": "Please enter the patient name."},
            "dob": {"required": "Please enter the date of birth."},
            "phone_no": {"required": "Please enter a phone number."},
            "address": {"required": "Please enter an address."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["gender"].widget.attrs["class"] = "form-select"
        self.fields["blood_group"].widget.attrs["class"] = "form-select"
        for field_name in ["name", "dob", "gender", "phone_no", "address", "blood_group"]:
            self.fields[field_name].required = True

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError("Please enter the patient name.")
        return name

    def clean_dob(self):
        dob = self.cleaned_data.get("dob")
        if dob and dob > timezone.localdate():
            raise forms.ValidationError("Date of birth cannot be in the future.")
        return dob

    def clean_phone_no(self):
        phone = (self.cleaned_data.get("phone_no") or "").strip()
        digits = "".join(character for character in phone if character.isdigit())
        if len(digits) < 10:
            raise forms.ValidationError(
                "Please enter a valid phone number with at least 10 digits."
            )
        return phone


class DoctorForm(forms.ModelForm):
    """Form for adding and editing doctors."""

    class Meta:
        model = Doctor
        fields = ["name", "specialization", "phone_no", "email"]
        labels = {
            "name": "Doctor Name",
            "specialization": "Specialization",
            "phone_no": "Phone Number",
            "email": "Email Address",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Dr. Jane Smith"}),
            "specialization": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Cardiologist"}),
            "phone_no": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 9876543210"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "e.g. doctor@clinic.com"}),
        }
        error_messages = {
            "name": {"required": "Please enter the doctor name."},
            "specialization": {"required": "Please enter the specialization."},
            "phone_no": {"required": "Please enter a phone number."},
            "email": {
                "required": "Please enter an email address.",
                "invalid": "Please enter a valid email address.",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ["name", "specialization", "phone_no", "email"]:
            self.fields[field_name].required = True

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError("Please enter the doctor name.")
        return name

    def clean_specialization(self):
        specialization = (self.cleaned_data.get("specialization") or "").strip()
        if not specialization:
            raise forms.ValidationError("Please enter the specialization.")
        return specialization

    def clean_phone_no(self):
        phone = (self.cleaned_data.get("phone_no") or "").strip()
        digits = "".join(character for character in phone if character.isdigit())
        if len(digits) < 10:
            raise forms.ValidationError(
                "Please enter a valid phone number with at least 10 digits."
            )
        return phone

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise forms.ValidationError("Please enter an email address.")
        return email


class AppointmentForm(forms.ModelForm):
    """Form for scheduling and editing appointments with conflict detection."""

    class Meta:
        model = Appointment
        fields = [
            "patient",
            "doctor",
            "appointment_date",
            "appointment_time",
            "status",
            "reason_for_visit",
        ]
        labels = {
            "patient": "Patient",
            "doctor": "Doctor",
            "appointment_date": "Appointment Date",
            "appointment_time": "Appointment Time",
            "status": "Status",
            "reason_for_visit": "Reason for Visit",
        }
        widgets = {
            "patient": forms.Select(attrs={"class": "form-select"}),
            "doctor": forms.Select(attrs={"class": "form-select"}),
            "appointment_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "appointment_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "reason_for_visit": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Describe the reason for the appointment..."}),
        }
        error_messages = {
            "patient": {"required": "Please select a patient."},
            "doctor": {"required": "Please select a doctor."},
            "appointment_date": {"required": "Please select an appointment date."},
            "appointment_time": {"required": "Please select an appointment time."},
            "status": {"required": "Please select an appointment status."},
            "reason_for_visit": {"required": "Please provide a reason for the visit."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in [
            "patient",
            "doctor",
            "appointment_date",
            "appointment_time",
            "status",
            "reason_for_visit",
        ]:
            self.fields[field_name].required = True
        self.fields["patient"].empty_label = "Select patient"
        self.fields["doctor"].empty_label = "Select doctor"

    def clean_reason_for_visit(self):
        reason = (self.cleaned_data.get("reason_for_visit") or "").strip()
        if not reason:
            raise forms.ValidationError("Please provide a reason for the visit.")
        return reason

    def clean(self):
        cleaned_data = super().clean()
        doctor = cleaned_data.get("doctor")
        patient = cleaned_data.get("patient")
        appointment_date = cleaned_data.get("appointment_date")
        appointment_time = cleaned_data.get("appointment_time")
        status = cleaned_data.get("status")

        if not (doctor and patient and appointment_date and appointment_time):
            return cleaned_data

        # Past date/time validation for Scheduled appointments
        is_new_or_rescheduled = (
            not self.instance.pk
            or self.instance.appointment_date != appointment_date
            or self.instance.appointment_time != appointment_time
        )
        if status == "Scheduled" and is_new_or_rescheduled:
            today = timezone.localdate()
            current_time = timezone.localtime().time()
            if appointment_date < today:
                self.add_error("appointment_date", "Scheduled appointments cannot be set in the past.")
            elif appointment_date == today and appointment_time < current_time:
                self.add_error("appointment_time", "Scheduled appointments for today cannot be set to a past time.")

        # Conflict validation (skip cancelled appointments)
        if status != "Cancelled":
            # Check doctor conflict
            doctor_conflicts = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
            ).exclude(status="Cancelled")
            if self.instance.pk:
                doctor_conflicts = doctor_conflicts.exclude(pk=self.instance.pk)
            if doctor_conflicts.exists():
                self.add_error(
                    "appointment_time",
                    f"{doctor.name} already has an appointment scheduled on {appointment_date} at {appointment_time.strftime('%H:%M')}."
                )

            # Check patient conflict
            patient_conflicts = Appointment.objects.filter(
                patient=patient,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
            ).exclude(status="Cancelled")
            if self.instance.pk:
                patient_conflicts = patient_conflicts.exclude(pk=self.instance.pk)
            if patient_conflicts.exists():
                self.add_error(
                    "appointment_time",
                    f"{patient.name} already has an appointment scheduled on {appointment_date} at {appointment_time.strftime('%H:%M')}."
                )

        return cleaned_data


class RoomForm(forms.ModelForm):
    """Form for adding and editing rooms."""

    class Meta:
        model = Room
        fields = [
            "room_number",
            "room_type",
            "bed_capacity",
            "charges_per_day",
            "status",
        ]
        labels = {
            "room_number": "Room Number",
            "room_type": "Room Type",
            "bed_capacity": "Bed Capacity",
            "charges_per_day": "Charges Per Day ($)",
            "status": "Operational Status",
        }
        widgets = {
            "room_number": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "e.g. 101, ICU-2"}
            ),
            "room_type": forms.Select(attrs={"class": "form-select"}),
            "bed_capacity": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "step": 1}
            ),
            "charges_per_day": forms.NumberInput(
                attrs={"class": "form-control", "min": 0, "step": "0.01", "placeholder": "e.g. 150.00"}
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
        }
        error_messages = {
            "room_number": {"required": "Please enter a room number."},
            "room_type": {"required": "Please select a room type."},
            "bed_capacity": {"required": "Please enter bed capacity."},
            "charges_per_day": {"required": "Please enter charges per day."},
            "status": {"required": "Please select room status."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ["room_number", "room_type", "bed_capacity", "charges_per_day", "status"]:
            self.fields[field_name].required = True

    def clean_room_number(self):
        room_number = (self.cleaned_data.get("room_number") or "").strip()
        if not room_number:
            raise forms.ValidationError("Please enter a room number.")
        duplicate_query = Room.objects.filter(room_number__iexact=room_number)
        if self.instance.pk:
            duplicate_query = duplicate_query.exclude(pk=self.instance.pk)
        if duplicate_query.exists():
            raise forms.ValidationError(
                f"Room number '{room_number}' already exists. Please choose a unique room number."
            )
        return room_number

    def clean_bed_capacity(self):
        bed_capacity = self.cleaned_data.get("bed_capacity")
        if bed_capacity is None or bed_capacity < 1:
            raise forms.ValidationError("Bed capacity must be at least 1.")
        if self.instance.pk:
            active_count = self.instance.admissions.filter(status="Admitted").count()
            if bed_capacity < active_count:
                raise forms.ValidationError(
                    f"Cannot reduce capacity to {bed_capacity}. There are currently {active_count} active admitted patient(s) in this room."
                )
        return bed_capacity

    def clean_charges_per_day(self):
        charges = self.cleaned_data.get("charges_per_day")
        if charges is None or charges < 0:
            raise forms.ValidationError("Charges per day cannot be negative.")
        return charges


class AdmissionForm(forms.ModelForm):
    """Form for admitting and editing patient admissions."""

    class Meta:
        model = Admission
        fields = [
            "patient",
            "room",
            "admission_date",
            "discharge_date",
            "status",
            "reason_for_admission",
        ]
        labels = {
            "patient": "Patient",
            "room": "Room",
            "admission_date": "Admission Date",
            "discharge_date": "Discharge Date",
            "status": "Admission Status",
            "reason_for_admission": "Reason for Admission",
        }
        widgets = {
            "patient": forms.Select(attrs={"class": "form-select"}),
            "room": forms.Select(attrs={"class": "form-select"}),
            "admission_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "discharge_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "status": forms.Select(attrs={"class": "form-select"}),
            "reason_for_admission": forms.Textarea(
                attrs={"class": "form-control", "rows": 3, "placeholder": "Describe clinical reason for admission..."}
            ),
        }
        error_messages = {
            "patient": {"required": "Please select a patient."},
            "room": {"required": "Please select a room."},
            "admission_date": {"required": "Please select an admission date."},
            "status": {"required": "Please select admission status."},
            "reason_for_admission": {"required": "Please enter the reason for admission."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ["patient", "room", "admission_date", "status", "reason_for_admission"]:
            self.fields[field_name].required = True
        self.fields["discharge_date"].required = False
        self.fields["patient"].empty_label = "Select patient"
        self.fields["room"].empty_label = "Select room"
        self.fields["room"].label_from_instance = (
            lambda obj: f"Room {obj.room_number} - {obj.room_type} (${obj.charges_per_day}/day, {obj.available_beds}/{obj.bed_capacity} beds free)"
        )

    def clean_reason_for_admission(self):
        reason = (self.cleaned_data.get("reason_for_admission") or "").strip()
        if not reason:
            raise forms.ValidationError("Please enter the reason for admission.")
        return reason

    def clean(self):
        cleaned_data = super().clean()
        patient = cleaned_data.get("patient")
        room = cleaned_data.get("room")
        admission_date = cleaned_data.get("admission_date")
        discharge_date = cleaned_data.get("discharge_date")
        status = cleaned_data.get("status")

        if not (patient and room and admission_date and status):
            return cleaned_data

        # 1. Validate discharge date
        if status == "Discharged":
            if not discharge_date:
                self.add_error("discharge_date", "Please enter a discharge date when marking an admission as Discharged.")
            elif discharge_date < admission_date:
                self.add_error("discharge_date", "Discharge date cannot be earlier than the admission date.")
        elif status == "Admitted":
            if discharge_date and discharge_date < admission_date:
                self.add_error("discharge_date", "Discharge date cannot be earlier than the admission date.")

        # 2. Check if patient already has an active admission elsewhere
        if status == "Admitted":
            existing_active = Admission.objects.filter(
                patient=patient, status="Admitted"
            )
            if self.instance.pk:
                existing_active = existing_active.exclude(pk=self.instance.pk)
            if existing_active.exists():
                active_record = existing_active.first()
                self.add_error(
                    "patient",
                    f"{patient.name} is already actively admitted in Room {active_record.room.room_number}. Discharge the existing admission before creating a new one."
                )

        # 3. Check room availability & capacity
        if status == "Admitted":
            if room.status == "Under Maintenance":
                self.add_error(
                    "room",
                    f"Room {room.room_number} is currently Under Maintenance and cannot accept admissions."
                )
            else:
                active_in_room = Admission.objects.filter(
                    room=room, status="Admitted"
                )
                if self.instance.pk:
                    active_in_room = active_in_room.exclude(pk=self.instance.pk)
                if active_in_room.count() >= room.bed_capacity:
                    self.add_error(
                        "room",
                        f"Room {room.room_number} is currently full ({active_in_room.count()}/{room.bed_capacity} beds occupied). Please select another room."
                    )

        return cleaned_data


class DischargeForm(forms.Form):
    """Simple form for discharging an admitted patient."""

    discharge_date = forms.DateField(
        widget=forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        label="Discharge Date",
        error_messages={"required": "Please enter the discharge date."},
    )

    def __init__(self, admission, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.admission = admission
        self.fields["discharge_date"].initial = timezone.localdate()

    def clean_discharge_date(self):
        discharge_date = self.cleaned_data.get("discharge_date")
        if discharge_date and discharge_date < self.admission.admission_date:
            raise forms.ValidationError(
                f"Discharge date ({discharge_date}) cannot be earlier than the admission date ({self.admission.admission_date})."
            )
        return discharge_date


class TreatmentForm(forms.ModelForm):
    """Form for adding and editing treatments."""

    class Meta:
        model = Treatment
        fields = ["patient", "doctor", "treatment_date", "diagnosis", "description", "notes"]
        labels = {
            "patient": "Patient",
            "doctor": "Treating Doctor",
            "treatment_date": "Treatment Date",
            "diagnosis": "Diagnosis",
            "description": "Treatment Description",
            "notes": "Additional Notes",
        }
        widgets = {
            "patient": forms.Select(attrs={"class": "form-select"}),
            "doctor": forms.Select(attrs={"class": "form-select"}),
            "treatment_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "diagnosis": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Hypertension, Fracture of left femur"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Describe the treatment procedure, medications administered, or interventions performed..."}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Follow-up instructions, observations, or additional clinical notes..."}),
        }
        error_messages = {
            "patient": {"required": "Please select a patient."},
            "doctor": {"required": "Please select the treating doctor."},
            "treatment_date": {"required": "Please enter the treatment date."},
            "diagnosis": {"required": "Please enter a diagnosis."},
            "description": {"required": "Please describe the treatment."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ["patient", "doctor", "treatment_date", "diagnosis", "description"]:
            self.fields[field_name].required = True
        self.fields["notes"].required = False
        self.fields["patient"].empty_label = "Select patient"
        self.fields["doctor"].empty_label = "Select doctor"

    def clean_diagnosis(self):
        diagnosis = (self.cleaned_data.get("diagnosis") or "").strip()
        if not diagnosis:
            raise forms.ValidationError("Please enter a diagnosis.")
        return diagnosis

    def clean_description(self):
        description = (self.cleaned_data.get("description") or "").strip()
        if not description:
            raise forms.ValidationError("Please describe the treatment.")
        return description


class PrescriptionForm(forms.ModelForm):
    """Form for creating and editing prescriptions."""

    class Meta:
        model = Prescription
        fields = ["patient", "doctor", "prescription_date", "instructions"]
        labels = {
            "patient": "Patient",
            "doctor": "Prescribing Doctor",
            "prescription_date": "Prescription Date",
            "instructions": "General Instructions",
        }
        widgets = {
            "patient": forms.Select(attrs={"class": "form-select"}),
            "doctor": forms.Select(attrs={"class": "form-select"}),
            "prescription_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "instructions": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "e.g. Take with food. Avoid alcohol. Complete the full course."}),
        }
        error_messages = {
            "patient": {"required": "Please select a patient."},
            "doctor": {"required": "Please select the prescribing doctor."},
            "prescription_date": {"required": "Please enter the prescription date."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ["patient", "doctor", "prescription_date"]:
            self.fields[field_name].required = True
        self.fields["instructions"].required = False
        self.fields["patient"].empty_label = "Select patient"
        self.fields["doctor"].empty_label = "Select doctor"


class PrescriptionMedicineForm(forms.ModelForm):
    """Form for a single medicine row in a prescription."""

    class Meta:
        model = PrescriptionMedicine
        fields = ["medicine", "medicine_name", "dosage", "frequency", "duration", "quantity"]
        labels = {
            "medicine": "Select From Inventory (Optional)",
            "medicine_name": "Medicine Name",
            "dosage": "Dosage",
            "frequency": "Frequency",
            "duration": "Duration",
            "quantity": "Quantity",
        }
        widgets = {
            "medicine": forms.Select(attrs={"class": "form-select medicine-select"}),
            "medicine_name": forms.TextInput(attrs={"class": "form-control medicine-name-input", "placeholder": "e.g. Paracetamol"}),
            "dosage": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 500mg"}),
            "frequency": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Twice daily after meals"}),
            "duration": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 5 days"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": 1}),
        }
        error_messages = {
            "dosage": {"required": "Please enter the dosage."},
            "frequency": {"required": "Please enter the frequency."},
            "duration": {"required": "Please enter the duration."},
            "quantity": {"required": "Please enter the quantity."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["medicine"].queryset = Medicine.objects.all().order_by("name", "batch_number")
        self.fields["medicine"].empty_label = "-- Select from inventory (optional) --"
        self.fields["medicine"].required = False
        self.fields["medicine_name"].required = False

    def clean(self):
        cleaned_data = super().clean()
        medicine = cleaned_data.get("medicine")
        medicine_name = (cleaned_data.get("medicine_name") or "").strip()

        if medicine and not medicine_name:
            cleaned_data["medicine_name"] = medicine.name
        elif not medicine and not medicine_name:
            self.add_error("medicine_name", "Please enter the medicine name.")

        return cleaned_data

    def clean_quantity(self):
        qty = self.cleaned_data.get("quantity")
        if qty is None or qty < 1:
            raise forms.ValidationError("Quantity must be at least 1.")
        return qty


# Inline formset for medicines within a prescription.
# min_num=1 ensures at least one medicine row is required.
PrescriptionMedicineFormSet = forms.inlineformset_factory(
    Prescription,
    PrescriptionMedicine,
    form=PrescriptionMedicineForm,
    extra=1,
    min_num=1,
    validate_min=True,
    can_delete=True,
)


class MedicineForm(forms.ModelForm):
    """Form for adding and editing medicine inventory records."""

    class Meta:
        model = Medicine
        fields = [
            "name",
            "category",
            "manufacturer",
            "batch_number",
            "purchase_price",
            "selling_price",
            "stock_quantity",
            "min_stock_threshold",
            "expiry_date",
        ]
        labels = {
            "name": "Medicine Name",
            "category": "Category",
            "manufacturer": "Manufacturer",
            "batch_number": "Batch Number",
            "purchase_price": "Purchase Price ($)",
            "selling_price": "Selling Price ($)",
            "stock_quantity": "Available Stock Quantity",
            "min_stock_threshold": "Minimum Stock Threshold (Low-Stock Alert)",
            "expiry_date": "Expiry Date",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Amoxicillin 500mg"}),
            "category": forms.Select(attrs={"class": "form-select"}),
            "manufacturer": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Pfizer, Sun Pharma"}),
            "batch_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. AMX-2026-09"}),
            "purchase_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0.01", "placeholder": "0.00"}),
            "selling_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0.01", "placeholder": "0.00"}),
            "stock_quantity": forms.NumberInput(attrs={"class": "form-control", "min": "0", "placeholder": "0"}),
            "min_stock_threshold": forms.NumberInput(attrs={"class": "form-control", "min": "0", "placeholder": "10"}),
            "expiry_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
        }
        error_messages = {
            "name": {"required": "Please enter the medicine name."},
            "category": {"required": "Please select a category."},
            "manufacturer": {"required": "Please enter the manufacturer name."},
            "batch_number": {"required": "Please enter the batch number."},
            "purchase_price": {
                "required": "Please enter the purchase price.",
                "min_value": "Purchase price must be greater than zero.",
            },
            "selling_price": {
                "required": "Please enter the selling price.",
                "min_value": "Selling price must be greater than zero.",
            },
            "stock_quantity": {
                "required": "Please enter the available stock quantity.",
                "min_value": "Stock quantity cannot be negative.",
            },
            "min_stock_threshold": {
                "required": "Please enter the minimum stock threshold.",
                "min_value": "Minimum stock threshold cannot be negative.",
            },
            "expiry_date": {"required": "Please enter the expiry date."},
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError("Please enter the medicine name.")
        return name

    def clean_manufacturer(self):
        mfg = (self.cleaned_data.get("manufacturer") or "").strip()
        if not mfg:
            raise forms.ValidationError("Please enter the manufacturer name.")
        return mfg

    def clean_batch_number(self):
        batch = (self.cleaned_data.get("batch_number") or "").strip()
        if not batch:
            raise forms.ValidationError("Please enter the batch number.")
        qs = Medicine.objects.filter(batch_number__iexact=batch)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError(
                f"A medicine record with batch number '{batch}' already exists. Please enter a unique batch number."
            )
        return batch

    def clean_purchase_price(self):
        price = self.cleaned_data.get("purchase_price")
        if price is None or price <= 0:
            raise forms.ValidationError("Purchase price must be greater than zero.")
        return price

    def clean_selling_price(self):
        price = self.cleaned_data.get("selling_price")
        if price is None or price <= 0:
            raise forms.ValidationError("Selling price must be greater than zero.")
        return price

    def clean_stock_quantity(self):
        qty = self.cleaned_data.get("stock_quantity")
        if qty is None or qty < 0:
            raise forms.ValidationError("Stock quantity cannot be negative.")
        return qty

    def clean_min_stock_threshold(self):
        thresh = self.cleaned_data.get("min_stock_threshold")
        if thresh is None or thresh < 0:
            raise forms.ValidationError("Minimum stock threshold cannot be negative.")
        return thresh

    def clean(self):
        cleaned_data = super().clean()
        purchase_price = cleaned_data.get("purchase_price")
        selling_price = cleaned_data.get("selling_price")
        if purchase_price is not None and selling_price is not None:
            if selling_price < purchase_price:
                self.add_error(
                    "selling_price",
                    f"Selling price (${selling_price}) cannot be less than purchase price (${purchase_price})."
                )
        return cleaned_data


class StockInForm(forms.Form):
    """Form for adding newly purchased stock to an existing medicine."""

    quantity = forms.IntegerField(
        min_value=1,
        label="Stock Quantity to Add",
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 1, "placeholder": "e.g. 50"}),
        error_messages={
            "required": "Please enter the quantity to add.",
            "min_value": "Stock-in quantity must be at least 1 unit.",
        },
    )
    purchase_price = forms.DecimalField(
        required=False,
        min_value=Decimal("0.01"),
        max_digits=10,
        decimal_places=2,
        label="Updated Purchase Price ($) (optional)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Leave blank to keep existing"}),
    )
    selling_price = forms.DecimalField(
        required=False,
        min_value=Decimal("0.01"),
        max_digits=10,
        decimal_places=2,
        label="Updated Selling Price ($) (optional)",
        widget=forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "placeholder": "Leave blank to keep existing"}),
    )
    notes = forms.CharField(
        required=False,
        label="Stock-in Notes / Supplier Reference",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "e.g. Invoice #INV-2026-90, purchased from ABC Pharma"}),
    )


class StockAdjustForm(forms.Form):
    """Form for adjusting stock of an existing medicine with strict validation."""

    ACTION_CHOICES = [
        ("ADD", "Add to Current Stock (+)"),
        ("DEDUCT", "Deduct from Current Stock (-)"),
        ("SET", "Set New Exact Stock Count (=)"),
    ]
    REASON_CHOICES = [
        ("Inventory Count", "Physical Inventory Audit / Reconciliation"),
        ("Damaged", "Damaged / Broken Goods Removal"),
        ("Expired", "Expired Stock Disposal"),
        ("Data Correction", "Data Entry Error Correction"),
        ("Return to Supplier", "Return to Supplier / Manufacturer"),
        ("Other", "Other (describe in notes)"),
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        label="Adjustment Action",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    quantity = forms.IntegerField(
        min_value=0,
        label="Quantity",
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 0, "placeholder": "Number of units"}),
        error_messages={"required": "Please enter the quantity."},
    )
    reason = forms.ChoiceField(
        choices=REASON_CHOICES,
        label="Reason for Adjustment",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    notes = forms.CharField(
        required=False,
        label="Additional Remarks (optional)",
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Provide details regarding this adjustment..."}),
    )

    def __init__(self, current_stock, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_stock = current_stock

    def clean(self):
        cleaned_data = super().clean()
        action = cleaned_data.get("action")
        quantity = cleaned_data.get("quantity")

        if quantity is not None and action:
            if action == "ADD" and quantity <= 0:
                self.add_error("quantity", "Quantity to add must be at least 1 unit.")
            elif action == "DEDUCT":
                if quantity <= 0:
                    self.add_error("quantity", "Quantity to deduct must be at least 1 unit.")
                elif quantity > self.current_stock:
                    self.add_error(
                        "quantity",
                        f"Cannot deduct {quantity} units: available stock is only {self.current_stock} units. Negative stock is not allowed."
                    )
            elif action == "SET":
                if quantity < 0:
                    self.add_error("quantity", "New stock count cannot be negative.")

        return cleaned_data


