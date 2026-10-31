from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


class Patient(models.Model):
    patient_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    phone_no = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    blood_group = models.CharField(max_length=5, blank=True)

    def __str__(self):
        return self.name


class Doctor(models.Model):
    doctor_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    specialization = models.CharField(max_length=100, blank=True)
    phone_no = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)

    def __str__(self):
        return self.name


class Appointment(models.Model):
    STATUS_CHOICES = [
        ("Scheduled", "Scheduled"),
        ("Completed", "Completed"),
        ("Cancelled", "Cancelled"),
    ]

    appointment_id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="appointments"
    )
    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name="appointments"
    )
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    reason_for_visit = models.TextField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Scheduled"
    )

    class Meta:
        ordering = ["-appointment_date", "-appointment_time"]

    def __str__(self):
        return f"Appointment #{self.appointment_id}: {self.patient.name} with {self.doctor.name} on {self.appointment_date}"


class Room(models.Model):
    ROOM_TYPE_CHOICES = [
        ("General Ward", "General Ward"),
        ("Semi-Private", "Semi-Private"),
        ("Private", "Private"),
        ("ICU", "ICU"),
        ("Emergency", "Emergency"),
    ]
    STATUS_CHOICES = [
        ("Available", "Available"),
        ("Under Maintenance", "Under Maintenance"),
    ]

    room_id = models.AutoField(primary_key=True)
    room_number = models.CharField(max_length=20, unique=True)
    room_type = models.CharField(
        max_length=50, choices=ROOM_TYPE_CHOICES, default="General Ward"
    )
    bed_capacity = models.PositiveIntegerField(default=1)
    charges_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default="Available"
    )

    class Meta:
        ordering = ["room_number"]

    def __str__(self):
        return f"Room {self.room_number} ({self.room_type})"

    @property
    def active_admissions_count(self):
        return self.admissions.filter(status="Admitted").count()

    @property
    def available_beds(self):
        return max(0, self.bed_capacity - self.active_admissions_count)

    @property
    def is_full(self):
        return self.active_admissions_count >= self.bed_capacity

    @property
    def dynamic_status(self):
        if self.status == "Under Maintenance":
            return "Under Maintenance"
        if self.is_full:
            return "Occupied"
        if self.active_admissions_count > 0:
            return "Partially Occupied"
        return "Available"


class Admission(models.Model):
    STATUS_CHOICES = [
        ("Admitted", "Admitted"),
        ("Discharged", "Discharged"),
    ]

    admission_id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="admissions"
    )
    room = models.ForeignKey(
        Room, on_delete=models.CASCADE, related_name="admissions"
    )
    admission_date = models.DateField()
    discharge_date = models.DateField(null=True, blank=True)
    reason_for_admission = models.TextField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="Admitted"
    )

    class Meta:
        ordering = ["-admission_date", "-admission_id"]

    def __str__(self):
        return f"Admission #{self.admission_id}: {self.patient.name} in Room {self.room.room_number}"


class Treatment(models.Model):
    treatment_id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="treatments"
    )
    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name="treatments"
    )
    treatment_date = models.DateField()
    diagnosis = models.CharField(max_length=200)
    description = models.TextField(help_text="Detailed description of treatment or procedure")
    notes = models.TextField(blank=True, help_text="Additional doctor notes, observations, or follow-up plans")

    class Meta:
        ordering = ["-treatment_date", "-treatment_id"]

    def __str__(self):
        return f"Treatment #{self.treatment_id} for {self.patient.name} ({self.diagnosis}) on {self.treatment_date}"


class Medicine(models.Model):
    CATEGORY_CHOICES = [
        ("Tablet", "Tablet"),
        ("Capsule", "Capsule"),
        ("Syrup", "Syrup"),
        ("Injection", "Injection"),
        ("Ointment", "Ointment"),
        ("Drops", "Drops"),
        ("Inhaler", "Inhaler"),
        ("Other", "Other"),
    ]

    medicine_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150)
    category = models.CharField(
        max_length=50, choices=CATEGORY_CHOICES, default="Tablet"
    )
    manufacturer = models.CharField(max_length=150)
    batch_number = models.CharField(max_length=50, unique=True)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    min_stock_threshold = models.PositiveIntegerField(default=10)
    expiry_date = models.DateField()

    class Meta:
        ordering = ["name", "batch_number"]

    def __str__(self):
        return f"{self.name} (Batch: {self.batch_number})"

    @property
    def is_expired(self):
        return self.expiry_date < timezone.localdate()

    @property
    def is_expiring_soon(self):
        today = timezone.localdate()
        return today <= self.expiry_date <= today + timedelta(days=30)

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.min_stock_threshold

    @property
    def is_out_of_stock(self):
        return self.stock_quantity == 0

    @property
    def stock_status(self):
        if self.stock_quantity == 0:
            return "Out of Stock"
        if self.stock_quantity <= self.min_stock_threshold:
            return "Low Stock"
        return "In Stock"

    @property
    def expiry_status(self):
        if self.is_expired:
            return "Expired"
        if self.is_expiring_soon:
            return "Expiring Soon"
        return "Valid"


class MedicineStockMovement(models.Model):
    MOVEMENT_TYPES = [
        ("Stock In", "Stock In"),
        ("Adjustment", "Adjustment"),
        ("Dispensed", "Dispensed"),
        ("Initial Stock", "Initial Stock"),
    ]

    movement_id = models.AutoField(primary_key=True)
    medicine = models.ForeignKey(
        Medicine, on_delete=models.CASCADE, related_name="stock_movements"
    )
    movement_type = models.CharField(max_length=30, choices=MOVEMENT_TYPES)
    quantity_change = models.IntegerField(help_text="Positive for addition, negative for deduction")
    resulting_stock = models.PositiveIntegerField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ["-created_at", "-movement_id"]

    def __str__(self):
        return f"{self.movement_type} ({self.quantity_change:+d}) for {self.medicine.name} at {self.created_at}"


class Prescription(models.Model):
    prescription_id = models.AutoField(primary_key=True)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="prescriptions"
    )
    doctor = models.ForeignKey(
        Doctor, on_delete=models.CASCADE, related_name="prescriptions"
    )
    prescription_date = models.DateField()
    instructions = models.TextField(
        blank=True, help_text="General instructions, precautions, or dietary advice"
    )

    class Meta:
        ordering = ["-prescription_date", "-prescription_id"]

    def __str__(self):
        return f"Prescription #{self.prescription_id} for {self.patient.name} on {self.prescription_date}"

    @property
    def has_dispensable_medicines(self):
        """Returns True if there is at least one linked medicine item not yet dispensed."""
        return self.medicines.filter(medicine__isnull=False, is_dispensed=False).exists()

    @property
    def is_fully_dispensed(self):
        """Returns True if all linked medicines have been dispensed (and at least 1 exists)."""
        linked = self.medicines.filter(medicine__isnull=False)
        return linked.exists() and not linked.filter(is_dispensed=False).exists()


class PrescriptionMedicine(models.Model):
    prescription = models.ForeignKey(
        Prescription, on_delete=models.CASCADE, related_name="medicines"
    )
    medicine = models.ForeignKey(
        Medicine, on_delete=models.SET_NULL, null=True, blank=True, related_name="prescription_items"
    )
    medicine_name = models.CharField(max_length=150)
    dosage = models.CharField(max_length=100, help_text="e.g. 500mg, 1 tablet, 5ml")
    frequency = models.CharField(max_length=100, help_text="e.g. Twice daily after food, 1-0-1")
    duration = models.CharField(max_length=100, help_text="e.g. 5 days, 2 weeks")
    quantity = models.PositiveIntegerField(default=1, help_text="Quantity prescribed")
    is_dispensed = models.BooleanField(default=False)
    dispensed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.medicine_name} - {self.dosage} ({self.frequency})"


