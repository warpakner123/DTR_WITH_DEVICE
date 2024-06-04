from datetime import datetime, timedelta
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseBadRequest
from .models import Employee, DTR, Department, Position, LoansTaxes, NightDifferential, Deductions, Benefits
from .forms import AddEmployeeForm, EmployeeForm, UploadFileForm, DTRForm
from django.contrib import messages
from computest import calculate_payroll, format_dates, format_dtr
import pandas as pd
from django.utils import timezone
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.forms import AuthenticationForm
from django.template.loader import render_to_string
import json
import ast
from django.utils.timezone import now
from django.db.models import Count
from django.db.models import ProtectedError
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.shortcuts import render
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

# from django.shortcuts import render
# from django.http import HttpResponse
# from django.template.loader import get_template
# from weasyprint import HTML


def generate_pdf_payroll_view(request):
    try:
        if request.method == 'POST':
            # Get the payroll data from the POST request
            payroll_data_literal = request.POST.get('PaySlip_Data', '')

            # Ensure that we have data to put into our context
            if not payroll_data_literal:
                raise ValueError("No PaySlip data provided.")

           # If we have a string, try to safely convert it to a Python object
            if isinstance(payroll_data_literal, str):
                try:
                    PaySlip_Data = ast.literal_eval(payroll_data_literal)
                except (ValueError, SyntaxError) as e:
                    logging.error(f"Error converting string to Python object: {e}")
                    return HttpResponse("Error parsing PaySlip data.")
            else:
                # If it's not a string, then use it as is (should be a dictionary)
                PaySlip_Data = payroll_data_literal

            # Render the HTML template with the PaySlip data
            html_string = render_to_string('PaySlip_Template.html', {'PaySlip_Data': PaySlip_Data})

            # Generate PDF
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename="payroll_results.pdf"'
            result = pisa.CreatePDF(html_string, dest=response)

            if result.err:
                logging.error(f"Error in PDF generation: {result.err}")
                return HttpResponse("Error generating PDF.")

            return response
        else:
            return HttpResponse("Invalid request method.")
    except Exception as e:
        logging.error(f"Unexpected error in PDF generation: {e}")
        return HttpResponse("Error generating PDF.")

def generate_pdf_dtr_view(request):
    try:
        if request.method == 'POST':
            # Get the payroll data from the POST request
            dtr_data_literal = request.POST.get('dtr_data', '')
            period = request.POST.get('period', '')
            position = request.POST.get('position', '')
            department = request.POST.get('department', '')
            employee_name = request.POST.get('employee_name', '')
            total_hours_weekly_literal = request.POST.get('total_hours_weekly', '')
            grand_total_hours = request.POST.get('grand_total_hours', '')

            # Ensure that we have data to put into our context
            if not all([dtr_data_literal, period, position,department, employee_name, total_hours_weekly_literal, grand_total_hours]):
                raise ValueError("No DTR data provided.")

            if isinstance(dtr_data_literal, str):
                try:
                    DTR_Data = ast.literal_eval(dtr_data_literal)

                except (ValueError, SyntaxError) as e:
                    logging.error(f"Error converting string to Python object: {e}")
                    return HttpResponse("Error parsing DTR data.")
            else:
                DTR_Data = dtr_data_literal

            if isinstance(total_hours_weekly_literal, str):
                try:
                    Weekly_Hours = ast.literal_eval(total_hours_weekly_literal)

                except (ValueError, SyntaxError) as e:
                    logging.error(f"Error converting string to Python object: {e}")
                    return HttpResponse("Error parsing DTR data.")
            else:
                Weekly_Hours = total_hours_weekly_literal

            context = {
                'dtr_data': DTR_Data,
                "period":period,
                "position":position.title(),
                "department":department.title(),
                "employee_name":employee_name.title(),
                "weekly_hours":Weekly_Hours,
                "grand_total_hours":grand_total_hours,
            }

            html_string = render_to_string('DTR_Template.html', context)

            # Generate PDF
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename="payroll_results.pdf"'
            result = pisa.CreatePDF(html_string, dest=response)

            if result.err:
                logging.error(f"Error in PDF generation: {result.err}")
                return HttpResponse("Error generating PDF.")

            return response
        else:
            return HttpResponse("Invalid request method.")
    except Exception as e:
        logging.error(f"Unexpected error in PDF generation: {e}")
        return HttpResponse("Error generating PDF.")

def custom_login(request):
    if request.user.is_authenticated:
        if request.user.employee.department.department_name.lower() == 'hr':
            return redirect('hr_dashboard')
        else:
            logout(request)
            messages.error(request, 'Access denied. Only HR can access the dashboard.')
            return redirect('custom_login')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                if request.user.employee.department.department_name.lower() == 'hr':
                    return redirect('hr_dashboard')
                else:
                    logout(request)
                    messages.error(request, 'Access denied. Only HR can access the dashboard.')
                    return redirect('custom_login')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def hr_dashboard(request):
    if request.user.is_authenticated and request.user.employee.department.department_name.lower() == 'hr':
        employees = Employee.objects.all()
        total_employees = Employee.objects.count()
        active_employees = Employee.objects.filter(status=1).count()
        today_date = now().date()
        today_attendance = DTR.objects.filter(datetime__date=today_date, status='C/In').count()

        for employee in employees:
            employee.full_name = f"{employee.first_name} {employee.last_name}".title()
            employee.department.department_name= employee.department.department_name.title()
            employee.position.position = employee.position.position.title()

        context = {
            'employees': employees,
            "total_employees":total_employees,
            "today_attendance":today_attendance,
            "active_employees":active_employees,
            "today_date":today_date
        }

        return render(request, 'hr_dashboard.html',context)
    else:
        messages.error(request, 'You must be an HR to view this page.')
        return redirect('custom_login')

def attendance(request):
    if request.method == 'POST':
        if 'upload_excel' in request.POST:
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                uploaded_file = request.FILES['excelFile']

                try:
                    df = pd.read_excel(uploaded_file)

                    for index, row in df.iterrows():
                        department = row['Department']
                        name = row['Name']
                        number = row['No.']
                        datetime_str = row['Date/Time']

                        if isinstance(datetime_str, pd.Timestamp):
                            datetime_obj = datetime_str.to_pydatetime()
                        else:
                            try:
                                datetime_obj = timezone.make_aware(datetime.strptime(datetime_str, '%d/%m/%Y %I:%M:%S %p'))
                            except (ValueError, TypeError):
                                datetime_obj = None

                        status = row['Status']
                        location_id = row['Location ID']
                        id_number = row['ID Number'] if not pd.isna(row['ID Number']) else None

                        try:
                            employee = Employee.objects.get(employee_id=number)
                            DTR.objects.create(
                                department=department,
                                name=name,
                                number=number,
                                datetime=datetime_obj,
                                status=status,
                                location_id=location_id,
                                id_number=id_number,
                            )
                        except Employee.DoesNotExist:
                            messages.error(request, f'Employee with ID {number} not found.')

                    messages.success(request, 'Excel file uploaded and processed successfully.')
                except Exception as e:
                    messages.error(request, f'An error occurred: {e}')
                return redirect('attendance')

        elif 'manual_submit' in request.POST:
            number = request.POST.get('employee')
            datetime_str = request.POST.get('datetime')
            status = request.POST.get('status')

            if not all([number, datetime_str, status]):
                messages.error(request, 'All fields are required.')
                return redirect('attendance')

            try:
                datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M')
                employee = Employee.objects.get(employee_id=number)
                department = employee.department.department_name
                name = f"{employee.first_name} {employee.last_name}".title()
                location_id = 0
                id_number = None

                DTR.objects.create(
                    department=department,
                    name=name,
                    number=number,
                    datetime=datetime_obj,
                    status=status,
                    location_id=location_id,
                    id_number=id_number
                )

                messages.success(request, 'Manual DTR entry added successfully.')
                return redirect('attendance')
            except Employee.DoesNotExist:
                messages.error(request, 'Employee not found.')
                return redirect('attendance')
            except ValueError as e:
                messages.error(request, f'Invalid datetime format: {e}')
                return redirect('attendance')
            except Exception as e:
                messages.error(request, f'An error occurred: {e}')
                return redirect('attendance')

        elif 'edit_dtr' in request.POST:
            dtr_id = request.POST.get('dtr_id')
            dtr_instance = get_object_or_404(DTR, pk=dtr_id)
            form = DTRForm(request.POST, instance=dtr_instance)
            if form.is_valid():
                form.save()
                messages.success(request, 'DTR entry successfully edited!')
                return redirect('attendance')

        elif 'delete_dtr' in request.POST:
            dtr_id = request.POST.get('dtr_id')
            dtr_instance = get_object_or_404(DTR, pk=dtr_id)
            dtr_instance.delete()
            messages.success(request, 'DTR entry successfully deleted!')
            return redirect('attendance')
        elif 'confirmBulkDelete' in request.POST:
            delete_all = request.POST.get('isAllChecked')
            ids_to_delete = request.POST.get('ids')

            if ids_to_delete:
                ids_to_delete = ids_to_delete.split(',')
            if delete_all == 'true':
                DTR.objects.all().delete()
            else:
                if ids_to_delete:
                    DTR.objects.filter(id__in=ids_to_delete).delete()

            messages.success(request, 'Selected DTR records have been deleted successfully.')
            return redirect('attendance')

    else:
        # Rendering the attendance page
        form = UploadFileForm()
        dtrs = []
        all_dtrs = DTR.objects.all().order_by('-datetime')
        for dtr in all_dtrs:
            try:
                employee = Employee.objects.get(employee_id=dtr.number)
                dtr.employee = employee
                dtr.employee.full_name = f"{employee.first_name} {employee.last_name}".title()
                dtr.employee.department.department_name = employee.department.department_name.title()
                dtr.employee.position.position = employee.position.position.title()
                dtr.datetime = dtr.datetime.strftime('%B %d, %Y %I:%M %p')
                dtrs.append(dtr)
            except Employee.DoesNotExist:
                continue

        employees = Employee.objects.filter(status=1).exclude(department__department_name__iexact='hr')
        for employee in employees:
            employee.full_name = f"{employee.first_name} {employee.last_name}".title()

        return render(request, 'attendance.html', {'form': form, 'dtrs': dtrs, 'employees': employees})

def payroll(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        employee_id = request.POST.get('employee')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        deduct = request.POST.get('deductions')
        selected_benefits = request.POST.getlist('benefits')  # Retrieve selected benefits

        if not all([employee_id, start_date, end_date]):
            messages.error(request, 'All fields are required.')
            return redirect('payroll')

        try:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

            if start_date_obj > end_date_obj:
                messages.error(request, 'End date must be after start date.')
                return redirect('payroll')

            employee = Employee.objects.get(employee_id=employee_id)

            start_date = datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0)
            end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1, seconds=-1)

            dtr_records = DTR.objects.filter(number=employee_id, datetime__range=[start_date, end_date]).order_by('datetime')

            if not dtr_records.exists():
                messages.error(request, 'No DTR records found for the selected employee and date range.')
                return redirect('payroll')

            # Pass the list of benefit IDs directly
            payroll_data_json = calculate_payroll(dtr_records, start_date, end_date, deduct, selected_benefits)
            payroll_data = json.loads(payroll_data_json)

            if action == 'payslip':
                return render(request, 'generate_payslip.html', {
                    'payroll_data': payroll_data,
                    'employee_name': f"{employee.first_name} {employee.last_name}",
                    'PaySlip_Data': payroll_data[0] if payroll_data else {}
                })
            elif action == 'dtr':
                period = format_dates(start_date, end_date)
                dtr_data_json = format_dtr(dtr_records, start_date, end_date, payroll_data_json)
                loaded_data = json.loads(dtr_data_json)
                grand_total_hours = loaded_data[0]["grand_total_hours"]
                total_hours_weekly = loaded_data[0]["total_hours_weekly"]

                dtr_data = json.loads(dtr_data_json)
                return render(request, 'generate_dtr.html', {
                    'dtr_data': dtr_data,
                    'employee_name': f"{employee.first_name} {employee.last_name}",
                    "position": employee.position.position,
                    "department": employee.department.department_name,
                    "period": period,
                    "grand_total_hours":grand_total_hours,
                    "total_hours_weekly":total_hours_weekly
                })

        except Employee.DoesNotExist:
            messages.error(request, 'Employee not found.')
            return redirect('payroll')
        except ValueError as e:
            messages.error(request, 'Invalid date format. Please use YYYY-MM-DD.')
            return redirect('payroll')
        except Exception as e:
            messages.error(request, f'An error occurred: {str(e)}')
            return redirect('payroll')

    employees = Employee.objects.filter(status=1).exclude(department__department_name__iexact='hr')
    for employee in employees:
        employee.full_name = f"{employee.first_name} {employee.last_name}".title()
        employee.department.department_name = employee.department.department_name.title()
        employee.position.position = employee.position.position.title()

    benefits = Benefits.objects.all()  # Retrieve all benefits to display in the template

    return render(request, 'payroll.html', {'employees': employees, 'benefits': benefits})

def logout_user(request):
    logout(request)
    return redirect('custom_login')

def profile(request):
    if request.method == 'POST':
        if 'edit_employee' in request.POST:
            form = EmployeeForm(request.POST)
            if form.is_valid():
                id = request.POST.get('id')
                employee_id = request.POST.get('employee_id')
                employee = get_object_or_404(Employee, id=id)
                # Check if the employee_id has been changed
                if employee.employee_id != employee_id:
                    # Check if an employee with the same employee_id already exists
                    existing_employee = Employee.objects.filter(employee_id=employee_id).exclude(id=id).first()
                    if existing_employee:
                        return HttpResponseBadRequest("Employee with this ID already exists!")
                form = EmployeeForm(request.POST, instance=employee)
                if form.is_valid():
                    form.save()
                    # Update deductions
                    deduction_ids = [value for key, value in request.POST.items() if key.startswith('loan_tax_')]
                    employee.sample_loans.clear()  # Clear existing deductions
                    for deduction_id in deduction_ids:
                        deduction = LoansTaxes.objects.get(id=deduction_id)
                        Deductions.objects.create(employee=employee, loanTaxes=deduction)
                    messages.success(request, 'Employee details updated successfully!')
                    return redirect('profile')
        elif 'delete_employee' in request.POST:
            id = request.POST.get('id')
            employee = get_object_or_404(Employee, id=id)
            employee.delete()
            messages.success(request, 'Employee successfully removed!')
            return redirect('profile')
        elif 'add_employee' in request.POST:
            employee_id = request.POST.get('employee_id')
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')

            # Check if an employee with the same employee_id already exists
            if Employee.objects.filter(employee_id=employee_id).exists():
                return HttpResponseBadRequest("Employee with this ID already exists!")

            # Check if an employee with the same first name and last name already exists
            if Employee.objects.filter(first_name=first_name, last_name=last_name).exists():
                return HttpResponseBadRequest("Employee with this name already exists!")

            form = AddEmployeeForm(request.POST)  # Instantiate the AddEmployeeForm with POST data
            if form.is_valid():  # Validate the form
                employee = form.save()   # Save the form data to the database
                # deductions_data = request.POST.getlist('deductions')  # Get the list of deductions from the form
                deduction_ids = [value for key, value in request.POST.items() if key.startswith('loan_tax_')]

                for deduction_id in deduction_ids:
                    deduction = LoansTaxes.objects.get(id=deduction_id)  # Retrieve the deduction object from the database
                    Deductions.objects.create(employee=employee, loanTaxes=deduction)  # Create Deductions object
                messages.success(request, 'Employee successfully added!')  # Success message
                return redirect('profile')  # Redirect to the profile page
            else:
                pass
    else:
        employees = Employee.objects.exclude(department__department_name__iexact='hr')
        departments = Department.objects.exclude(department_name__iexact='hr')
        positions = Position.objects.exclude(position__iexact='hr')
        loans_taxes = LoansTaxes.objects.all()

        for employee in employees:
            employee.full_name = f"{employee.first_name} {employee.last_name}".title()
            employee.department.department_name = employee.department.department_name.title()
            employee.position.position = employee.position.position.title()
            employee.deduction_ids = set(employee.sample_loans.values_list('id', flat=True))  # Add this line

        for position in positions:
            position.position = position.position.title()

        for department in departments:
            department.department_name = department.department_name.title()

        for loan_tax in loans_taxes:
            loan_tax.name = loan_tax.name.title()

        context = {
            'employees': employees,
            'departments': departments,
            'positions': positions,
            'loans_taxes': loans_taxes,
        }
        return render(request, 'profile.html', context)

def department(request):
    if request.method == 'POST':
        if 'add_department_submit' in request.POST:
            department_name = request.POST.get('department_name')

            if not department_name:
                messages.error(request, 'Department name is required.')
                return redirect('department')

            if Department.objects.filter(department_name__iexact=department_name).exists():
                messages.error(request, 'A department with this name already exists.')
                return redirect('department')

            try:
                Department.objects.create(department_name=department_name )
                messages.success(request, 'Department added successfully.')
                return redirect('department')
            except Exception as e:
                messages.error(request, f'An error occurred: {e}')
                return redirect('department')
        elif 'edit_department_submit' in request.POST:
            department_id = request.POST.get('edit_department_id')
            department_name = request.POST.get('edit_department_name')

            if not department_name:
                messages.error(request, 'Department name is required.')
                return redirect('department')

            department = get_object_or_404(Department, pk=department_id)

            if Department.objects.exclude(pk=department_id).filter(department_name__iexact=department_name).exists():
                messages.error(request, 'A department with this name already exists.')
                return redirect('department')

            try:
                department.department_name = department_name
                department.save()
                messages.success(request, 'Department updated successfully.')
                return redirect('department')

            except Exception as e:
                messages.error(request, f'An error occurred: {e}')
                return redirect('department')
        elif 'delete_department_submit' in request.POST:
            department_id = request.POST.get('delete_department_id')

            department = get_object_or_404(Department, pk=department_id)

            if department.employee_set.exists():
                messages.error(request, 'Cannot delete department. There are employees associated with it.')
                return redirect('department')

            try:
                department.delete()
                messages.success(request, 'Department deleted successfully.')
                return redirect('department')
            except ProtectedError as e:
                messages.error(request, 'Cannot delete department. There are employees associated with it.')
            except Exception as e:
                messages.error(request, f'An error occurred: {e}')

                return redirect('department')
        elif 'add_position_submit' in request.POST:
            position_name = request.POST.get('position_name')

            if not position_name:
                messages.error(request, 'Position name is required.')
                return redirect('department')

            if Position.objects.filter(position__iexact=position_name).exists():
                messages.error(request, 'A position with this name already exists.')
                return redirect('department')

            try:
                Position.objects.create(position=position_name )
                messages.success(request, 'Position added successfully.')
                return redirect('department')
            except Exception as e:
                messages.error(request, f'An error occurred: {e}')
                return redirect('department')
        elif 'edit_position_submit' in request.POST:
            position_id = request.POST.get('edit_position_id')
            position_name = request.POST.get('edit_position_name')

            if not position_name:
                messages.error(request, 'Position name is required.')
                return redirect('department')

            position = get_object_or_404(Position, pk=position_id)

            if Position.objects.exclude(pk=position_id).filter(position__iexact=position_name).exists():
                messages.error(request, 'A position with this name already exists.')
                return redirect('department')

            try:
                position.position = position_name
                position.save()
                messages.success(request, 'Position updated successfully.')
                return redirect('department')

            except Exception as e:
                messages.error(request, f'An error occurred: {e}')
                return redirect('department')
        elif 'delete_position_submit' in request.POST:
            position_id = request.POST.get('delete_position_id')

            position = get_object_or_404(Position, pk=position_id)

            if position.employee_set.exists():
                messages.error(request, 'Cannot delete position. There are employees associated with it.')
                return redirect('department')

            try:
                position.delete()
                messages.success(request, 'Position deleted successfully.')
                return redirect('department')
            except ProtectedError as e:
                messages.error(request, 'Cannot delete position. There are employees associated with it.')
            except Exception as e:
                messages.error(request, f'An error occurred: {e}')

                return redirect('department')
    else:
        departments = Department.objects.annotate(total=Count('employee'),employees_list=Count('employee__id', distinct=True),)
        positions = Position.objects.annotate(total=Count('employee'),employees_list=Count('employee__id', distinct=True),)

        for position in positions:
            position.position = position.position.title()
            position.employees = position.employee_set.all()

            for employee in position.employees:
                employee.full_name = f"{employee.first_name} {employee.last_name}".title()
                employee.department.department_name= employee.department.department_name.title()
                employee.position.position = employee.position.position.title()

        for department in departments:
            department.department_name = department.department_name.title()
            department.employees = department.employee_set.all()

            for employee in department.employees:
                employee.full_name = f"{employee.first_name} {employee.last_name}".title()
                employee.department.department_name= employee.department.department_name.title()
                employee.position.position = employee.position.position.title()

        context = {
            "departments":departments,
            "positions":positions,
        }
        return render(request, 'department.html',context)

def compensation(request):
    if request.method == 'POST':
        if 'add_loan_tax_submit' in request.POST:
            name = request.POST.get('loan_tax_name')
            amount = request.POST.get('loan_tax_amount')

            if not all([name, amount]):
                messages.error(request, 'All fields are required.')
                return redirect('compensation')

            if LoansTaxes.objects.filter(name__iexact=name).exists():
                messages.error(request, 'A loan/tax with this name already exists.')
                return redirect('compensation')

            try:
                LoansTaxes.objects.create(name=name, amount=amount )
                messages.success(request, 'Loan/Taxes added successfully.')
                return redirect('compensation')

            except Exception as e:
                messages.error(request, f'An error occurred: {e}')
                return redirect('compensation')
        elif 'edit_loan_tax_submit' in request.POST:
            id = request.POST.get('edit_loan_tax_id')
            name = request.POST.get('edit_loan_tax_name')
            amount = request.POST.get('edit_loan_tax_amount')

            if not all([name, amount]):
                messages.error(request, 'All fields are required.')
                return redirect('compensation')

            loans_taxes = get_object_or_404(LoansTaxes, pk=id)

            if LoansTaxes.objects.exclude(pk=id).filter(name__iexact=name).exists():
                messages.error(request, 'A loan/tax with this name already exists.')
                return redirect('compensation')

            try:
                loans_taxes.name = name
                loans_taxes.amount = amount
                loans_taxes.save()
                messages.success(request, 'Loan/Tax updated successfully.')
                return redirect('compensation')

            except Exception as e:
                messages.error(request, f'An error occurred: {e}')
                return redirect('compensation')
        elif 'delete_loan_tax_submit' in request.POST:
            id = request.POST.get('delete_loan_tax_id')

            loans_taxes = get_object_or_404(LoansTaxes, pk=id)

            try:
                loans_taxes.delete()
                messages.success(request, 'Loan/Taxes deleted successfully.')
                return redirect('compensation')
            except Exception as e:
                messages.error(request, f'An error occurred: {e}')

                return redirect('compensation')
        elif 'add_benefit_submit' in request.POST:
            name = request.POST.get('benefit_name')
            amount = request.POST.get('benefit_amount')

            if not all([name, amount]):
                messages.error(request, 'All fields are required.')
                return redirect('compensation')

            if Benefits.objects.filter(name__iexact=name).exists():
                messages.error(request, 'A benefit with this name already exists.')
                return redirect('compensation')

            try:
                Benefits.objects.create(name=name, amount=amount )
                messages.success(request, 'Benefit added successfully.')
                return redirect('compensation')

            except Exception as e:
                messages.error(request, f'An error occurred: {e}')
                return redirect('compensation')
        elif 'edit_benefit_submit' in request.POST:
            id = request.POST.get('edit_benefit_id')
            name = request.POST.get('edit_benefit_name')
            amount = request.POST.get('edit_benefit_amount')

            if not all([name, amount]):
                messages.error(request, 'All fields are required.')
                return redirect('compensation')

            benefit = get_object_or_404(Benefits, pk=id)

            if Benefits.objects.exclude(pk=id).filter(name__iexact=name).exists():
                messages.error(request, 'A benefit with this name already exists.')
                return redirect('compensation')

            try:
                benefit.name = name
                benefit.amount = amount
                benefit.save()
                messages.success(request, 'Benefit updated successfully.')
                return redirect('compensation')

            except Exception as e:
                messages.error(request, f'An error occurred: {e}')
                return redirect('compensation')
        elif 'delete_benefit_submit' in request.POST:
            id = request.POST.get('delete_benefit_id')

            benefit = get_object_or_404(Benefits, pk=id)

            try:
                benefit.delete()
                messages.success(request, 'Benefit deleted successfully.')
                return redirect('compensation')
            except Exception as e:
                messages.error(request, f'An error occurred: {e}')
                return redirect('compensation')
    else:
        loans_taxes = LoansTaxes.objects.annotate(total=Count('employee'),employees_list=Count('employee__id', distinct=True),)
        benefit = Benefits.objects.all()

        for loan_tax in loans_taxes:
            loan_tax.name = loan_tax.name.title()
        for data in benefit:
            data.name = data.name.title()

        context = {
            "benefit":benefit,
            "loans_taxes":loans_taxes,
        }
        return render(request, 'compensation.html', context)