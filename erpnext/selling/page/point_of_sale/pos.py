import serial
import os
from time import sleep
import click
import frappe


#global constants
control_byte = '\n'
ACL_1_X_addr = ord('X')
ACL_1_Y_addr = ord('Y')
ACL_1_Z_addr = ord('Z')
GYRO_1_X_addr = ord('I')
GYRO_1_Y_addr = ord('J')
GYRO_1_Z_addr = ord('K')

@frappe.whitelist()
def pole_display(item,amount,grand_total):
    if item:
        doc = frappe.get_doc('Item',item)
    
        #initialize the serial port
        s = serial.Serial()
        s.port = "/dev/ttyUSB0"
        s.baudrate = 9600
        s.open()
        
         #a="Item:"+str(doc.item_name)+" Amt:"+str(amount)+" GT:"+str(grand_total)
       
        c  = "Price:"+str(amount)
        if len(c)<20:
            d=20-len(c)
            for j in range(1,d+1):
               c+=" "
        s.write(c.encode())
       
        a="Item:"+str(doc.item_name)
        if len(a)<20:
            b=20-len(a)
            for i in range(1,b+1):
               a+=" "
        s.write(a.encode())
        s.close()
       

@frappe.whitelist()
def clear():
    s = serial.Serial()
    s.port = "/dev/ttyUSB0"
    s.baudrate = 9600
    s.open()
    a=""
    if len(a)<40:
        b=40-len(a)
        for i in range(1,b+1):
            a+=" "
    s.write(a.encode())   
   