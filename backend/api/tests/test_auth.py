import uuid
from unittest.mock import patch
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.test import APITestCase
from rest_framework import status
from django.conf import settings
from django.urls.exceptions import NoReverseMatch
from django.core.cache import cache

from api.models import User
from api.serializers.auth import SignUpSerializer
from api.services.auth import send_verification_email

# ---------- Serializer ----------
class SignUpSerializerTesets(APITestCase):
    def setUp(self):
        cache.clear()

    def test_valid_data(self):
        payload = {
            "email": "test@example.com",
            "username": "newuser",
            "password": "ComplexPass123!",
            "firstName": "New",
            "lastName": "User",
        }
        serializer = SignUpSerializer(data=payload)
        self.assertTrue(serializer.is_valid(), msg=serializer.errors)
        user = serializer.save()
        self.assertEqual(user.email, payload["email"])
        self.assertFalse(user.is_active)
        self.assertNotEqual(user.password, payload["password"])
        self.assertTrue(user.check_password(payload["password"]))

    def test_invalid_email(self):
        serializer = SignUpSerializer(
            data = {
                "email": "testexample.com",
                "username": "newuser",
                "password": "ComplexPass123!",
                "firstName": "New",
                "lastName": "User",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_duplicate_email(self):
        User.objects.create_user(
            username="newuser",
            email="test@example.com",
            password="test",
            first_name="New",
            last_name="User"
        )
        serializer = SignUpSerializer(
            data = {
                "email": "test@example.com",
                "username": "newuser2",
                "password": "ComplexPass123!",
                "firstName": "A",
                "lastName": "B",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)

    def test_weak_password(self):
        serializer = SignUpSerializer(
            data={
                "email": "weak@example.com",
                "username": "weak",
                "password": "123",
                "firstName": "A",
                "lastName": "B",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("password", serializer.errors)

    def test_missing_required_fields(self):
        serializer = SignUpSerializer(data={})
        self.assertFalse(serializer.is_valid())
        for field in ("email", "username", "password", "first_name", "last_name"):
            self.assertIn(field, serializer.errors)

# ---------- Services ----------
class VerificationEmailTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="newuser",
            email="test@example.com",
            password="test",
            first_name="New",
            last_name="User"
        )
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)

    # Mock send_email
    @patch("api.services.auth.send_mail")
    def test_email_queued_with_correct_content(self, mock_send_mail):
        send_verification_email(self.user)
        self.assertEqual(mock_send_mail.call_count, 1)
        _, kwargs = mock_send_mail.call_args
        self.assertEqual(kwargs["subject"], "Confirmation Email")
        self.assertEqual(kwargs["recipient_list"], ["test@example.com"])
        self.assertIn(settings.FRONTEND_URL, kwargs["html_message"])
        self.assertIn(self.uid, kwargs["html_message"])

    def test_activate_user(self):
        key = f'{self.uid}-{self.token}'
        url = reverse("verify_email", kwargs={"key": key})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_bad_uid(self):
        key = f'abc-{self.token}'
        bad_url = reverse("verify_email", kwargs={"key": key})
        res = self.client.get(bad_url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bad_token(self):
        key = f'{self.uid}-abc'
        bad_url = reverse("verify_email", kwargs={"key": key})
        res = self.client.get(bad_url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bad_url_argument(self):
        with self.assertRaisesMessage(
            NoReverseMatch,
            "verify_email",
        ):
            reverse("verify_email", kwargs={"test": "test"})

    def test_invalid_key(self):
        url = reverse("verify_email", kwargs={"key": "invalid-pk-token"})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_user(self):
        fake_uid = urlsafe_base64_encode(force_bytes(uuid.uuid4()))
        key = f'{fake_uid}-{self.token}'
        url = reverse("verify_email", kwargs={"key": key})
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

# ---------- Views ----------
class SignUpViewTests(APITestCase):
    URL = reverse("signup")

    def setUp(self):
        cache.clear()

    def test_successful_email_sent(self):
        with patch("api.views.auth.send_verification_email") as mock_send:
            res = self.client.post(
                self.URL,
                {
                    "email": "test@example.com",
                    "username": "newuser",
                    "password": "ComplexPass123!",
                    "firstName": "New",
                    "lastName": "User"
                },
                format="json",
            )
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="test@example.com").exists())
        mock_send.assert_called_once()

    def test_duplicate_user_email(self):
        User.objects.create_user(
            username="newuser",
            email="test@example.com",
            password="test",
            first_name="New",
            last_name="User"
        )
        res = self.client.post(
            self.URL,
            {
                "email": "test@example.com",
                "username": "newuser",
                "password": "ComplexPass123!",
                "firstName": "New",
                "lastName": "User"
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", res.data)

    def test_weak_password(self):
        res = self.client.post(
            self.URL,
            {
                "email": "test@example.com",
                "username": "newuser",
                "password": "123",
                "firstName": "New",
                "lastName": "User"
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", res.data)

    def test_missing_required_field(self):
        res = self.client.post(self.URL, {}, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        for field in ("email", "username", "password", "first_name", "last_name"):
            self.assertIn(field, res.data)

    def test_invalid_email_format_400(self):
        res = self.client.post(
            self.URL,
            {
                "email": "testexample.com",
                "username": "newuser",
                "password": "ComplexPass123!",
                "firstName": "New",
                "lastName": "User",
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", res.data)


    def test_duplicate_username(self):
        User.objects.create_user(
            username="taken", email="test@example.com", password="pass"
        )
        res = self.client.post(
            self.URL,
            {
                "email": "test@example.com",
                "username": "taken",
                "password": "ComplexPass123!",
                "firstName": "New",
                "lastName": "User",
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", res.data)

    def test_ratelimit_blocks_request(self):
        for i in range(5):
            self.client.post(
                self.URL,
                {
                    "email": f"rate{i}@example.com",
                    "username": f"rate{i}",
                    "password": "ComplexPass123!",
                    "firstName": "New",
                    "lastName": "User",
                },
                format="json",
            )
        res = self.client.post(
            self.URL,
            {
                "email": f"abcdefg@example.com",
                "username": f"rate_x",
                "password": "ComplexPass123!",
                "firstName": "New",
                "lastName": "User",
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

# ---------- Verify Email ----------
class VerifyEmailViewTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="newuser", email="test@example.com", password="ComplexPass123!", is_active=False
        )
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)

    def _url(self, uid=None, token=None):
        key = f"{uid or self.uid}-{token or self.token}"
        return reverse("verify_email", kwargs={"key": key})
    
    def test_valid_key_verify_user(self):
        res = self.client.get(self._url())
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["detail"], "E-mail verified")
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_missing_separator(self):
        res = self.client.get(reverse("verify_email", kwargs={"key": "missingsep"}))
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["detail"], "Bad link")

    def test_nonexistent_user(self):
        fake_uid = urlsafe_base64_encode(force_bytes(uuid.uuid4()))
        res = self.client.get(self._url(uid=fake_uid))
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["detail"], "Bad link")

    def test_bad_token(self):
        res = self.client.get(self._url(token="bad-token"))
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["detail"], "Bad or expired token")

    def test_token_invalid_after_password_change(self):
        old_token = self.token
        self.user.set_password("newPass123!")
        self.user.save()
        res = self.client.get(self._url(token=old_token))
        self.assertEqual(res.status_code, 400)
        self.assertEqual(res.data["detail"], "Bad or expired token")

class ResendVerifyViewTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.inactive = User.objects.create_user(
            username="newuser", email="test@example.com", password="pass", is_active=False
        )
        self.active = User.objects.create_user(
            username="newuser2", email="test2@example.com", password="pass", is_active=True
        )
        self.url = reverse("resend_verify")

    @patch("api.views.auth.send_verification_email")
    def test_resend_to_inactive_user_sends_email(self, mock_send):
        res = self.client.post(self.url, {"email": "test@example.com"})
        self.assertEqual(res.status_code, 204)
        mock_send.assert_called_once_with(self.inactive)

    def test_no_email_sent_to_active_user(self):
        with patch("api.views.auth.send_verification_email") as mock_send:
            res = self.client.post(self.url, {"email": "test2@example.com"})
        self.assertEqual(res.status_code, 204)
        mock_send.assert_not_called()

    def test_no_email_sent_to_nonexistent_address(self):
        with patch("api.views.auth.send_verification_email") as mock_send:
            res = self.client.post(self.url, {"email": "no@example.com"})
        self.assertEqual(res.status_code, 204)
        mock_send.assert_not_called()

    def test_ratelimit_blocks_4th_call(self):
        for _ in range(3):
            self.client.post(self.url, {"email": "test@example.com"})
        res = self.client.post(self.url, {"email": "test@example.com"})
        self.assertEqual(res.status_code, 403)