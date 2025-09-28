from django.db import models
from cloudinary_storage.storage import MediaCloudinaryStorage

from authentication.models import User

# Predefined categories
CATEGORY_CHOICES = [
    ('Phone', 'Phone'),
    ('Laptop', 'Laptop'),
    ('Tablet', 'Tablet'),
    ('Smartwatch', 'Smartwatch'),
    ('Earbuds / Headphones', 'Earbuds / Headphones'),
    ('Camera', 'Camera'),
    ('Other electronics', 'Other electronics'),
]

class Device(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
	serial_number = models.CharField(max_length=100)
	name = models.CharField(max_length=100)
	category = models.CharField(max_length=100)
	brand = models.CharField(max_length=100, blank=True, null=True)
	color = models.CharField(max_length=50, blank=True, null=True)
	description = models.TextField(blank=True, null=True)
	device_image = models.ImageField(upload_to='device_images/', storage=MediaCloudinaryStorage(), blank=True, null=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		unique_together = ('user', 'serial_number')
		verbose_name = 'Device'
		verbose_name_plural = 'Devices'

	def __str__(self):
		return f"{self.name} ({self.serial_number})"



class LostItem(models.Model):
	# Exact schema per frontend (stored as snake_case fields)
	title = models.CharField(max_length=150)
	date_found = models.DateField(blank=True, null=True)
	category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
	time_found = models.TimeField(blank=True, null=True)
	brand = models.CharField(max_length=100, blank=True, null=True)
	image = models.ImageField(upload_to='lost_item_images/', storage=MediaCloudinaryStorage(), blank=True, null=True)
	recepiet = models.FileField(upload_to='lost_item_receipts/', blank=True, null=True)
	additional_info = models.TextField(blank=True, null=True)
	address_type = models.CharField(max_length=100, blank=True, null=True)
	state = models.CharField(max_length=100, blank=True, null=True)
	city_town = models.CharField(max_length=100, blank=True, null=True)
	serial_number = models.CharField(max_length=100, blank=True, null=True)
	first_name = models.CharField(max_length=100, blank=True, null=True)
	last_name = models.CharField(max_length=100, blank=True, null=True)
	phone_number = models.CharField(max_length=20, blank=True, null=True)
	loster_email = models.EmailField(blank=True, null=True, help_text="Email of the person who lost the item")

	# Internal bookkeeping
	date_reported = models.DateTimeField(auto_now_add=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='lost_items', null=True, blank=True)
	status = models.CharField(max_length=50, default='lost')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		user_repr = self.user.email if getattr(self.user, 'email', None) else 'anonymous'
		return f"Lost by {user_repr}"


class FoundItem(models.Model):
	name = models.CharField(max_length=100)
	category = models.CharField(max_length=100, choices=CATEGORY_CHOICES)
	description = models.TextField(blank=True, null=True)
	serial_number = models.CharField(max_length=100, blank=True, null=True)
	contact_email = models.EmailField(blank=True, null=True)
	founder_email = models.EmailField(blank=True, null=True, help_text="Email of the person who found the item")
	location = models.CharField(max_length=200, blank=True, null=True, help_text="Where the item was found")
	phone_number = models.CharField(max_length=20, blank=True, null=True)
	device_image = models.ImageField(upload_to='found_item_images/', storage=MediaCloudinaryStorage(), blank=True, null=True)
	# New optional fields to match frontend schema
	reporter_first_name = models.CharField(max_length=100, blank=True, null=True)
	reporter_last_name = models.CharField(max_length=100, blank=True, null=True)
	province = models.CharField(max_length=100, blank=True, null=True)
	district = models.CharField(max_length=100, blank=True, null=True)
	address = models.CharField(max_length=200, blank=True, null=True)
	date_reported = models.DateTimeField(auto_now_add=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='found_items', null=True, blank=True)
	device = models.ForeignKey(Device, on_delete=models.SET_NULL, null=True, blank=True, related_name='found_items')
	status = models.CharField(max_length=50, default='found')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		user_email = self.user.email if getattr(self.user, 'email', None) else 'anonymous'
		return f"Found: {self.name} by {user_email}"


class Match(models.Model):
	lost_item = models.ForeignKey(LostItem, on_delete=models.CASCADE, related_name='matches')
	found_item = models.ForeignKey(FoundItem, on_delete=models.CASCADE, related_name='matches')
	STATUS_CHOICES = (
		('unclaimed', 'Unclaimed'),
		('claimed', 'Claimed'),
	)
	match_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unclaimed', db_index=True)
	match_date = models.DateTimeField(auto_now_add=True)
	claimed_at = models.DateTimeField(null=True, blank=True)
	# Snapshot fields captured at match time
	loster_name = models.CharField(max_length=200, blank=True, null=True)
	loster_phone_number = models.CharField(max_length=50, blank=True, null=True)
	loster_email = models.EmailField(blank=True, null=True)
	founder_name = models.CharField(max_length=200, blank=True, null=True)
	founder_phone_number = models.CharField(max_length=50, blank=True, null=True)
	founder_email = models.EmailField(blank=True, null=True)
	device_name = models.CharField(max_length=200, blank=True, null=True)
	serial_number = models.CharField(max_length=100, blank=True, null=True)

	def __str__(self):
		return f"Match: Lost({self.lost_item_id}) - Found({self.found_item_id})"

	class Meta:
		unique_together = ('lost_item', 'found_item')
		indexes = [
			models.Index(fields=['match_status']),
			models.Index(fields=['lost_item', 'found_item']),
		]


class Return(models.Model):
	lost_item = models.ForeignKey(LostItem, on_delete=models.CASCADE, related_name='returns')
	found_item = models.ForeignKey(FoundItem, on_delete=models.CASCADE, related_name='returns')
	owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='returns_as_owner', null=True, blank=True)
	finder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='returns_as_finder', null=True, blank=True)
	# Guest/anonymous snapshots
	owner_email = models.EmailField(blank=True, null=True)
	owner_name = models.CharField(max_length=200, blank=True, null=True)
	finder_email = models.EmailField(blank=True, null=True)
	finder_name = models.CharField(max_length=200, blank=True, null=True)
	return_date = models.DateTimeField(auto_now_add=True)
	confirmation = models.BooleanField(default=False)
	# Claim metadata
	claimed_at = models.DateTimeField(auto_now_add=True)
	claimed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='returns_claimed')
	notes = models.TextField(blank=True, null=True)

	def __str__(self):
		return f"Return: Lost({self.lost_item_id}) - Found({self.found_item_id})"


class Contact(models.Model):
	first_name = models.CharField(max_length=100)
	last_name = models.CharField(max_length=100)
	email = models.EmailField()
	subject = models.CharField(max_length=200)
	message = models.TextField()
	created_at = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return f"Contact from {self.first_name} {self.last_name} - {self.subject}"
