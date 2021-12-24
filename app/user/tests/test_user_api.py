from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


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
