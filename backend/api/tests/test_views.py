# from django.urls import reverse
# from rest_framework.test import APITestCase, APIClient
# from django.contrib.auth import get_user_model
# from django.core.files.uploadedfile import SimpleUploadedFile
# from rest_framework import status
# from io import BytesIO
# from PIL import Image

# from ..models import Speciality, Doctor

# User = get_user_model()

# def create_test_image():
#     # Create a simple image in memory
#     image = Image.new('RGB', (100, 100), color='red')
#     buffer = BytesIO()
#     image.save(buffer, format='JPEG')
#     return buffer.getvalue()

# class SpecialityViewTest(APITestCase):
#     def setUp(self):
#         self.client = APIClient()
        
#         self.admin_user = User.objects.create_superuser(
#             email='admin@test.com',
#             password='testpass123',
#             first_name='Admin',
#             last_name='User',
#             date_of_birth='1990-01-01',
#         )
#         self.regular_user = User.objects.create_user(
#             email='user@test.com',
#             password='testpass123',
#             first_name='Regular',
#             last_name='User',
#             date_of_birth='1990-01-01',
#         )
        
#         self.iamge_file = SimpleUploadedFile(
#             "test.svg",
#             b"file_content",
#             content_type="image/svg+xml"
#         )
        
#         self.speciality_data = {
#             "name": "Gynecologist",
#             "image": self.iamge_file
#         }
        
#     def test_admin_create_speciality(self):
#         self.client.force_authenticate(user=self.admin_user)
#         response = self.client.post(reverse('speciality-list-create'), self.speciality_data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(Speciality.objects.count(), 1)
        
#     def test_regular_user_create_speciality(self):
#         self.client.force_authenticate(user=self.regular_user)
#         response = self.client.post(reverse('speciality-list-create'), self.speciality_data)
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
#         self.assertEqual(Speciality.objects.count(), 0)
        
#     def test_anyone_can_view_specialities(self):
#         Speciality.objects.create(**self.speciality_data)
        
#         # Test without authentication
#         response = self.client.get(reverse('speciality-list-create'))
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 1)

# class DoctorViewTest(APITestCase):
#     def setUp(self):
#         self.client = APIClient()
        
#         self.admin_user = User.objects.create_superuser(
#             email='admin@test.com',
#             password='testpass123',
#             first_name='Admin',
#             last_name='User',
#             date_of_birth='1990-01-01',
#         )
#         self.regular_user = User.objects.create_user(
#             email='user@test.com',
#             password='testpass123',
#             first_name='Regular',
#             last_name='User',
#             date_of_birth='1990-01-01',
#         )
        
#         self.iamge_file = SimpleUploadedFile(
#             "test.svg",
#             b"file_content",
#             content_type="image/svg+xml"
#         )
#         self.speciality = Speciality.objects.create(
#             name="Gynecologist",
#             image=self.iamge_file
#         )
        
#         self.doctor_image_file = SimpleUploadedFile(
#             "test.jpg",
#             create_test_image(),
#             content_type="image/jpeg"
#         )
#         self.doctor_data = {
#             "speciality_id": self.speciality.id,
#             "first_name": "John",
#             "last_name": "Doe",
#             "image": self.doctor_image_file,
#             "degree": "MD",
#             "experience": 10.,
#             "about": "Experienced cardiologist",
#             "fees": 50.00,
#             "address_line1": "123 Main St",
#             "city": "New York",
#             "state": "NY",
#             "zip_code": "10001"
#         }
        
#     def test_admin_create_doctor(self):
#         self.client.force_authenticate(user=self.admin_user)
#         response = self.client.post(reverse('doctor-list-create'), self.doctor_data)
#         self.assertEqual(response.status_code, status.HTTP_201_CREATED)
#         self.assertEqual(Doctor.objects.count(), 1)
#         self.assertEqual(Doctor.objects.first().speciality, self.speciality)

#     def test_regular_user_create_doctor(self):
#         self.client.force_authenticate(user=self.regular_user)
#         response = self.client.post(reverse('doctor-list-create'), self.doctor_data)
#         self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
#         self.assertEqual(Doctor.objects.count(), 0)
        
#     def test_anyone_can_view_doctor(self):
#         Doctor.objects.create(**self.doctor_data)
#         response = self.client.get(reverse('doctor-list-create'))
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(len(response.data), 1)
        
# class DoctorDeleteViewTest(APITestCase):
#     def setUp(self):
#         self.client = APIClient()
        
#         self.admin_user = User.objects.create_superuser(
#             email='admin@test.com',
#             password='testpass123',
#             first_name='Admin',
#             last_name='User',
#             date_of_birth='1990-01-01',
#         )
        
#         self.iamge_file = SimpleUploadedFile(
#             "test.svg",
#             b"file_content",
#             content_type="image/svg+xml"
#         )
#         self.speciality = Speciality.objects.create(
#             name="Gynecologist",
#             image=self.iamge_file
#         )
        
#         self.doctor_image_file = SimpleUploadedFile(
#             "test.jpg",
#             create_test_image(),
#             content_type="image/jpeg"
#         )
#         self.doctor_data = {
#             "speciality_id": self.speciality.id,
#             "first_name": "John",
#             "last_name": "Doe",
#             "image": self.doctor_image_file,
#             "degree": "MD",
#             "experience": 10.,
#             "about": "Experienced cardiologist",
#             "fees": 50.00,
#             "address_line1": "123 Main St",
#             "city": "New York",
#             "state": "NY",
#             "zip_code": "10001"
#         }
        
#         self.client.force_authenticate(user=self.admin_user)
        
#     def test_delete_doctor(self):
#         response = self.client.post(reverse('doctor-list-create'), self.doctor_data)
#         self.client.delete(reverse('doctor-delete', kwargs={"pk": response.data["id"]}))
#         self.assertEqual(Doctor.objects.count(), 0)
        
# class DoctorBySspecialityViewTest(APITestCase):
#     def setUp(self):
#         self.client = APIClient()
        
#         self.admin_user = User.objects.create_superuser(
#             email='admin@test.com',
#             password='testpass123',
#             first_name='Admin',
#             last_name='User',
#             date_of_birth='1990-01-01',
#         )
        
#         self.iamge_file = SimpleUploadedFile(
#             "test.svg",
#             b"file_content",
#             content_type="image/svg+xml"
#         )
#         self.speciality = Speciality.objects.create(
#             name="Gynecologist",
#             image=self.iamge_file
#         )
        
#         self.doctor_image_file = SimpleUploadedFile(
#             "test.jpg",
#             create_test_image(),
#             content_type="image/jpeg"
#         )
#         self.doctor_data = {
#             "speciality_id": self.speciality.id,
#             "first_name": "John",
#             "last_name": "Doe",
#             "image": self.doctor_image_file,
#             "degree": "MD",
#             "experience": 10.,
#             "about": "Experienced cardiologist",
#             "fees": 50.00,
#             "address_line1": "123 Main St",
#             "city": "New York",
#             "state": "NY",
#             "zip_code": "10001"
#         }
        
#         self.client.force_authenticate(user=self.admin_user)
#         self.client.post(reverse('doctor-list-create'), self.doctor_data)

#     def test_get_query_set(self):
#         response = self.client.get(reverse('doctors-by-speciality', kwargs={"speciality": "Gynecologist"}))
#         res_data = response.data[0]
#         doc_data = self.doctor_data
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertEqual(res_data['firstName'], doc_data['first_name'])
#         self.assertEqual(res_data['lastName'], doc_data['last_name'])
#         self.assertEqual(res_data['id'], doc_data['speciality_id'])
        