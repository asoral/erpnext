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
def pole_display(item,amount,grand_total,pos_profile):
    if item:
        dat = frappe.get_last_doc('POS Opening Entry')
        print('!!!!!!!!!!!pos_opening_entry',dat)
        doc = frappe.get_doc('Item',item)
        port = frappe.get_value('POS Profile',pos_profile,'port_display')
        print('AAAAAAAAAAAAport',port)
        if port:
            #initialize the serial port
            s = serial.Serial()
            # COMPORT = int(input("Please enter the port number: ")) #this refers to which port your usb is inserted into
            # ser.port = "COM{}".format(COMPORT-1)
            s.port = str(port)
            s.baudrate = 9600
            s.open()
            
            #a="Item:"+str(doc.item_name)+" Amt:"+str(amount)+" GT:"+str(grand_total)

            a="Item:"+str(doc.item_name)
            if len(a)<20:
                b=20-len(a)
                for i in range(1,b+1):
                    a+=" "
            s.write(a.encode())
            

            c  = "Price:"+str(amount)
            if len(c)<20:
                d=20-len(c)
                for j in range(1,d+1):
                    c+=" "
            s.write(c.encode())
            s.close()
        
        print('jjjjjjjjjjjjj')

@frappe.whitelist()
def pole_clear(pos_profile):
    print('iiiiiiiiiiiiiiiiiiiii')
    port = frappe.get_value('POS Profile',pos_profile,'port_display')
    if port:
        s = serial.Serial()
        s.port = port
        s.baudrate = 9600
        s.open()
        a=""
        if len(a)<40:
            b=40-len(a)
            for i in range(1,b+1):
                a+=" "
        s.write(a.encode())   
   
@frappe.whitelist()
def check(grand_total,pos_profile):
    print('((((((((((((((*************')
    if item:
        doc = frappe.get_doc('Item',item)
        port = frappe.get_value('POS Profile',pos_profile,'port_display')
        if port:
            s = serial.Serial()
            s.port = port
            s.baudrate = 9600
            s.open()
            d  = "Total:"+str(grand_total)
            if len(d)<20:
                e=40-len(d)
                for j in range(1,e+1):
                    d+=" "
            s.write(d.encode())
            s.close()