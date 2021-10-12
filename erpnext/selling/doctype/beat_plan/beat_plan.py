# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import getdate
import datetime
from frappe.model.document import Document

class BeatPlan(Document):
	@frappe.whitelist()
	def fill_child_t(self):
		doc = frappe.get_doc('Beat',{'name':self.beat_id})
		date1 = str(self.beat_start_date)
		print("Yes",date1)
		date2 = str(self.beat_end_date)
		start = datetime.datetime.strptime(date1, '%Y-%m-%d').date()
		end = datetime.datetime.strptime(date2, '%Y-%m-%d').date()
		step = datetime.timedelta(days=1)
		t_list = []
		d_list = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
		for i in doc.beatct:
			if i.sales_person == self.sales_person:
				t_list.append(i.monday)
				t_list.append(i.tuesday)
				t_list.append(i.wednesday)
				t_list.append(i.thursday)
				t_list.append(i.friday)
				t_list.append(i.saturday)
		date_list=[]
		while start <= end:
			date = start.strftime('%Y-%m-%d')
			date_list.append(date)
			start += step
		dict= [{'day': day, 'date': date, 'territory': territory} for day,date,territory in zip(d_list,date_list,t_list)]
		holiday = frappe.db.sql("""
								select holiday_date from `tabHoliday` """,as_dict = 1)
		print(len(dict))
		updated_list = []
		
		for i in range(len(dict)):
			for a in  holiday :
				b = a.holiday_date
				c = b.strftime('%Y-%m-%d')
				if c == dict[i]['date']  :
					updated_list.append(dict[i])
		v = []
		for i in dict:
			if i not in updated_list:
				v.append(i)
		
		
		for i in v:
			cust = frappe.db.get_all('Customer',{"territory":i.get('territory'),'is_a_secondary_cust':1})
			self.append('beat_plan_items',{
			"date": i.get("date"),
			"territory":i.get("territory"),
			"day":i.get("day"),
			"sch_visit_ct":len(cust)
			})

	
	def on_submit(self):
		items = frappe.db.get_all('Beat Plan Items',{'parent':self.name},['name'])
		items_list = []
		for i in items:
			items_list.append(i.get('name'))
		for j in items_list:
			doc=frappe.get_doc("Beat Plan Items",j)
			doc.act_visit_ct=int(0)
			print(type(doc.act_visit_ct))
			doc.save()
			self.reload()

			
		
			
			
			

			
		
		
				
					
					
				