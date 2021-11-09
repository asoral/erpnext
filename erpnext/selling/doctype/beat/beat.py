# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import datetime
import frappe
from frappe.utils import getdate
from frappe.model.document import Document
import pandas as pd

class Beat(Document):
	@frappe.whitelist()
	def get_salesperson(self):
		x =	frappe.db.get_all('Sales Person',{'parent_sales_person':self.sales_manager},["name"])
		print("############",x)
		for i in x:
			self.append("beatct",{
				"sales_person":i.name
			})
		
	def before_submit(self):
		tlst = []
		for i in self.beatct:
			doc = frappe.get_doc('Beat Items',{"sales_person":i.sales_person})
			if doc.monday != None:
				tlst.append(doc.monday)
			if doc.tuesday != None:
				tlst.append(doc.tuesday)
			if doc.wednesday != None:
				tlst.append(doc.wednesday)
			if doc.thursday != None:
				tlst.append(doc.thursday)
			if doc.friday != None:
				tlst.append(doc.friday)
			if doc.saturday != None:
				tlst.append(doc.saturday)
		set_t = set(tlst)
		self.t_visit = len(set_t)
		cst = []
		for i in set_t:
			cust = frappe.db.get_all('Customer',{"territory":i})
			for j in cust:
				cst.append(j.get('name'))
		print(cst)
		self.sch_visits = len(cst)


	def before_save(self):
		count = 0
		self.working_day = 6
		get_date = getdate(self.week_start_date).strftime("%Y-%m-%d")
		get_end_date = getdate(self.week_end_date).strftime("%Y-%m-%d")
		hlist = frappe.db.get_all('Holiday',["holiday_date"])
		for h in hlist:
			h_str = h.holiday_date.strftime('%Y-%m-%d')
			l_range = pd.date_range(start=get_date,end=get_end_date).to_pydatetime().tolist()
		for t in l_range:
			lrange_str = t.strftime('%Y-%m-%d')
			for h in hlist:
				h_str = h.holiday_date.strftime('%Y-%m-%d')
				if h_str == lrange_str:
					count+=1
				else:
					print("NoMatch",h_str,lrange_str)
		self.working_day = self.working_day - count

	def on_submit(self):
		for i in self.beatct:
			beat_p = frappe.new_doc('Beat Plan')
			beat_p.beat_id = self.name
			beat_p.beat_start_date = self.week_start_date
			beat_p.beat_end_date = self.week_end_date
			beat_p.sales_person = i.sales_person
			beat_p.run_method('fill_child_t')
			beat_p.save()
			beat_p.submit()
		

		
