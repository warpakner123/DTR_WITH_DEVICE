from django.db import models
from datetime import datetime
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import User

class Department(models.Model):
    department_name = models.CharField(max_length=255)

    def __str__(self):
        return self.department_name

class Position(models.Model):
    position = models.CharField(max_length=255)

    def __str__(self):
        return self.position

class LoansTaxes(models.Model):
    name=models.CharField(max_length=255)
    amount=models.FloatField()

    def __str__(self):
        return self.name

class Employee(models.Model):
    STATUS_CHOICES = [
        (1, "Active"),
        (0, "Inactive"),
    ]

    EMP_TYPE_CHOICES = [
        ("Part-Time", "Part-Time"),
        ("Full-Time", "Full-Time"),
        ("Flex-Time", "Flex-Time"),
        ("Project-Based", "Project-Based"),
    ]
    employee_id = models.IntegerField(null=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    dob = models.DateField()
    date_hired = models.DateField()
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, null=True, blank=True)
    position = models.ForeignKey(Position, on_delete=models.CASCADE, null=True, blank=True)
    hourly_rate = models.FloatField(default=0.0)
    Overtime_rate = models.FloatField(default=0.0)
    employee_type = models.CharField(max_length=100, choices=EMP_TYPE_CHOICES, default="Part-Time")
    email = models.EmailField(max_length=255)
    sample_loans=models.ManyToManyField(LoansTaxes,related_name="employee", through="Deductions")
    system_id=models.IntegerField(null=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class DTR(models.Model):
    department = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    number = models.IntegerField() #using the as the employee_id
    datetime = models.DateTimeField(default=datetime.now)  # Add default value
    status = models.CharField(max_length=10)   #only has C/In or Checked In, no Checked Out status
    location_id = models.IntegerField()  #branch location
    id_number = models.IntegerField(null=True)  # Making id_number nullable

    def __str__(self):
        return f"{self.number} - {self.datetime.strftime('%d/%m/%Y %I:%M:%S %p')}"

class Deductions(models.Model):
    employee=models.ForeignKey(Employee, on_delete=models.CASCADE, null=True)
    loanTaxes=models.ForeignKey(LoansTaxes, on_delete=models.CASCADE, null=True)