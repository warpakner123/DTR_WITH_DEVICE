import os
import django
from django.db.models import Sum
from datetime import datetime, date
from collections import defaultdict
import calendar
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Import models
from employeeDTR.models import Employee, Deductions, DTR

def print_loans_taxes_data(employee):
    """Print loan and tax deductions for a given employee."""
    loans_taxes = Deductions.objects.filter(employee=employee)
    for deduction in loans_taxes:
        loan_tax = deduction.loanTaxes
        print(f"{loan_tax.name} : ₱{loan_tax.amount:.2f}")

# def calculate_hours_for_day(dtr_entries):
#     """Calculate regular and overtime hours for a given day."""
#     if not dtr_entries:
#         return 0, 0
#     check_in = min(dtr_entries, key=lambda x: x.datetime).datetime
#     check_out = max(dtr_entries, key=lambda x: x.datetime).datetime
#     total_hours = ((check_out - check_in).total_seconds() / 3600)
#     regular_hours = min(total_hours, 8)
#     overtime_hours = max(0, total_hours - regular_hours)
#     return regular_hours, overtime_hours

def calculate_hours_for_day(dtr_entries):
    """Calculate regular and overtime hours for a given day."""
    if not dtr_entries:
        return 0, 0

    # Sort DTR entries by datetime
    sorted_entries = sorted(dtr_entries, key=lambda x: x.datetime)

    # Separate DTR entries into morning and afternoon sessions
    morning_entries = []
    afternoon_entries = []
    for entry in sorted_entries:
        if entry.datetime.hour <= 12:
            morning_entries.append(entry)
        else:
            afternoon_entries.append(entry)

    # Calculate total hours worked for morning session
    if len(morning_entries) >= 2:
        morning_check_in = min(morning_entries, key=lambda x: x.datetime).datetime
        morning_check_out = max(morning_entries, key=lambda x: x.datetime).datetime
        morning_hours = ((morning_check_out - morning_check_in).total_seconds() / 3600)
    else:
        morning_hours = 0

    # Calculate total hours worked for afternoon session
    if len(afternoon_entries) >= 2:
        afternoon_check_in = min(afternoon_entries, key=lambda x: x.datetime).datetime
        afternoon_check_out = max(afternoon_entries, key=lambda x: x.datetime).datetime
        afternoon_hours = ((afternoon_check_out - afternoon_check_in).total_seconds() / 3600)
    else:
        afternoon_hours = 0

    # Calculate total hours worked
    total_hours = morning_hours + afternoon_hours

    # Calculate regular and overtime hours
    if total_hours <= 8:
        regular_hours = total_hours
        overtime_hours = 0
    else:
        regular_hours = 8
        overtime_hours = total_hours - 8

    return regular_hours, overtime_hours


def calculate_payroll(dtr_records, start_date, end_date):
    """Calculate payroll for all employees within a specified period."""
    payroll_data = []

    # Group DTR records by employee and date
    grouped_by_employee = defaultdict(lambda: defaultdict(list))
    for record in dtr_records:
        grouped_by_employee[record.number][record.datetime.date()].append(record)

    # Process each employee
    for employee_id, dates in grouped_by_employee.items():
        employee = Employee.objects.filter(employee_id=employee_id).first()
        if not employee:
            continue  # Skip if employee not found

        total_regular_hours = 0
        total_overtime_hours = 0

        # Determine payroll period
        last_day_of_month = calendar.monthrange(start_date.year, start_date.month)[1]
        if start_date.day == 1 and (15 >= end_date.day or end_date.day < last_day_of_month):
            period = '1-15'
            period_end = datetime(start_date.year, start_date.month, 15).date()  # Convert to date
        elif start_date.day == 16 and end_date.day <= last_day_of_month:
            period = f'16-{last_day_of_month}'
            period_end = datetime(start_date.year, start_date.month, last_day_of_month).date()  # Convert to date
        elif start_date.day == 1 and end_date.day == last_day_of_month:
            period = 'Full Month'
            period_end = end_date.date()  # Assuming end_date is a datetime object; convert to date
        else:
            period = 'Custom Period'
            period_end = end_date.date()  # Convert to date

        for date, dtr_entries in dates.items():
            # Ensure date is compared with period_end as date objects
            if date > period_end:
                continue
            regular_hours, overtime_hours = calculate_hours_for_day(dtr_entries)
            total_regular_hours += regular_hours
            total_overtime_hours += overtime_hours

        gross_pay_regular = total_regular_hours * employee.hourly_rate
        gross_pay_overtime = total_overtime_hours * employee.Overtime_rate
        total_deductions = 0 if period == f'16-{last_day_of_month}' else Deductions.objects.filter(employee=employee).aggregate(Sum('loanTaxes__amount'))['loanTaxes__amount__sum'] or 0
        net_pay = gross_pay_regular + gross_pay_overtime - total_deductions

        payroll_data.append({
            'employee_id': employee_id,
            'complete_name': f"{employee.first_name} {employee.last_name}",
            'pay_period': period,
            'period_start': start_date.strftime("%Y-%m-%d"),
            'period_end': period_end.strftime("%Y-%m-%d"),
            'total_hours_worked': total_regular_hours + total_overtime_hours,
            'regular_hours': total_regular_hours,
            'overtime_hours': total_overtime_hours,
            'gross_pay_regular': gross_pay_regular,
            'gross_pay_overtime': gross_pay_overtime,
            'gross_pay': gross_pay_regular + gross_pay_overtime,
            'deductions_details': [{'name': deduction.loanTaxes.name, 'amount': deduction.loanTaxes.amount} for deduction in Deductions.objects.filter(employee=employee)],
            'total_deductions': total_deductions,
            'net_pay': net_pay,
        })

        payroll_data_json = json.dumps(payroll_data, ensure_ascii=False)
        return payroll_data_json
