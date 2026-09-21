from datetime import date, timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Category, Expense


class ExpenseAPITests(APITestCase):
	expenses_url = '/api/expenses/'
	categories_url = '/api/categories/'
	summary_url = '/api/summary/'

	def setUp(self):
		self.user = User.objects.create_user(username='saroon', password='password123')
		self.other_user = User.objects.create_user(username='other', password='password123')
		self.food, _ = Category.objects.get_or_create(name='Food')
		self.transport, _ = Category.objects.get_or_create(name='Transport')
		self.client.force_authenticate(user=self.user)

	def create_expense(self, user=None, category=None, amount='10.00', expense_date=None, note='Test'):
		return Expense.objects.create(
			user=user or self.user,
			category=category or self.food,
			amount=amount,
			date=expense_date or timezone.localdate(),
			note=note,
		)

	def test_authenticated_categories_returns_ok(self):
		response = self.client.get(self.categories_url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn('Food', {item['name'] for item in response.data})

	def test_categories_are_currently_public(self):
		self.client.force_authenticate(user=None)

		response = self.client.get(self.categories_url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)

	def test_valid_expense_returns_created(self):
		response = self.client.post(self.expenses_url, {
			'amount': '10.25',
			'category': self.food.id,
			'note': 'Lunch',
			'date': '2026-09-21',
		}, format='json')

		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(Expense.objects.filter(user=self.user).count(), 1)

	def test_amount_below_one_returns_bad_request(self):
		response = self.client.post(self.expenses_url, {
			'amount': '0.50',
			'category': self.food.id,
			'date': '2026-09-21',
		}, format='json')

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_missing_required_expense_fields_returns_bad_request(self):
		response = self.client.post(self.expenses_url, {}, format='json')

		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

	def test_expenses_are_authenticated_and_user_scoped(self):
		own_expense = self.create_expense(note='Mine')
		self.create_expense(user=self.other_user, note='Not mine')

		response = self.client.get(self.expenses_url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]['id'], own_expense.id)

		self.client.force_authenticate(user=None)
		self.assertEqual(self.client.get(self.expenses_url).status_code, status.HTTP_401_UNAUTHORIZED)

	def test_category_filter_returns_matching_expenses(self):
		self.create_expense(category=self.food, note='Food expense')
		self.create_expense(category=self.transport, note='Transport expense')

		response = self.client.get(f'{self.expenses_url}?category={self.food.id}')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]['category'], self.food.id)

	def test_date_filters_include_requested_boundaries(self):
		self.create_expense(expense_date=date(2026, 9, 1), note='Start')
		self.create_expense(expense_date=date(2026, 9, 21), note='End')
		self.create_expense(expense_date=date(2026, 8, 31), note='Outside')

		response = self.client.get(f'{self.expenses_url}?start_date=2026-09-01&end_date=2026-09-21')

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual({item['note'] for item in response.data}, {'Start', 'End'})

	def test_summary_returns_user_totals_and_categories(self):
		today = timezone.localdate()
		previous_month = today.replace(day=1) - timedelta(days=1)
		self.create_expense(amount='25.00', expense_date=today, category=self.food)
		self.create_expense(amount='10.00', expense_date=today, category=self.transport)
		self.create_expense(amount='20.00', expense_date=previous_month, category=self.food)
		self.create_expense(user=self.other_user, amount='999.00', expense_date=today)

		response = self.client.get(self.summary_url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['current_month_total'], '₹35.00')
		self.assertEqual(response.data['previous_month_total'], '₹20.00')
		self.assertEqual(response.data['month_over_month_percentage'], '+75.00%')
		self.assertEqual({item['category'] for item in response.data['current_month_by_category']}, {'Food', 'Transport'})

		self.client.force_authenticate(user=None)
		self.assertEqual(self.client.get(self.summary_url).status_code, status.HTTP_401_UNAUTHORIZED)

	def test_summary_returns_insight_for_more_than_twenty_percent_category_increase(self):
		today = timezone.localdate()
		previous_month = today.replace(day=1) - timedelta(days=1)
		self.create_expense(amount='100.00', expense_date=previous_month)
		self.create_expense(amount='125.00', expense_date=today)

		response = self.client.get(self.summary_url)

		self.assertEqual(response.data['insights'], [{
			'category': 'Food',
			'increase_percentage': 25.0,
			'message': 'Food spending increased by 25% compared to last month.',
		}])

	def test_summary_does_not_return_insight_for_exactly_twenty_percent_increase(self):
		today = timezone.localdate()
		previous_month = today.replace(day=1) - timedelta(days=1)
		self.create_expense(amount='100.00', expense_date=previous_month)
		self.create_expense(amount='120.00', expense_date=today)

		response = self.client.get(self.summary_url)

		self.assertEqual(response.data['insights'], [])

	def test_summary_does_not_return_insight_for_less_than_twenty_percent_increase(self):
		today = timezone.localdate()
		previous_month = today.replace(day=1) - timedelta(days=1)
		self.create_expense(amount='100.00', expense_date=previous_month)
		self.create_expense(amount='119.00', expense_date=today)

		response = self.client.get(self.summary_url)

		self.assertEqual(response.data['insights'], [])

	def test_summary_skips_insight_when_previous_category_spending_is_zero(self):
		today = timezone.localdate()
		self.create_expense(amount='100.00', expense_date=today)

		response = self.client.get(self.summary_url)

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data['insights'], [])
