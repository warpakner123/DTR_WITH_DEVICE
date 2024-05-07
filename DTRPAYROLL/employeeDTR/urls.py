from django.urls import path
from . import views

urlpatterns = [
    path('', views.custom_login, name='custom_login'),
    path('hr-dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('attendance/', views.attendance, name='attendance'),
    path('payroll/', views.payroll, name='payroll'),
    path('logout/', views.logout_user, name='logout'),
    path('generate-pdf-payroll/', views.generate_pdf_payroll_view, name='generate-pdf-payroll'),
    path('edit_dtr/<int:dtr_id>/', views.edit_dtr, name='edit_dtr'),
    path('delete_dtr/<int:dtr_id>/', views.delete_dtr, name='delete_dtr'),
    path('profile/', views.profile, name='profile'),
    path('delete_employee/<int:employee_id>/', views.delete_employee, name='delete_employee'),
    path('edit_employee/<int:employee_id>/', views.edit_employee, name='edit_employee'),
    path('department/', views.department, name='department'),
    path('compensation/', views.compensation, name='compensation'),
]
