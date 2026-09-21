from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import Sum
from django.utils import timezone
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response

from .filters import ExpenseFilter
from .models import Category, Expense
from .serializers import CategorySerializer, ExpenseSerializer


class CategoryListView(generics.ListAPIView):
	queryset = Category.objects.order_by('name')
	serializer_class = CategorySerializer
	permission_classes = []


class ExpenseListCreateView(generics.ListCreateAPIView):
	serializer_class = ExpenseSerializer
	filterset_class = ExpenseFilter

	def get_queryset(self):
		return Expense.objects.filter(user=self.request.user).select_related('category').order_by('-date', '-created_at')

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)


class SummaryView(APIView):
	def get(self, request):
		today = timezone.localdate()
		current_start = today.replace(day=1)
		next_month_start = (current_start + timedelta(days=32)).replace(day=1)
		previous_end = current_start - timedelta(days=1)
		previous_start = previous_end.replace(day=1)
		user_expenses = Expense.objects.filter(user=request.user)
		current_expenses = user_expenses.filter(date__gte=current_start, date__lt=next_month_start)
		previous_expenses = user_expenses.filter(date__gte=previous_start, date__lt=current_start)
		current_total = current_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
		previous_total = previous_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
		category_totals = current_expenses.values('category__name').annotate(total=Sum('amount')).order_by('category__name')
		previous_category_totals = {
			item['category__name']: item['total']
			for item in previous_expenses.values('category__name').annotate(total=Sum('amount'))
		}
		insights = []
		for item in category_totals:
			category_name = item['category__name']
			previous_category_total = previous_category_totals.get(category_name, Decimal('0.00'))
			if previous_category_total:
				increase_percentage = ((item['total'] - previous_category_total) / previous_category_total * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
				if increase_percentage > 20:
					display_percentage = int(increase_percentage) if increase_percentage == increase_percentage.to_integral_value() else float(increase_percentage)
					insights.append({
						'category': category_name,
						'increase_percentage': display_percentage,
						'message': f'{category_name} spending increased by {display_percentage:g}% compared to last month.',
					})

		percentage = None
		if previous_total:
			percentage = ((current_total - previous_total) / previous_total * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
		elif current_total == 0:
			percentage = Decimal('0.00')

		return Response({
			'current_month_total': f'₹{current_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP):,.2f}',
			'current_month_by_category': [
				{'category': item['category__name'], 'total': f'₹{item["total"].quantize(Decimal("0.01"), rounding=ROUND_HALF_UP):,.2f}'}
				for item in category_totals
			],
			'previous_month_total': f'₹{previous_total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP):,.2f}',
			'month_over_month_percentage': '0%' if not current_total and not previous_total else None if percentage is None else f'{percentage:+.2f}%',
			'insights': insights,
		})
