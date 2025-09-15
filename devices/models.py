from django.db import models


from authentication.models import User

class Device(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
	serial_number = models.CharField(max_length=100)
	name = models.CharField(max_length=100)
	category = models.CharField(max_length=100)
	brand = models.CharField(max_length=100, blank=True, null=True)
	color = models.CharField(max_length=50, blank=True, null=True)
	description = models.TextField(blank=True, null=True)
	device_image = models.ImageField(upload_to='device_images/', blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		unique_together = ('user', 'serial_number')
		verbose_name = 'Device'
		verbose_name_plural = 'Devices'

	def __str__(self):
		return f"{self.name} ({self.serial_number})"


class LostItem(models.Model):
	name = models.CharField(max_length=100)
	category = models.CharField(max_length=100)
	description = models.TextField(blank=True, null=True)
	color = models.CharField(max_length=50, blank=True, null=True)
	date_reported = models.DateTimeField(auto_now_add=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lost_items')
	device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, related_name='lost_items')
	status = models.CharField(max_length=50, default='lost')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Lost: {self.name} by {self.user.email}"


class FoundItem(models.Model):
	name = models.CharField(max_length=100)
	category = models.CharField(max_length=100)
	description = models.TextField(blank=True, null=True)
	color = models.CharField(max_length=50, blank=True, null=True)
	date_reported = models.DateTimeField(auto_now_add=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='found_items')
	device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, related_name='found_items')
	status = models.CharField(max_length=50, default='found')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f"Found: {self.name} by {self.user.email}"


class Match(models.Model):
	lost_item = models.ForeignKey(LostItem, on_delete=models.CASCADE, related_name='matches')
	found_item = models.ForeignKey(FoundItem, on_delete=models.CASCADE, related_name='matches')
	match_status = models.CharField(max_length=50)
	match_date = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Match: Lost({self.lost_item_id}) - Found({self.found_item_id})"


class Return(models.Model):
	lost_item = models.ForeignKey(LostItem, on_delete=models.CASCADE, related_name='returns')
	found_item = models.ForeignKey(FoundItem, on_delete=models.CASCADE, related_name='returns')
	owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='returns_as_owner')
	finder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='returns_as_finder')
	return_date = models.DateTimeField(auto_now_add=True)
	confirmation = models.BooleanField(default=False)

	def __str__(self):
		return f"Return: Lost({self.lost_item_id}) - Found({self.found_item_id})"
