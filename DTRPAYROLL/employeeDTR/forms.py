# forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import DTR

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