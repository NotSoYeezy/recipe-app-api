from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
USER_OWN_URL = reverse('user:profile')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTest(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test if user can be successfully created"""
        user_data = {
            'email': 'test@test.pl',
            'password': 'testPassword',
            'name': 'Test Name'
        }
        resp = self.client.post(CREATE_USER_URL, user_data)

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**resp.data)
        self.assertTrue(user.check_password(user_data['password']))
        self.assertNotIn('password', resp.data)

    def test_user_exists(self):
        """Test if user can't create user that already exists"""
        user_data = {
            'email': 'test@test.pl',
            'password': 'testPass',
            'name': 'Test Name'
        }
        create_user(**user_data)

        resp = self.client.post(CREATE_USER_URL, user_data)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        """Test if password is long enough"""
        user_data = {
            'email': 'test@test.pl',
            'password': 'pw',
            'name': 'Test Name'
        }
        resp = self.client.post(CREATE_USER_URL, user_data)

        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        user_exists = get_user_model().objects.filter(email=user_data['email']).exists()

        self.assertFalse(user_exists)

    def test_create_token_for_user(self):
        """Testing that auth token can be created for user"""
        user_data = {
            'email': 'test@test.pl',
            'password': 'testPassword'
        }
        create_user(**user_data)
        resp = self.client.post(TOKEN_URL, user_data)

        self.assertIn('token', resp.data)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credentials(self):
        """Testing that token is not created if invalid credentials are given"""
        create_user(email='test@test.pl', password='testPassword')
        post_data = {
            'email': 'test@test.pl',
            'password': 'InvalidPassword',
        }
        resp = self.client.post(TOKEN_URL, post_data)

        self.assertNotIn('token', resp.data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_no_user(self):
        """Testing that token is not created if user doesn't exist"""
        post_data = {
            'email': 'test@test.pl',
            'password': 'testPassword'
        }
        resp = self.client.post(TOKEN_URL, post_data)

        self.assertNotIn('token', resp.data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """Testing that email and password are required"""
        resp = self.client.post(TOKEN_URL, {'email': 'wrong', 'password': ''})
        self.assertNotIn('token', resp.data)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Testing that auth is required for users"""
        resp = self.client.get(USER_OWN_URL)

        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTest(TestCase):
    """Test API requests that require authentication"""

    def setUp(self):
        self.user = create_user(
            email='test@test.pl',
            password='testPassword',
            name='Test Name'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""
        resp = self.client.get(USER_OWN_URL)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_post_own_not_allowed(self):
        """Test that POST request is not allowed on the user own url"""
        resp = self.client.post(USER_OWN_URL, {})

        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test that authenticated user can update his profile"""
        patch_data = {'name': 'new Name', 'password': 'newPassword123'}
        resp = self.client.patch(USER_OWN_URL, patch_data)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, patch_data['name'])
        self.assertTrue(self.user.check_password(patch_data['password']))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
