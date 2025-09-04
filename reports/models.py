from django.db import models


from authentication.models import User
from devices.models import LostItem, FoundItem

class Report(models.Model):
	REPORT_TYPE_CHOICES = (
		('lost', 'Lost'),
		('found', 'Found'),
		('other', 'Other'),
	)

	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
	# item can be either LostItem or FoundItem, so we use a generic relation
	item_id = models.PositiveIntegerField()
	type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
	details = models.TextField(blank=True, null=True)
	report_date = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Report by {self.user.email} on item {self.item_id} ({self.type})" 

