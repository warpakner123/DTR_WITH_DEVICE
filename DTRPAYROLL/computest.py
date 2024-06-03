import os
import django
from django.db.models import Sum
from datetime import datetime, date
from collections import defaultdict
import calendar
import json
from datetime import datetime, timedelta
from django.http import JsonResponse


# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# Import models
from employeeDTR.models import Employee, Deductions, Benefits

def print_loans_taxes_data(employee):
    """Print loan and tax deductions for a given employee."""
    loans_taxes = Deductions.objects.filter(employee=employee)
    for deduction in loans_taxes:
        loan_tax = deduction.loanTaxes
        print(f"{loan_tax.name} : {loan_tax.amount:.2f}")

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

def calculate_payroll(dtr_records, start_date, end_date, deduct, selected_benefits):
    """Calculate payroll for all employees within a specified period."""
    payroll_data = []

    # Group DTR records by employee and date
    grouped_by_employee = defaultdict(lambda: defaultdict(list))
    for record in dtr_records:
        grouped_by_employee[record.number][record.datetime.date()].append(record)

    # Fetch selected benefits objects
    selected_benefits_objects = Benefits.objects.filter(id__in=selected_benefits)

    # Process each employee
    for employee_id, dates in grouped_by_employee.items():
        employee = Employee.objects.filter(employee_id=employee_id).first()
        if not employee:
            continue  # Skip if employee not found

        total_regular_hours = 0
        total_overtime_hours = 0
        total_additions = 0

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
        total_deductions = 0 if deduct == 'no' else Deductions.objects.filter(employee=employee).aggregate(Sum('loanTaxes__amount'))['loanTaxes__amount__sum'] or 0

        # Add selected benefits to total_additions
        selected_benefits_total = sum([benefit.amount for benefit in selected_benefits_objects])
        total_additions += selected_benefits_total

        net_pay = gross_pay_regular + gross_pay_overtime + total_additions - total_deductions

        payroll_data.append({
            'employee_id': employee_id,
            'complete_name': f"{employee.first_name} {employee.last_name}",
            'pay_period': period,
            'period_start': start_date.strftime("%Y-%m-%d"),
            'period_end': period_end.strftime("%Y-%m-%d"),
            'total_hours_worked': f"{total_regular_hours + total_overtime_hours:.2f}",
            'regular_hours': f"{total_regular_hours:.2f}",
            'overtime_hours': f"{total_overtime_hours:.2f}",
            'basic_pay_regular': f" {gross_pay_regular:,.2f}",
            'basic_pay_overtime': f" {gross_pay_overtime:,.2f}",
            'basic_pay': f" {gross_pay_regular + gross_pay_overtime:,.2f}",
            'gross_pay': f" {gross_pay_regular + gross_pay_overtime + total_additions:,.2f}",
            'deductions_details': [{'name': deduction.loanTaxes.name, 'amount': f" {deduction.loanTaxes.amount:,.2f}"} for deduction in Deductions.objects.filter(employee=employee)],
            'total_deductions': f" {total_deductions:,.2f}",
            'addition_details': [{'name': benefit.name, 'amount': f" {benefit.amount:,.2f}"} for benefit in selected_benefits_objects],
            'total_additions': f" {total_additions:,.2f}",
            'net_pay': f" {net_pay:,.2f}",
            'deduct': deduct,
        })

    payroll_data_json = json.dumps(payroll_data, ensure_ascii=False)
    return payroll_data_json

def format_dtr(dtr_records, start_date, end_date, payroll_data):
    dtr_data = []

    loaded_data = json.loads(payroll_data)
    total_hours_worked = loaded_data[0]["total_hours_worked"]

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

        weekly_hours = defaultdict(lambda: {'regular_hours': 0, 'overtime_hours': 0})

        for date, dtr_entries in dates.items():
            # Ensure date is compared with period_end as date objects
            if date > period_end:
                continue
            regular_hours, overtime_hours = calculate_hours_for_day(dtr_entries)
            total_regular_hours += regular_hours
            total_overtime_hours += overtime_hours

            # Calculate week number and update weekly hours
            week_start = date - timedelta(days=date.weekday())  # Monday of the current week
            week_end = week_start + timedelta(days=6)
            weekly_hours[(week_start, week_end)]['regular_hours'] += regular_hours
            weekly_hours[(week_start, week_end)]['overtime_hours'] += overtime_hours

        total_hours_worked = total_regular_hours + total_overtime_hours
        week_index = 1
        formatted_weekly_hours = []

        for (week_start, week_end), hours in weekly_hours.items():
            formatted_weekly_hours.append({
                'week_no': f"Week {week_index}",
                'date_range': f"{week_start.strftime('%b %d, %Y')} - {week_end.strftime('%b %d, %Y')}",
                'total_hours': f"{hours['regular_hours'] + hours['overtime_hours']:.2f}",
                'regular_hours': f"{hours['regular_hours']:.2f}",
                'overtime_hours': f"{hours['overtime_hours']:.2f}"
            })
            week_index += 1


        payroll_data.append({
            'weekly_hours': formatted_weekly_hours
        })
        # 'total_hours_worked': f"{total_regular_hours + total_overtime_hours:.2f}",


    # loaded_hours_data = json.loads(payroll_data)
    total_hours_weekly = payroll_data[0]["weekly_hours"]

    for data in dtr_records:
        day = data.datetime.strftime('%a'),
        date = data.datetime.strftime('%d/%m/%Y'),
        time = data.datetime.strftime('%I:%M %p'),
        mode = "In" if data.status == "C/In" else "Out",
        remarks = "MODE IN" if data.status == "C/In" else "MODE OUT",

        newData = {
        "day": day[0],  # Extracting the string directly
        "date": date[0],  # Extracting the string directly
        "time": time[0],  # Extracting the string directly
        "mode": mode[0],  # Extracting the string directly
        "remarks": remarks[0]  ,# Extracting the string directly
        "grand_total_hours":total_hours_worked,
        "total_hours_weekly": total_hours_weekly
    }

        dtr_data.append(newData)
    dtr_data_json = json.dumps(dtr_data, ensure_ascii=False)
    return dtr_data_json

def format_dates(date1, date2):
    # Ensure input dates are datetime objects
    if isinstance(date1, str):
        date1 = datetime.strptime(date1, "%Y-%m-%d")
    if isinstance(date2, str):
        date2 = datetime.strptime(date2, "%Y-%m-%d")

    date_format = "%b %d, %Y"  # Example: Jan 01, 2024

    if date1.year == date2.year:
        if date1.month == date2.month:
            if date1.day == date2.day:
                # Same day (e.g., Jan 01, 2024)
                return date1.strftime(date_format)
            else:
                # Same month and year (e.g., Jan 01 - 31, 2024)
                return f"{date1.strftime('%b %d')} - {date2.strftime('%d')}, {date1.year}"
        else:
            # Different months but same year (e.g., Jan 01 - Dec 01, 2024)
            return f"{date1.strftime('%b %d')} - {date2.strftime('%b %d')}, {date1.year}"
    else:
        # Different months and years (e.g., Jan 01, 2023 - Dec 01, 2024)
        return f"{date1.strftime(date_format)} - {date2.strftime(date_format)}"
