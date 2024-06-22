Setting up the project:

#create venv first:
python -m venv env

#activate the venv
.\env\Scripts\activate

#go inside the app folder:
cd .\DTRPAYROLL\

#install the requirements.txt
pip install -r requirements.txt

#create localDB  table in MYSQL using xampp 
and using this as the table name "dtr_payroll"

#migrate
python manage.py makemigrations
python manage.py migrate

#install pyzk source : https://github.com/fananimi/pyzk extracted file should be in django project
pip install -U pyzk

#runserver
python manage.py runserver
