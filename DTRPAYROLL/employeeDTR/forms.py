# forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import DTR, Employee

class UploadFileForm(forms.Form):
    excelFile = forms.FileField(label='', widget=forms.FileInput(attrs={'accept': '.xls, .xlsx'}))

class DTRForm(forms.ModelForm):
    class Meta:
        model = DTR
        fields = ['datetime', 'status']
        widgets = {
            'datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'status': forms.Select(choices=[('C/In', 'Check-in'), ('C/Out', 'Check-out')]),
        }

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['employee_id','first_name', 'last_name', 'email', 'dob', 'address', 'department', 'position', 'hourly_rate', 'Overtime_rate', 'employee_type', 'date_hired', 'status']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'date_hired': forms.DateInput(attrs={'type': 'date'}),
            'department': forms.Select(attrs={'class': 'form-control mb-3', 'required': True}),
            'position': forms.Select(attrs={'class': 'form-control mb-3', 'required': True}),
            'hourly_rate': forms.NumberInput(attrs={'step': '0.01'}),
            'Overtime_rate': forms.NumberInput(attrs={'step': '0.01'}),
            'employee_type': forms.Select(attrs={'class': 'form-control mb-3', 'required': True}),
        }

class AddEmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['employee_id', 'first_name', 'last_name', 'email', 'dob', 'address', 'department', 'position', 'hourly_rate', 'Overtime_rate', 'employee_type', 'date_hired']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date'}),
            'date_hired': forms.DateInput(attrs={'type': 'date'}),
            'department': forms.Select(attrs={'class': 'form-control mb-3', 'required': True}),
            'position': forms.Select(attrs={'class': 'form-control mb-3', 'required': True}),
            'hourly_rate': forms.NumberInput(attrs={'step': '0.01'}),
            'Overtime_rate': forms.NumberInput(attrs={'step': '0.01'}),
            'employee_type': forms.Select(attrs={'class': 'form-control mb-3', 'required': True}),
        }
