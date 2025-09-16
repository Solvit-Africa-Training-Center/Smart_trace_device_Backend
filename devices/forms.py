from django import forms
from .models import LostItem, FoundItem


class LostItemForm(forms.ModelForm):
	class Meta:
		model = LostItem
		fields = [
			'name', 'category', 'description', 'color', 'serial_number', 'contact_email', 'device'
		]

	def clean_contact_email(self):
		email = self.cleaned_data.get('contact_email')
		if not email:
			raise forms.ValidationError('Contact email is required to submit a lost item.')
		return email


class FoundItemForm(forms.ModelForm):
	class Meta:
		model = FoundItem
		fields = [
			'name', 'category', 'description', 'color', 'serial_number', 'contact_email', 'device'
		]


