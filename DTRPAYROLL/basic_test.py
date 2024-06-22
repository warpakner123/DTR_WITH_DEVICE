# -*- coding: utf-8 -*-
import sys
sys.path.append("zk")

from zk import ZK, const

conn = None
zk = ZK('192.168.1.201', port=4370, timeout=5, password=0, force_udp=True, ommit_ping=False)
try:
    print ('Connecting to device ...')
    conn = zk.connect()
    print ('Disabling device ...')
    conn.disable_device()
    print ('Firmware Version: : {}'.format(conn.get_firmware_version()))
    # print '--- Get User ---'
    users = conn.get_users()
    for user in users:
        privilege = 'User'
        if user.usertype() == const.USER_ADMIN:
            privilege = 'Admin'
        elif user.usertype() == const.USER_MANAGER:
            privilege = 'Manager'
        elif user.usertype() == const.USER_ENROLLER:
            privilege = 'Enroller'
        if user.is_disabled():
            privilege += '(DISABLED)'
        print ('- UID #{}'.format(user.uid))
        print ('  Name       : {}'.format(user.name))
        print ('  Privilege  : {}'.format(privilege))
        print ('  Password   : {}'.format(user.password))
        print ('  Group ID   : {}'.format(user.group_id))
        print ('  User  ID   : {}'.format(user.user_id))

    print ("Voice Test ...")
    conn.test_voice()
    print ('Enabling device ...')
    conn.enable_device()
except Exception as e:
    print ("Process terminate : {}".format(e))
finally:
    if conn:
        conn.disconnect()
