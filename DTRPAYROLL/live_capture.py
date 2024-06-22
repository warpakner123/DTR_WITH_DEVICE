from posixpath import abspath
import sys
import os
import time
import os
import django
from django.db.models import Sum
from datetime import datetime, date
from collections import defaultdict
import calendar
import json
from datetime import datetime, timedelta
from django.http import JsonResponse
from zk import ZK, const


sys.path.insert(1,abspath("./pyzk"))
conn = None
zk = ZK('192.168.1.201', port=4370, timeout=5, password=0, force_udp=True, ommit_ping=False)
try:
    conn = zk.connect()
    conn.set_time(datetime.now())
    print("Updating Time!")
    print("Time Updated!")
    print("Running Live Capture!")
    for attendance in conn.live_capture():
        if attendance is None:
            pass
        else:
            print (attendance)
except Exception as e:
    print ("Process terminate : {}".format(e))
finally:
    if conn:
        conn.disconnect()
