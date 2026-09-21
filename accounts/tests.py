from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase


class AuthenticationTests(APITestCase):
	register_url = '/api/auth/register/'
	login_url = '/api/auth/login/'

	def test_registration_succeeds(self):
		response = self.client.post(self.register_url, {
			'username': 'saroon',
			'password': 'password123',
			'first_name': 'Saroon',
			'last_name': 'K',
		}, format='json')

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertTrue(User.objects.filter(username='saroon').exists())

	def test_duplicate_username_returns_bad_request(self):
		User.objects.create_user(username='saroon', password='password123')

		response = self.client.post(self.register_url, {
			'username': 'saroon',
			'password': 'password123',
		}, format='json')

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_valid_login_returns_access_and_refresh_tokens(self):
		User.objects.create_user(username='saroon', password='password123')

		response = self.client.post(self.login_url, {
			'username': 'saroon',
			'password': 'password123',
		}, format='json')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('access', response.data)
		self.assertIn('refresh', response.data)

	def test_invalid_login_returns_unauthorized(self):
		User.objects.create_user(username='saroon', password='password123')

		response = self.client.post(self.login_url, {
			'username': 'saroon',
			'password': 'wrong-password',
		}, format='json')

		self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
