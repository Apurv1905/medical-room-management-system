from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
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


class PatientManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff", password="testpass123")
        self.patient = Patient.objects.create(
            name="Asha Rao",
            dob=date(1990, 5, 12),
            gender="Female",
            phone_no="9876543210",
            address="12 Park Street",
            blood_group="O+",
        )
        self.valid_data = {
            "name": "Ravi Kumar",
            "dob": "1988-03-04",
            "gender": "Male",
            "phone_no": "9123456789",
            "address": "44 Lake Road",
            "blood_group": "B+",
        }

    def test_guest_is_redirected_from_patient_list(self):
        response = self.client.get(reverse("patient_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_guest_cannot_create_patient_with_post(self):
        response = self.client.post(reverse("patient_add"), self.valid_data)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.assertEqual(Patient.objects.count(), 1)

    def test_logged_in_user_can_view_patient_list(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.get(reverse("patient_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Asha Rao")
        self.assertContains(response, "9876543210")

    def test_search_finds_patient_by_name_or_phone(self):
        self.client.login(username="staff", password="testpass123")
        by_name = self.client.get(reverse("patient_list"), {"q": "Asha"})
        by_phone = self.client.get(reverse("patient_list"), {"q": "987654"})
        missing = self.client.get(reverse("patient_list"), {"q": "zzzz"})
        self.assertContains(by_name, "Asha Rao")
        self.assertContains(by_phone, "Asha Rao")
        self.assertContains(missing, "No patients matched")

    def test_logged_in_user_can_add_patient(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.post(reverse("patient_add"), self.valid_data)
        patient = Patient.objects.get(name="Ravi Kumar")
        self.assertRedirects(response, reverse("patient_detail", args=[patient.pk]))
        self.assertEqual(patient.phone_no, "9123456789")

    def test_add_patient_shows_validation_errors(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.post(reverse("patient_add"), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter the patient name.")
        self.assertEqual(Patient.objects.count(), 1)

    def test_logged_in_user_can_view_patient_details(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.get(reverse("patient_detail", args=[self.patient.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Asha Rao")
        self.assertContains(response, "12 Park Street")

    def test_logged_in_user_can_edit_patient(self):
        self.client.login(username="staff", password="testpass123")
        data = self.valid_data.copy()
        data["name"] = "Asha Rao"
        data["phone_no"] = "9000000000"
        response = self.client.post(
            reverse("patient_edit", args=[self.patient.pk]),
            data,
        )
        self.assertRedirects(response, reverse("patient_detail", args=[self.patient.pk]))
        self.patient.refresh_from_db()
        self.assertEqual(self.patient.phone_no, "9000000000")

    def test_delete_page_asks_for_confirmation(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.get(reverse("patient_delete", args=[self.patient.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Delete this patient?")
        self.assertTrue(Patient.objects.filter(pk=self.patient.pk).exists())

    def test_logged_in_user_can_delete_patient_with_post(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.post(reverse("patient_delete", args=[self.patient.pk]))
        self.assertRedirects(response, reverse("patient_list"))
        self.assertFalse(Patient.objects.filter(pk=self.patient.pk).exists())

    def test_dashboard_and_admin_still_work(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('dashboard')}",
        )
        admin_response = self.client.get("/admin/login/")
        self.assertEqual(admin_response.status_code, 200)


class DoctorManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff", password="testpass123")
        self.doctor = Doctor.objects.create(
            name="Dr. Priya Sharma",
            specialization="Cardiology",
            phone_no="9876543210",
            email="priya.sharma@clinic.com",
        )
        self.valid_data = {
            "name": "Dr. Arjun Mehta",
            "specialization": "Pediatrics",
            "phone_no": "9123456789",
            "email": "arjun.mehta@clinic.com",
        }

    def test_guest_is_redirected_from_doctor_list(self):
        response = self.client.get(reverse("doctor_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_guest_cannot_create_doctor_with_post(self):
        response = self.client.post(reverse("doctor_add"), self.valid_data)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.assertEqual(Doctor.objects.count(), 1)

    def test_logged_in_user_can_view_doctor_list(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.get(reverse("doctor_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dr. Priya Sharma")
        self.assertContains(response, "Cardiology")
        self.assertContains(response, "9876543210")
        self.assertContains(response, "priya.sharma@clinic.com")

    def test_search_finds_doctor_by_name_and_specialization(self):
        self.client.login(username="staff", password="testpass123")
        by_name = self.client.get(reverse("doctor_list"), {"q": "Priya"})
        by_spec = self.client.get(reverse("doctor_list"), {"q": "Cardio"})
        missing = self.client.get(reverse("doctor_list"), {"q": "Orthopedic"})
        self.assertContains(by_name, "Dr. Priya Sharma")
        self.assertContains(by_spec, "Dr. Priya Sharma")
        self.assertContains(missing, "No doctors matched")

    def test_logged_in_user_can_add_doctor(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.post(reverse("doctor_add"), self.valid_data)
        doctor = Doctor.objects.get(name="Dr. Arjun Mehta")
        self.assertRedirects(response, reverse("doctor_detail", args=[doctor.pk]))
        self.assertEqual(doctor.specialization, "Pediatrics")
        self.assertEqual(doctor.phone_no, "9123456789")
        self.assertEqual(doctor.email, "arjun.mehta@clinic.com")

    def test_add_doctor_shows_validation_errors(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.post(reverse("doctor_add"), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter the doctor name.")
        self.assertEqual(Doctor.objects.count(), 1)

    def test_add_doctor_validates_phone_and_email(self):
        self.client.login(username="staff", password="testpass123")
        bad_data = {
            "name": "Dr. Bad Data",
            "specialization": "Dermatology",
            "phone_no": "123",
            "email": "not-an-email",
        }
        response = self.client.post(reverse("doctor_add"), bad_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "at least 10 digits")
        self.assertContains(response, "valid email address")
        self.assertEqual(Doctor.objects.count(), 1)

    def test_logged_in_user_can_view_doctor_details(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.get(reverse("doctor_detail", args=[self.doctor.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dr. Priya Sharma")
        self.assertContains(response, "Cardiology")
        self.assertContains(response, "priya.sharma@clinic.com")

    def test_logged_in_user_can_edit_doctor(self):
        self.client.login(username="staff", password="testpass123")
        data = self.valid_data.copy()
        data["name"] = "Dr. Priya Sharma"
        data["specialization"] = "Interventional Cardiology"
        data["phone_no"] = "9000000000"
        data["email"] = "priya.updated@clinic.com"
        response = self.client.post(
            reverse("doctor_edit", args=[self.doctor.pk]),
            data,
        )
        self.assertRedirects(response, reverse("doctor_detail", args=[self.doctor.pk]))
        self.doctor.refresh_from_db()
        self.assertEqual(self.doctor.specialization, "Interventional Cardiology")
        self.assertEqual(self.doctor.phone_no, "9000000000")
        self.assertEqual(self.doctor.email, "priya.updated@clinic.com")

    def test_delete_page_asks_for_confirmation(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.get(reverse("doctor_delete", args=[self.doctor.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Delete this doctor?")
        self.assertTrue(Doctor.objects.filter(pk=self.doctor.pk).exists())

    def test_logged_in_user_can_delete_doctor_with_post(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.post(reverse("doctor_delete", args=[self.doctor.pk]))
        self.assertRedirects(response, reverse("doctor_list"))
        self.assertFalse(Doctor.objects.filter(pk=self.doctor.pk).exists())

    def test_dashboard_reflects_doctor_count_and_link(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total Doctors")
        self.assertContains(response, reverse("doctor_list"))

    def test_sidebar_includes_active_doctor_navigation(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.get(reverse("doctor_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("doctor_list"))
        self.assertContains(response, 'class="nav-link active"')


class AppointmentManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff", password="testpass123")
        self.patient = Patient.objects.create(
            name="Asha Rao",
            dob=date(1990, 5, 12),
            gender="Female",
            phone_no="9876543210",
            address="12 Park Street",
            blood_group="O+",
        )
        self.patient2 = Patient.objects.create(
            name="Ravi Kumar",
            dob=date(1988, 3, 4),
            gender="Male",
            phone_no="9123456789",
            address="44 Lake Road",
            blood_group="B+",
        )
        self.doctor = Doctor.objects.create(
            name="Dr. Priya Sharma",
            specialization="Cardiology",
            phone_no="9876543210",
            email="priya.sharma@clinic.com",
        )
        self.doctor2 = Doctor.objects.create(
            name="Dr. Arjun Mehta",
            specialization="Pediatrics",
            phone_no="9123456789",
            email="arjun.mehta@clinic.com",
        )
        self.future_date = timezone.localdate() + timedelta(days=2)
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=self.future_date,
            appointment_time=time(10, 30),
            reason_for_visit="Routine cardiac checkup",
            status="Scheduled",
        )
        self.valid_data = {
            "patient": self.patient2.pk,
            "doctor": self.doctor2.pk,
            "appointment_date": (timezone.localdate() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "appointment_time": "14:00",
            "reason_for_visit": "Fever and cold evaluation",
            "status": "Scheduled",
        }

    def test_guest_is_redirected_from_appointment_list(self):
        response = self.client.get(reverse("appointment_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_guest_cannot_create_appointment_with_post(self):
        response = self.client.post(reverse("appointment_add"), self.valid_data)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_logged_in_user_can_view_appointment_list(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.get(reverse("appointment_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Asha Rao")
        self.assertContains(response, "Dr. Priya Sharma")
        self.assertContains(response, "10:30")

    def test_search_finds_appointment_by_patient_doctor_or_reason(self):
        self.client.login(username="staff", password="testpass123")
        by_patient = self.client.get(reverse("appointment_list"), {"q": "Asha"})
        by_doctor = self.client.get(reverse("appointment_list"), {"q": "Priya"})
        by_reason = self.client.get(reverse("appointment_list"), {"q": "cardiac"})
        missing = self.client.get(reverse("appointment_list"), {"q": "nonexistent"})

        self.assertContains(by_patient, "Asha Rao")
        self.assertContains(by_doctor, "Dr. Priya Sharma")
        self.assertContains(by_reason, "Asha Rao")
        self.assertContains(missing, "No appointments matched")

    def test_filters_by_status_doctor_and_date(self):
        self.client.login(username="staff", password="testpass123")
        by_status = self.client.get(reverse("appointment_list"), {"status": "Scheduled"})
        by_wrong_status = self.client.get(reverse("appointment_list"), {"status": "Completed"})
        by_doctor = self.client.get(reverse("appointment_list"), {"doctor": self.doctor.pk})
        by_date = self.client.get(reverse("appointment_list"), {"date": self.future_date.strftime("%Y-%m-%d")})

        self.assertContains(by_status, "Asha Rao")
        self.assertNotContains(by_wrong_status, "Asha Rao")
        self.assertContains(by_doctor, "Asha Rao")
        self.assertContains(by_date, "Asha Rao")

    def test_logged_in_user_can_schedule_appointment(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.post(reverse("appointment_add"), self.valid_data)
        appointment = Appointment.objects.get(reason_for_visit="Fever and cold evaluation")
        self.assertRedirects(response, reverse("appointment_detail", args=[appointment.pk]))
        self.assertEqual(appointment.patient, self.patient2)
        self.assertEqual(appointment.doctor, self.doctor2)

    def test_add_appointment_validation_errors_for_empty_fields(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.post(reverse("appointment_add"), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please select a patient.")
        self.assertContains(response, "Please select a doctor.")
        self.assertEqual(Appointment.objects.count(), 1)

    def test_add_appointment_scheduled_in_past_fails(self):
        self.client.login(username="staff", password="testpass123")
        past_data = self.valid_data.copy()
        past_data["appointment_date"] = (timezone.localdate() - timedelta(days=1)).strftime("%Y-%m-%d")
        response = self.client.post(reverse("appointment_add"), past_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Scheduled appointments cannot be set in the past.")
        self.assertEqual(Appointment.objects.count(), 1)

    def test_conflicting_appointment_for_doctor_is_prevented(self):
        self.client.login(username="staff", password="testpass123")
        conflict_data = {
            "patient": self.patient2.pk,
            "doctor": self.doctor.pk,
            "appointment_date": self.future_date.strftime("%Y-%m-%d"),
            "appointment_time": "10:30",
            "reason_for_visit": "Another consultation",
            "status": "Scheduled",
        }
        response = self.client.post(reverse("appointment_add"), conflict_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already has an appointment scheduled")
        self.assertEqual(Appointment.objects.count(), 1)

    def test_conflicting_appointment_for_patient_is_prevented(self):
        self.client.login(username="staff", password="testpass123")
        conflict_data = {
            "patient": self.patient.pk,
            "doctor": self.doctor2.pk,
            "appointment_date": self.future_date.strftime("%Y-%m-%d"),
            "appointment_time": "10:30",
            "reason_for_visit": "Overlapping consultation",
            "status": "Scheduled",
        }
        response = self.client.post(reverse("appointment_add"), conflict_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already has an appointment scheduled")
        self.assertEqual(Appointment.objects.count(), 1)

    def test_cancelled_appointment_allows_rescheduling_same_slot(self):
        self.client.login(username="staff", password="testpass123")
        self.appointment.status = "Cancelled"
        self.appointment.save()

        new_data = {
            "patient": self.patient2.pk,
            "doctor": self.doctor.pk,
            "appointment_date": self.future_date.strftime("%Y-%m-%d"),
            "appointment_time": "10:30",
            "reason_for_visit": "Replaced slot consultation",
            "status": "Scheduled",
        }
        response = self.client.post(reverse("appointment_add"), new_data)
        new_appt = Appointment.objects.get(reason_for_visit="Replaced slot consultation")
        self.assertRedirects(response, reverse("appointment_detail", args=[new_appt.pk]))

    def test_logged_in_user_can_view_appointment_details(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.get(reverse("appointment_detail", args=[self.appointment.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Routine cardiac checkup")
        self.assertContains(response, "Asha Rao")
        self.assertContains(response, "Dr. Priya Sharma")

    def test_logged_in_user_can_edit_appointment(self):
        self.client.login(username="staff", password="testpass123")
        data = {
            "patient": self.patient.pk,
            "doctor": self.doctor.pk,
            "appointment_date": self.future_date.strftime("%Y-%m-%d"),
            "appointment_time": "10:30",
            "reason_for_visit": "Updated reason: ECG and blood pressure review",
            "status": "Completed",
        }
        response = self.client.post(
            reverse("appointment_edit", args=[self.appointment.pk]),
            data,
        )
        self.assertRedirects(response, reverse("appointment_detail", args=[self.appointment.pk]))
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, "Completed")
        self.assertEqual(self.appointment.reason_for_visit, "Updated reason: ECG and blood pressure review")

    def test_delete_page_asks_for_confirmation(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.get(reverse("appointment_delete", args=[self.appointment.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Delete this appointment?")
        self.assertTrue(Appointment.objects.filter(pk=self.appointment.pk).exists())

    def test_logged_in_user_can_delete_appointment_with_post(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.post(reverse("appointment_delete", args=[self.appointment.pk]))
        self.assertRedirects(response, reverse("appointment_list"))
        self.assertFalse(Appointment.objects.filter(pk=self.appointment.pk).exists())

    def test_dashboard_reflects_appointment_count_and_link(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total Appointments")
        self.assertContains(response, reverse("appointment_list"))

    def test_sidebar_includes_active_appointment_navigation(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.get(reverse("appointment_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("appointment_list"))
        self.assertContains(response, 'class="nav-link active"')


class RoomManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff", password="testpass123")
        self.room = Room.objects.create(
            room_number="101",
            room_type="General Ward",
            bed_capacity=2,
            charges_per_day=Decimal("150.00"),
            status="Available",
        )
        self.valid_data = {
            "room_number": "ICU-1",
            "room_type": "ICU",
            "bed_capacity": 1,
            "charges_per_day": "500.00",
            "status": "Available",
        }

    def test_guest_redirected_from_room_list(self):
        response = self.client.get(reverse("room_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_guest_cannot_create_room_with_post(self):
        response = self.client.post(reverse("room_add"), self.valid_data)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.assertEqual(Room.objects.count(), 1)

    def test_logged_in_user_can_view_room_list(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.get(reverse("room_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Room 101")
        self.assertContains(response, "General Ward")
        self.assertContains(response, "$150.00")

    def test_search_and_filters_work_for_rooms(self):
        self.client.login(username="staff", password="testpass123")
        Room.objects.create(
            room_number="202",
            room_type="Private",
            bed_capacity=1,
            charges_per_day=Decimal("300.00"),
            status="Under Maintenance",
        )

        by_number = self.client.get(reverse("room_list"), {"q": "101"})
        self.assertContains(by_number, "Room 101")
        self.assertNotContains(by_number, "Room 202")

        by_type = self.client.get(reverse("room_list"), {"type": "Private"})
        self.assertContains(by_type, "Room 202")
        self.assertNotContains(by_type, "Room 101")

        by_status = self.client.get(reverse("room_list"), {"status": "Under Maintenance"})
        self.assertContains(by_status, "Room 202")
        self.assertNotContains(by_status, "Room 101")

    def test_logged_in_user_can_add_room(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.post(reverse("room_add"), self.valid_data)
        room = Room.objects.get(room_number="ICU-1")
        self.assertRedirects(response, reverse("room_detail", args=[room.pk]))
        self.assertEqual(room.bed_capacity, 1)
        self.assertEqual(room.charges_per_day, Decimal("500.00"))

    def test_duplicate_room_number_is_prevented(self):
        self.client.login(username="staff", password="testpass123")
        duplicate_data = self.valid_data.copy()
        duplicate_data["room_number"] = "101"
        response = self.client.post(reverse("room_add"), duplicate_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")
        self.assertEqual(Room.objects.count(), 1)

    def test_bed_capacity_and_charges_validation(self):
        self.client.login(username="staff", password="testpass123")
        bad_data = self.valid_data.copy()
        bad_data["bed_capacity"] = 0
        bad_data["charges_per_day"] = -50
        response = self.client.post(reverse("room_add"), bad_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Bed capacity must be at least 1")
        self.assertContains(response, "Charges per day cannot be negative")

    def test_logged_in_user_can_edit_room(self):
        self.client.login(username="staff", password="testpass123")
        data = {
            "room_number": "101-Renovated",
            "room_type": "Semi-Private",
            "bed_capacity": 3,
            "charges_per_day": "220.00",
            "status": "Available",
        }
        response = self.client.post(reverse("room_edit", args=[self.room.pk]), data)
        self.assertRedirects(response, reverse("room_detail", args=[self.room.pk]))
        self.room.refresh_from_db()
        self.assertEqual(self.room.room_number, "101-Renovated")
        self.assertEqual(self.room.bed_capacity, 3)

    def test_cannot_delete_room_with_active_admissions(self):
        self.client.login(username="staff", password="testpass123")
        patient = Patient.objects.create(name="Deepak Joshi")
        Admission.objects.create(
            patient=patient,
            room=self.room,
            admission_date=timezone.localdate(),
            status="Admitted",
            reason_for_admission="Post-surgery recovery",
        )
        response = self.client.post(reverse("room_delete", args=[self.room.pk]))
        self.assertRedirects(response, reverse("room_detail", args=[self.room.pk]))
        self.assertTrue(Room.objects.filter(pk=self.room.pk).exists())

    def test_can_delete_room_without_active_admissions(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.post(reverse("room_delete", args=[self.room.pk]))
        self.assertRedirects(response, reverse("room_list"))
        self.assertFalse(Room.objects.filter(pk=self.room.pk).exists())

    def test_dashboard_reflects_room_count_and_link(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total Rooms")
        self.assertContains(response, reverse("room_list"))

    def test_sidebar_includes_active_room_navigation(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.get(reverse("room_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("room_list"))
        self.assertContains(response, 'class="nav-link active"')


class AdmissionManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff", password="testpass123")
        self.patient = Patient.objects.create(
            name="Deepak Joshi",
            dob=date(1985, 7, 20),
            gender="Male",
            phone_no="9876500000",
            blood_group="A+",
        )
        self.patient2 = Patient.objects.create(
            name="Meena Kumari",
            dob=date(1992, 11, 15),
            gender="Female",
            phone_no="9876511111",
            blood_group="O-",
        )
        self.room = Room.objects.create(
            room_number="101",
            room_type="General Ward",
            bed_capacity=1,
            charges_per_day=Decimal("150.00"),
            status="Available",
        )
        self.room_maintenance = Room.objects.create(
            room_number="202",
            room_type="Private",
            bed_capacity=1,
            charges_per_day=Decimal("300.00"),
            status="Under Maintenance",
        )
        self.valid_data = {
            "patient": self.patient.pk,
            "room": self.room.pk,
            "admission_date": timezone.localdate().strftime("%Y-%m-%d"),
            "discharge_date": "",
            "status": "Admitted",
            "reason_for_admission": "Severe pneumonia and oxygen requirement",
        }

    def test_guest_redirected_from_admission_list(self):
        response = self.client.get(reverse("admission_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_guest_cannot_admit_patient_with_post(self):
        response = self.client.post(reverse("admission_add"), self.valid_data)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.assertEqual(Admission.objects.count(), 0)

    def test_logged_in_user_can_view_admission_list(self):
        self.client.login(username="staff", password="testpass123")
        Admission.objects.create(
            patient=self.patient,
            room=self.room,
            admission_date=timezone.localdate(),
            status="Admitted",
            reason_for_admission="Observation",
        )
        response = self.client.get(reverse("admission_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Deepak Joshi")
        self.assertContains(response, "Room 101")
        self.assertContains(response, "Admitted")

    def test_logged_in_user_can_admit_patient(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.post(reverse("admission_add"), self.valid_data)
        admission = Admission.objects.get(patient=self.patient)
        self.assertRedirects(response, reverse("admission_detail", args=[admission.pk]))
        self.assertEqual(admission.status, "Admitted")
        self.assertEqual(self.room.active_admissions_count, 1)
        self.assertTrue(self.room.is_full)

    def test_cannot_admit_patient_to_full_room(self):
        self.client.login(username="staff", password="testpass123")
        # Admit first patient filling capacity (bed_capacity = 1)
        Admission.objects.create(
            patient=self.patient,
            room=self.room,
            admission_date=timezone.localdate(),
            status="Admitted",
            reason_for_admission="First patient",
        )
        # Attempt to admit second patient to full room
        full_data = self.valid_data.copy()
        full_data["patient"] = self.patient2.pk
        response = self.client.post(reverse("admission_add"), full_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "currently full")
        self.assertEqual(Admission.objects.count(), 1)

    def test_cannot_admit_patient_to_maintenance_room(self):
        self.client.login(username="staff", password="testpass123")
        data = self.valid_data.copy()
        data["room"] = self.room_maintenance.pk
        response = self.client.post(reverse("admission_add"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Under Maintenance")
        self.assertEqual(Admission.objects.count(), 0)

    def test_cannot_admit_already_admitted_patient(self):
        self.client.login(username="staff", password="testpass123")
        # Admit patient to Room 1
        room_extra = Room.objects.create(
            room_number="303",
            bed_capacity=2,
            charges_per_day=Decimal("100.00"),
            status="Available",
        )
        Admission.objects.create(
            patient=self.patient,
            room=self.room,
            admission_date=timezone.localdate(),
            status="Admitted",
            reason_for_admission="Admitted already",
        )
        # Attempt to admit same patient to Room 303
        data = self.valid_data.copy()
        data["room"] = room_extra.pk
        response = self.client.post(reverse("admission_add"), data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already actively admitted")
        self.assertEqual(Admission.objects.count(), 1)

    def test_discharge_date_cannot_be_before_admission_date(self):
        self.client.login(username="staff", password="testpass123")
        bad_data = self.valid_data.copy()
        bad_data["admission_date"] = "2026-10-15"
        bad_data["discharge_date"] = "2026-10-10"
        bad_data["status"] = "Discharged"
        response = self.client.post(reverse("admission_add"), bad_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cannot be earlier than")

    def test_logged_in_user_can_discharge_patient(self):
        self.client.login(username="staff", password="testpass123")
        admission = Admission.objects.create(
            patient=self.patient,
            room=self.room,
            admission_date=timezone.localdate() - timedelta(days=3),
            status="Admitted",
            reason_for_admission="Flu",
        )
        self.assertTrue(self.room.is_full)

        # POST discharge confirmation
        discharge_data = {
            "discharge_date": timezone.localdate().strftime("%Y-%m-%d"),
        }
        response = self.client.post(reverse("admission_discharge", args=[admission.pk]), discharge_data)
        self.assertRedirects(response, reverse("admission_detail", args=[admission.pk]))
        admission.refresh_from_db()
        self.assertEqual(admission.status, "Discharged")
        self.assertEqual(admission.discharge_date, timezone.localdate())

        # Now bed is freed up
        self.assertEqual(self.room.active_admissions_count, 0)
        self.assertEqual(self.room.available_beds, 1)

    def test_logged_in_user_can_view_admission_details(self):
        self.client.login(username="staff", password="testpass123")
        admission = Admission.objects.create(
            patient=self.patient,
            room=self.room,
            admission_date=timezone.localdate() - timedelta(days=2),
            status="Admitted",
            reason_for_admission="Appendicitis observation",
        )
        response = self.client.get(reverse("admission_detail", args=[admission.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Appendicitis observation")
        self.assertContains(response, "Deepak Joshi")
        self.assertContains(response, "Room 101")
        self.assertContains(response, "$150.00")

    def test_logged_in_user_can_edit_admission(self):
        self.client.login(username="staff", password="testpass123")
        admission = Admission.objects.create(
            patient=self.patient,
            room=self.room,
            admission_date=timezone.localdate(),
            status="Admitted",
            reason_for_admission="Original reason",
        )
        edit_data = {
            "patient": self.patient.pk,
            "room": self.room.pk,
            "admission_date": timezone.localdate().strftime("%Y-%m-%d"),
            "discharge_date": "",
            "status": "Admitted",
            "reason_for_admission": "Updated clinical reason after diagnosis",
        }
        response = self.client.post(reverse("admission_edit", args=[admission.pk]), edit_data)
        self.assertRedirects(response, reverse("admission_detail", args=[admission.pk]))
        admission.refresh_from_db()
        self.assertEqual(admission.reason_for_admission, "Updated clinical reason after diagnosis")

    def test_logged_in_user_can_delete_admission_with_post(self):
        self.client.login(username="staff", password="testpass123")
        admission = Admission.objects.create(
            patient=self.patient,
            room=self.room,
            admission_date=timezone.localdate(),
            status="Admitted",
            reason_for_admission="To be deleted",
        )
        response = self.client.post(reverse("admission_delete", args=[admission.pk]))
        self.assertRedirects(response, reverse("admission_list"))
        self.assertFalse(Admission.objects.filter(pk=admission.pk).exists())

    def test_dashboard_reflects_admission_count_and_link(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Total Admissions")
        self.assertContains(response, reverse("admission_list"))

    def test_sidebar_includes_active_admission_navigation(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.get(reverse("admission_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("admission_list"))
        self.assertContains(response, 'class="nav-link active"')


class MedicineInventoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="staff", password="testpass123")
        self.patient = Patient.objects.create(
            name="Ramesh Patel",
            dob=date(1985, 4, 15),
            gender="Male",
            phone_no="9876501234",
            address="50 MG Road, Bangalore",
            blood_group="O+",
        )
        self.doctor = Doctor.objects.create(
            name="Dr. Anita Desai",
            specialization="General Medicine",
            phone_no="9876505678",
            email="anita.desai@clinic.com",
        )
        self.today = timezone.localdate()
        self.medicine = Medicine.objects.create(
            name="Amoxicillin 500mg",
            category="Capsule",
            manufacturer="Sun Pharma",
            batch_number="AMX-2026-01",
            purchase_price=Decimal("12.50"),
            selling_price=Decimal("18.00"),
            stock_quantity=50,
            min_stock_threshold=15,
            expiry_date=self.today + timedelta(days=180),
        )
        self.valid_data = {
            "name": "Paracetamol 650mg",
            "category": "Tablet",
            "manufacturer": "Cipla",
            "batch_number": "PCM-2026-99",
            "purchase_price": "5.00",
            "selling_price": "8.50",
            "stock_quantity": "100",
            "min_stock_threshold": "20",
            "expiry_date": (self.today + timedelta(days=365)).strftime("%Y-%m-%d"),
        }

    def test_guest_redirected_from_medicine_list(self):
        response = self.client.get(reverse("medicine_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_guest_cannot_create_medicine_with_post(self):
        response = self.client.post(reverse("medicine_add"), self.valid_data)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
        self.assertEqual(Medicine.objects.count(), 1)

    def test_logged_in_user_can_view_medicine_list(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.get(reverse("medicine_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Amoxicillin 500mg")
        self.assertContains(response, "AMX-2026-01")
        self.assertContains(response, "Sun Pharma")
        self.assertContains(response, "50")

    def test_medicine_search_by_name_and_batch_number(self):
        self.client.login(username="staff", password="testpass123")
        by_name = self.client.get(reverse("medicine_list"), {"q": "Amoxicillin"})
        by_batch = self.client.get(reverse("medicine_list"), {"q": "AMX-2026"})
        missing = self.client.get(reverse("medicine_list"), {"q": "NonexistentMedicine"})

        self.assertContains(by_name, "Amoxicillin 500mg")
        self.assertContains(by_batch, "AMX-2026-01")
        self.assertContains(missing, "No medicines matched")

    def test_medicine_filter_by_category(self):
        self.client.login(username="staff", password="testpass123")
        Medicine.objects.create(
            name="Cough Syrup 100ml",
            category="Syrup",
            manufacturer="Dabur",
            batch_number="SYR-2026-10",
            purchase_price=Decimal("45.00"),
            selling_price=Decimal("60.00"),
            stock_quantity=30,
            min_stock_threshold=10,
            expiry_date=self.today + timedelta(days=120),
        )

        capsule_res = self.client.get(reverse("medicine_list"), {"category": "Capsule"})
        syrup_res = self.client.get(reverse("medicine_list"), {"category": "Syrup"})

        self.assertContains(capsule_res, "Amoxicillin 500mg")
        self.assertNotContains(capsule_res, "Cough Syrup 100ml")
        self.assertContains(syrup_res, "Cough Syrup 100ml")
        self.assertNotContains(syrup_res, "Amoxicillin 500mg")

    def test_medicine_filter_by_low_stock(self):
        self.client.login(username="staff", password="testpass123")
        low_med = Medicine.objects.create(
            name="Low Stock Medicine",
            category="Tablet",
            manufacturer="TestLab",
            batch_number="LOW-001",
            purchase_price=Decimal("10.00"),
            selling_price=Decimal("15.00"),
            stock_quantity=4,
            min_stock_threshold=10,
            expiry_date=self.today + timedelta(days=90),
        )
        out_med = Medicine.objects.create(
            name="Out of Stock Medicine",
            category="Tablet",
            manufacturer="TestLab",
            batch_number="OUT-001",
            purchase_price=Decimal("10.00"),
            selling_price=Decimal("15.00"),
            stock_quantity=0,
            min_stock_threshold=10,
            expiry_date=self.today + timedelta(days=90),
        )

        res_low = self.client.get(reverse("medicine_list"), {"status": "low_stock"})
        self.assertContains(res_low, "Low Stock Medicine")
        self.assertNotContains(res_low, "Amoxicillin 500mg")

        res_out = self.client.get(reverse("medicine_list"), {"status": "out_of_stock"})
        self.assertContains(res_out, "Out of Stock Medicine")
        self.assertNotContains(res_out, "Low Stock Medicine")

    def test_medicine_filter_by_expiry_status(self):
        self.client.login(username="staff", password="testpass123")
        expired_med = Medicine.objects.create(
            name="Expired Aspirin",
            category="Tablet",
            manufacturer="OldPharma",
            batch_number="EXP-999",
            purchase_price=Decimal("2.00"),
            selling_price=Decimal("4.00"),
            stock_quantity=20,
            min_stock_threshold=5,
            expiry_date=self.today - timedelta(days=10),
        )
        soon_med = Medicine.objects.create(
            name="Soon Expiring Vitamin C",
            category="Tablet",
            manufacturer="NutriCo",
            batch_number="SOON-888",
            purchase_price=Decimal("8.00"),
            selling_price=Decimal("12.00"),
            stock_quantity=25,
            min_stock_threshold=5,
            expiry_date=self.today + timedelta(days=15),
        )

        expired_res = self.client.get(reverse("medicine_list"), {"status": "expired"})
        self.assertContains(expired_res, "Expired Aspirin")
        self.assertNotContains(expired_res, "Amoxicillin 500mg")

        soon_res = self.client.get(reverse("medicine_list"), {"status": "expiring_soon"})
        self.assertContains(soon_res, "Soon Expiring Vitamin C")
        self.assertNotContains(soon_res, "Amoxicillin 500mg")

    def test_logged_in_user_can_add_medicine(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.post(reverse("medicine_add"), self.valid_data)
        pcm = Medicine.objects.get(batch_number="PCM-2026-99")
        self.assertRedirects(response, reverse("medicine_detail", args=[pcm.pk]))
        self.assertEqual(pcm.stock_quantity, 100)
        self.assertEqual(pcm.selling_price, Decimal("8.50"))
        # Verify initial stock movement log was recorded
        movement = pcm.stock_movements.first()
        self.assertIsNotNone(movement)
        self.assertEqual(movement.movement_type, "Initial Stock")
        self.assertEqual(movement.quantity_change, 100)

    def test_add_medicine_validation_negative_stock_and_price_prevented(self):
        self.client.login(username="staff", password="testpass123")
        bad_data = self.valid_data.copy()
        bad_data["stock_quantity"] = "-5"
        bad_data["purchase_price"] = "-2.00"
        bad_data["selling_price"] = "-4.00"
        response = self.client.post(reverse("medicine_add"), bad_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stock quantity cannot be negative")
        self.assertContains(response, "greater than zero")
        self.assertEqual(Medicine.objects.count(), 1)

    def test_add_medicine_selling_price_less_than_purchase_price_prevented(self):
        self.client.login(username="staff", password="testpass123")
        loss_data = self.valid_data.copy()
        loss_data["purchase_price"] = "20.00"
        loss_data["selling_price"] = "15.00"
        response = self.client.post(reverse("medicine_add"), loss_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "cannot be less than purchase price")
        self.assertEqual(Medicine.objects.count(), 1)

    def test_duplicate_batch_number_prevented(self):
        self.client.login(username="staff", password="testpass123")
        duplicate_data = self.valid_data.copy()
        duplicate_data["batch_number"] = "AMX-2026-01"  # already belongs to Amoxicillin
        response = self.client.post(reverse("medicine_add"), duplicate_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")
        self.assertEqual(Medicine.objects.count(), 1)

    def test_logged_in_user_can_view_medicine_details(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.get(reverse("medicine_detail", args=[self.medicine.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Amoxicillin 500mg")
        self.assertContains(response, "AMX-2026-01")
        self.assertContains(response, "Sun Pharma")
        self.assertContains(response, "$12.50")
        self.assertContains(response, "$18.00")

    def test_logged_in_user_can_edit_medicine(self):
        self.client.login(username="staff", password="testpass123")
        data = {
            "name": "Amoxicillin & Clavulanate 625mg",
            "category": "Tablet",
            "manufacturer": "Sun Pharma Labs",
            "batch_number": "AMX-2026-01",
            "purchase_price": "14.00",
            "selling_price": "22.00",
            "stock_quantity": "55",
            "min_stock_threshold": "10",
            "expiry_date": (self.today + timedelta(days=200)).strftime("%Y-%m-%d"),
        }
        response = self.client.post(reverse("medicine_edit", args=[self.medicine.pk]), data)
        self.assertRedirects(response, reverse("medicine_detail", args=[self.medicine.pk]))
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.name, "Amoxicillin & Clavulanate 625mg")
        self.assertEqual(self.medicine.stock_quantity, 55)
        # Check stock movement adjustment was recorded
        adjustment = self.medicine.stock_movements.filter(movement_type="Adjustment").first()
        self.assertIsNotNone(adjustment)
        self.assertEqual(adjustment.quantity_change, 5)

    def test_logged_in_user_can_delete_medicine_with_post(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.post(reverse("medicine_delete", args=[self.medicine.pk]))
        self.assertRedirects(response, reverse("medicine_list"))
        self.assertFalse(Medicine.objects.filter(pk=self.medicine.pk).exists())

    def test_stock_in_increases_stock_and_records_movement(self):
        self.client.login(username="staff", password="testpass123")
        stock_in_data = {
            "quantity": 30,
            "purchase_price": "13.00",
            "selling_price": "19.00",
            "notes": "Invoice #INV-2026-042 from Global Supplier",
        }
        response = self.client.post(reverse("medicine_stock_in", args=[self.medicine.pk]), stock_in_data)
        self.assertRedirects(response, reverse("medicine_detail", args=[self.medicine.pk]))
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.stock_quantity, 80)
        self.assertEqual(self.medicine.purchase_price, Decimal("13.00"))
        self.assertEqual(self.medicine.selling_price, Decimal("19.00"))

        movement = self.medicine.stock_movements.filter(movement_type="Stock In").first()
        self.assertIsNotNone(movement)
        self.assertEqual(movement.quantity_change, 30)
        self.assertEqual(movement.resulting_stock, 80)
        self.assertIn("INV-2026-042", movement.notes)

    def test_stock_in_invalid_quantity_prevented(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.post(reverse("medicine_stock_in", args=[self.medicine.pk]), {"quantity": 0})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "must be at least 1")
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.stock_quantity, 50)

    def test_stock_adjustment_add_and_set(self):
        self.client.login(username="staff", password="testpass123")
        # Test Set exact count
        set_data = {
            "action": "SET",
            "quantity": 42,
            "reason": "Inventory Count",
            "notes": "Physical audit count",
        }
        response = self.client.post(reverse("medicine_stock_adjust", args=[self.medicine.pk]), set_data)
        self.assertRedirects(response, reverse("medicine_detail", args=[self.medicine.pk]))
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.stock_quantity, 42)

    def test_stock_adjustment_deduct_cannot_exceed_available_stock(self):
        self.client.login(username="staff", password="testpass123")
        excess_deduct = {
            "action": "DEDUCT",
            "quantity": 999,  # available is only 50
            "reason": "Damaged",
            "notes": "Attempting excess deduction",
        }
        response = self.client.post(reverse("medicine_stock_adjust", args=[self.medicine.pk]), excess_deduct)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Negative stock is not allowed")
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.stock_quantity, 50)

    def test_prescription_medicine_linked_to_inventory_does_not_deduct_stock_automatically(self):
        self.client.login(username="staff", password="testpass123")
        # Create prescription linking to Amoxicillin (stock=50)
        prescription = Prescription.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            prescription_date=self.today,
            instructions="Take after food",
        )
        PrescriptionMedicine.objects.create(
            prescription=prescription,
            medicine=self.medicine,
            medicine_name=self.medicine.name,
            dosage="500mg",
            frequency="Three times daily",
            duration="5 days",
            quantity=15,
        )

        # Stock must NOT be deducted automatically upon prescription creation!
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.stock_quantity, 50)

        # View detail page and verify dispense button is visible
        detail_res = self.client.get(reverse("prescription_detail", args=[prescription.pk]))
        self.assertEqual(detail_res.status_code, 200)
        self.assertContains(detail_res, "Dispense Medicines & Deduct Stock")

    def test_prescription_dispense_workflow_deducts_stock_and_marks_dispensed(self):
        self.client.login(username="staff", password="testpass123")
        prescription = Prescription.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            prescription_date=self.today,
        )
        item = PrescriptionMedicine.objects.create(
            prescription=prescription,
            medicine=self.medicine,
            medicine_name=self.medicine.name,
            dosage="500mg",
            frequency="TDS",
            duration="7 days",
            quantity=21,
        )
        self.assertFalse(item.is_dispensed)

        # Explicit dispense POST
        response = self.client.post(reverse("prescription_dispense", args=[prescription.pk]))
        self.assertRedirects(response, reverse("prescription_detail", args=[prescription.pk]))

        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.stock_quantity, 29)  # 50 - 21 = 29
        item.refresh_from_db()
        self.assertTrue(item.is_dispensed)
        self.assertIsNotNone(item.dispensed_at)

        # Verify stock movement recorded
        dispense_movement = self.medicine.stock_movements.filter(movement_type="Dispensed").first()
        self.assertIsNotNone(dispense_movement)
        self.assertEqual(dispense_movement.quantity_change, -21)
        self.assertEqual(dispense_movement.resulting_stock, 29)

    def test_prescription_dispense_prevented_when_insufficient_stock(self):
        self.client.login(username="staff", password="testpass123")
        prescription = Prescription.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            prescription_date=self.today,
        )
        item = PrescriptionMedicine.objects.create(
            prescription=prescription,
            medicine=self.medicine,
            medicine_name=self.medicine.name,
            dosage="500mg",
            frequency="TDS",
            duration="30 days",
            quantity=100,  # only 50 in stock
        )

        response = self.client.post(reverse("prescription_dispense", args=[prescription.pk]))
        self.assertRedirects(response, reverse("prescription_detail", args=[prescription.pk]))

        # Stock must remain unchanged and item must not be marked dispensed
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.stock_quantity, 50)
        item.refresh_from_db()
        self.assertFalse(item.is_dispensed)

    def test_prescription_dispense_prevented_when_expired(self):
        self.client.login(username="staff", password="testpass123")
        expired_med = Medicine.objects.create(
            name="Expired Antibiotic",
            category="Tablet",
            manufacturer="ExpiredCo",
            batch_number="EXP-001",
            purchase_price=Decimal("10.00"),
            selling_price=Decimal("15.00"),
            stock_quantity=40,
            min_stock_threshold=5,
            expiry_date=self.today - timedelta(days=5),
        )
        prescription = Prescription.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            prescription_date=self.today,
        )
        item = PrescriptionMedicine.objects.create(
            prescription=prescription,
            medicine=expired_med,
            medicine_name=expired_med.name,
            dosage="250mg",
            frequency="Daily",
            duration="5 days",
            quantity=5,
        )

        response = self.client.post(reverse("prescription_dispense", args=[prescription.pk]))
        self.assertRedirects(response, reverse("prescription_detail", args=[prescription.pk]))

        expired_med.refresh_from_db()
        self.assertEqual(expired_med.stock_quantity, 40)
        item.refresh_from_db()
        self.assertFalse(item.is_dispensed)

    def test_prescription_dispense_prevented_when_already_dispensed(self):
        self.client.login(username="staff", password="testpass123")
        prescription = Prescription.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            prescription_date=self.today,
        )
        item = PrescriptionMedicine.objects.create(
            prescription=prescription,
            medicine=self.medicine,
            medicine_name=self.medicine.name,
            dosage="500mg",
            frequency="TDS",
            duration="5 days",
            quantity=10,
            is_dispensed=True,
            dispensed_at=timezone.now(),
        )

        # Attempting second dispense should not deduct again
        response = self.client.post(reverse("prescription_dispense", args=[prescription.pk]))
        self.assertRedirects(response, reverse("prescription_detail", args=[prescription.pk]))
        self.medicine.refresh_from_db()
        self.assertEqual(self.medicine.stock_quantity, 50)

    def test_dashboard_reflects_medicine_count_and_inventory_links(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Medicine Inventory")
        self.assertContains(response, reverse("medicine_list"))
        self.assertContains(response, "Total Prescriptions")

    def test_sidebar_includes_active_medicine_navigation(self):
        self.client.login(username="staff", password="testpass123")
        response = self.client.get(reverse("medicine_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("medicine_list"))
        self.assertContains(response, 'class="nav-link active"')

class DashboardVisualizationTests(TestCase):
    def setUp(self):
        User.objects.create_user(username="dashboard-staff", password="test-password")
        self.client.login(username="dashboard-staff", password="test-password")

    def test_dashboard_visual_metrics_use_current_database_records(self):
        today = timezone.localdate()
        patient = Patient.objects.create(name="Dashboard Patient")
        doctor = Doctor.objects.create(name="Dr. Dashboard")
        room = Room.objects.create(
            room_number="D-1",
            bed_capacity=3,
            charges_per_day=Decimal("100.00"),
        )
        Admission.objects.create(
            patient=patient,
            room=room,
            admission_date=today,
            reason_for_admission="Observation",
            status="Admitted",
        )
        Medicine.objects.create(
            name="Dashboard Medicine",
            manufacturer="Clinic",
            batch_number="DASH-1",
            purchase_price=Decimal("1.00"),
            selling_price=Decimal("2.00"),
            stock_quantity=4,
            min_stock_threshold=5,
            expiry_date=today + timedelta(days=90),
        )
        Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=today,
            appointment_time=time(23, 59),
            reason_for_visit="Review",
            status="Completed",
        )
        upcoming = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=today + timedelta(days=1),
            appointment_time=time(10, 0),
            reason_for_visit="Follow-up",
            status="Scheduled",
        )

        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["appointment_chart_data"][-1], 2)
        self.assertEqual(response.context["total_beds"], 3)
        self.assertEqual(response.context["occupied_beds"], 1)
        self.assertEqual(response.context["available_beds"], 2)
        self.assertEqual(response.context["total_stock_units"], 4)
        self.assertEqual(response.context["low_stock_medicines"], 1)
        self.assertEqual(list(response.context["upcoming_appointments"]), [upcoming])
        self.assertContains(response, "Appointment trend")
        self.assertContains(response, "Room occupancy")
        self.assertContains(response, "Dashboard Medicine")

    def test_dashboard_visualizations_handle_empty_data(self):
        response = self.client.get(reverse("dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["appointment_chart_data"], [0] * 6)
        self.assertEqual(response.context["total_beds"], 0)
        self.assertEqual(response.context["occupancy_percent"], 0)
        self.assertEqual(response.context["total_stock_units"], 0)
        self.assertFalse(response.context["upcoming_appointments"])
        self.assertContains(response, "No upcoming appointments scheduled.")


class TreatmentManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="treatment-staff", password="test-password")
        self.patient = Patient.objects.create(name="Treatment Patient")
        self.doctor = Doctor.objects.create(name="Dr. Treatment")
        self.treatment = Treatment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            treatment_date=timezone.localdate(),
            diagnosis="Routine review",
            description="Initial treatment notes",
        )
        self.valid_data = {
            "patient": self.patient.pk,
            "doctor": self.doctor.pk,
            "treatment_date": timezone.localdate().strftime("%Y-%m-%d"),
            "diagnosis": "Updated diagnosis",
            "description": "Treatment description",
            "notes": "Follow-up notes",
        }
        self.client.login(username="treatment-staff", password="test-password")

    def test_treatment_crud_and_relationships(self):
        list_response = self.client.get(reverse("treatment_list"))
        detail_response = self.client.get(
            reverse("treatment_detail", args=[self.treatment.pk])
        )
        self.assertContains(list_response, self.patient.name)
        self.assertContains(detail_response, self.doctor.name)

        add_response = self.client.post(reverse("treatment_add"), self.valid_data)
        created = Treatment.objects.get(diagnosis="Updated diagnosis")
        self.assertRedirects(
            add_response,
            reverse("treatment_detail", args=[created.pk]),
        )
        self.assertEqual(created.patient, self.patient)
        self.assertEqual(created.doctor, self.doctor)

        edit_data = self.valid_data | {"diagnosis": "Edited diagnosis"}
        edit_response = self.client.post(
            reverse("treatment_edit", args=[self.treatment.pk]),
            edit_data,
        )
        self.assertRedirects(
            edit_response,
            reverse("treatment_detail", args=[self.treatment.pk]),
        )
        self.treatment.refresh_from_db()
        self.assertEqual(self.treatment.diagnosis, "Edited diagnosis")
        self.assertEqual(self.treatment.notes, "Follow-up notes")

        delete_response = self.client.post(
            reverse("treatment_delete", args=[self.treatment.pk])
        )
        self.assertRedirects(delete_response, reverse("treatment_list"))
        self.assertFalse(Treatment.objects.filter(pk=self.treatment.pk).exists())

    def test_treatment_required_fields_show_validation_errors(self):
        response = self.client.post(reverse("treatment_add"), {})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please select a patient.")
        self.assertContains(response, "Please select the treating doctor.")
        self.assertContains(response, "Please enter a diagnosis.")
        self.assertEqual(Treatment.objects.count(), 1)

    def test_treatment_views_require_login(self):
        self.client.logout()
        urls = [
            reverse("treatment_list"),
            reverse("treatment_add"),
            reverse("treatment_detail", args=[self.treatment.pk]),
            reverse("treatment_edit", args=[self.treatment.pk]),
            reverse("treatment_delete", args=[self.treatment.pk]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(
                    response,
                    f"{reverse('login')}?next={url}",
                )


class PrescriptionManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="prescription-staff", password="test-password")
        self.patient = Patient.objects.create(name="Prescription Patient")
        self.doctor = Doctor.objects.create(name="Dr. Prescription")
        self.prescription = Prescription.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            prescription_date=timezone.localdate(),
            instructions="Original instructions",
        )
        self.item = PrescriptionMedicine.objects.create(
            prescription=self.prescription,
            medicine_name="Custom medicine",
            dosage="10mg",
            frequency="Once daily",
            duration="5 days",
            quantity=5,
        )
        self.client.login(username="prescription-staff", password="test-password")

    def test_prescription_crud_and_relationships(self):
        list_response = self.client.get(reverse("prescription_list"))
        detail_response = self.client.get(
            reverse("prescription_detail", args=[self.prescription.pk])
        )
        self.assertContains(list_response, self.patient.name)
        self.assertContains(detail_response, "Custom medicine")

        add_data = {
            "patient": self.patient.pk,
            "doctor": self.doctor.pk,
            "prescription_date": timezone.localdate().strftime("%Y-%m-%d"),
            "instructions": "New instructions",
            "medicines-TOTAL_FORMS": "1",
            "medicines-INITIAL_FORMS": "0",
            "medicines-MIN_NUM_FORMS": "1",
            "medicines-MAX_NUM_FORMS": "1000",
            "medicines-0-medicine": "",
            "medicines-0-medicine_name": "New custom medicine",
            "medicines-0-dosage": "20mg",
            "medicines-0-frequency": "Twice daily",
            "medicines-0-duration": "7 days",
            "medicines-0-quantity": "14",
        }
        add_response = self.client.post(reverse("prescription_add"), add_data)
        created = Prescription.objects.get(instructions="New instructions")
        self.assertRedirects(
            add_response,
            reverse("prescription_detail", args=[created.pk]),
        )
        new_item = created.medicines.get()
        self.assertEqual(created.patient, self.patient)
        self.assertEqual(created.doctor, self.doctor)
        self.assertEqual(new_item.medicine_name, "New custom medicine")
        self.assertEqual(new_item.quantity, 14)

        edit_data = {
            "patient": self.patient.pk,
            "doctor": self.doctor.pk,
            "prescription_date": timezone.localdate().strftime("%Y-%m-%d"),
            "instructions": "Edited instructions",
            "medicines-TOTAL_FORMS": "2",
            "medicines-INITIAL_FORMS": "1",
            "medicines-MIN_NUM_FORMS": "1",
            "medicines-MAX_NUM_FORMS": "1000",
            "medicines-0-id": self.item.pk,
            "medicines-0-medicine": "",
            "medicines-0-medicine_name": "Edited custom medicine",
            "medicines-0-dosage": "15mg",
            "medicines-0-frequency": "Twice daily",
            "medicines-0-duration": "10 days",
            "medicines-0-quantity": "20",
            "medicines-1-medicine": "",
            "medicines-1-medicine_name": "",
            "medicines-1-dosage": "",
            "medicines-1-frequency": "",
            "medicines-1-duration": "",
            "medicines-1-quantity": "1",
        }
        edit_response = self.client.post(
            reverse("prescription_edit", args=[self.prescription.pk]),
            edit_data,
        )
        self.assertRedirects(
            edit_response,
            reverse("prescription_detail", args=[self.prescription.pk]),
        )
        self.prescription.refresh_from_db()
        self.item.refresh_from_db()
        self.assertEqual(self.prescription.instructions, "Edited instructions")
        self.assertEqual(self.item.medicine_name, "Edited custom medicine")
        self.assertEqual(self.item.quantity, 20)

        delete_response = self.client.post(
            reverse("prescription_delete", args=[self.prescription.pk])
        )
        self.assertRedirects(delete_response, reverse("prescription_list"))
        self.assertFalse(
            Prescription.objects.filter(pk=self.prescription.pk).exists()
        )
        self.assertFalse(
            PrescriptionMedicine.objects.filter(pk=self.item.pk).exists()
        )

    def test_prescription_requires_at_least_one_medicine(self):
        response = self.client.post(
            reverse("prescription_add"),
            {
                "patient": self.patient.pk,
                "doctor": self.doctor.pk,
                "prescription_date": timezone.localdate().strftime("%Y-%m-%d"),
                "instructions": "",
                "medicines-TOTAL_FORMS": "0",
                "medicines-INITIAL_FORMS": "0",
                "medicines-MIN_NUM_FORMS": "1",
                "medicines-MAX_NUM_FORMS": "1000",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please submit at least 1 form.")
        self.assertEqual(Prescription.objects.count(), 1)

    def test_prescription_required_header_fields_show_validation_errors(self):
        response = self.client.post(reverse("prescription_add"), {})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please select a patient.")
        self.assertContains(response, "Please select the prescribing doctor.")
        self.assertContains(response, "Please enter the prescription date.")
        self.assertEqual(Prescription.objects.count(), 1)

    def test_prescription_medicine_requires_name_or_inventory_selection(self):
        data = {
            "patient": self.patient.pk,
            "doctor": self.doctor.pk,
            "prescription_date": timezone.localdate().strftime("%Y-%m-%d"),
            "instructions": "",
            "medicines-TOTAL_FORMS": "1",
            "medicines-INITIAL_FORMS": "0",
            "medicines-MIN_NUM_FORMS": "1",
            "medicines-MAX_NUM_FORMS": "1000",
            "medicines-0-medicine": "",
            "medicines-0-medicine_name": "",
            "medicines-0-dosage": "10mg",
            "medicines-0-frequency": "Daily",
            "medicines-0-duration": "5 days",
            "medicines-0-quantity": "5",
        }
        response = self.client.post(reverse("prescription_add"), data)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Please enter the medicine name.")
        self.assertEqual(Prescription.objects.count(), 1)

    def test_prescription_views_require_login(self):
        self.client.logout()
        urls = [
            reverse("prescription_list"),
            reverse("prescription_add"),
            reverse("prescription_detail", args=[self.prescription.pk]),
            reverse("prescription_edit", args=[self.prescription.pk]),
            reverse("prescription_delete", args=[self.prescription.pk]),
        ]

        for url in urls:
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertRedirects(
                    response,
                    f"{reverse('login')}?next={url}",
                )


class AuthenticationTests(TestCase):
    def setUp(self):
        User.objects.create_user(username="auth-staff", password="test-password")

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("dashboard"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('dashboard')}",
        )

    def test_login_and_logout(self):
        login_response = self.client.post(
            reverse("login"),
            {"username": "auth-staff", "password": "test-password"},
        )
        self.assertRedirects(login_response, reverse("dashboard"))
        self.assertEqual(
            self.client.get(reverse("dashboard")).status_code,
            200,
        )

        logout_response = self.client.post(reverse("logout"))
        self.assertRedirects(logout_response, reverse("login"))
        self.assertRedirects(
            self.client.get(reverse("dashboard")),
            f"{reverse('login')}?next={reverse('dashboard')}",
        )
