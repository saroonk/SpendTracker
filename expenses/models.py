from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
	name = models.CharField(max_length=100, unique=True)
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.name


class Expense(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expenses')
	category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='expenses')
	amount = models.DecimalField(max_digits=10, decimal_places=2)
	note = models.TextField(blank=True)
	date = models.DateField()
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f'{self.user.username}: {self.amount} on {self.date}'
