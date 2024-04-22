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
python manage.py migrate

#runserver
python manage.py runserver