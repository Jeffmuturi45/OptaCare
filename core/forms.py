from django import forms
from core.models import Patient, Visit, CustomUser


class PatientRegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=200)
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}))
    gender = forms.ChoiceField(choices=[
        ('', 'Select…'),
        ('male',   'Male'),
        ('female', 'Female'),
        ('other',  'Other'),
    ])
    phone = forms.CharField(max_length=20)
    national_id = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)
    payment_type = forms.ChoiceField(choices=[
        ('cash',      'Cash / M-Pesa'),
        ('insurance', 'Insurance'),
        ('deposit',   'Deposit / Prepaid'),
    ])
    insurance_no = forms.CharField(max_length=60, required=False)

    # Visit fields
    visit_type = forms.ChoiceField(choices=[
        ('walk_in',         'Walk-in (see doctor today)'),
        ('appointment',     'Book appointment'),
        ('dispensing_only', 'Dispensing only'),
    ])
    assigned_doctor = forms.IntegerField(required=False)
    notes = forms.CharField(
        widget=forms.Textarea, required=False, max_length=500)

    def clean_phone(self):
        phone = self.cleaned_data['phone'].strip().replace(' ', '')
        if len(phone) < 9:
            raise forms.ValidationError('Enter a valid phone number.')
        return phone

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('payment_type') == 'insurance' and not cleaned.get('insurance_no'):
            self.add_error('insurance_no', 'Insurance number required.')
        return cleaned
