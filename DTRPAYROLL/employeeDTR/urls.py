from django.urls import path
from . import views

urlpatterns = [
    path('', views.custom_login, name='custom_login'),
    path('hr-dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('attendance/', views.attendance, name='attendance'),
    path('payroll/', views.payroll, name='payroll'),
    path('logout/', views.logout_user, name='logout'),
    path('generate-pdf-payroll/', views.generate_pdf_payroll_view, name='generate-pdf-payroll'),
    path('generate-pdf-dtr/', views.generate_pdf_dtr_view, name='generate-pdf-dtr'),
    path('profile/', views.profile, name='profile'),
    path('department/', views.department, name='department'),
    path('compensation/', views.compensation, name='compensation'),
    path('device/',views.device, name='device')
]
