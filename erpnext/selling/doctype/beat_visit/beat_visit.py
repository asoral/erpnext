# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import pandas
import datetime
from datetime import date, timedelta 
from frappe.utils import getdate
from frappe.model.document import Document
import calendar
from calendar import monthrange

from erpnext.stock.get_item_details import get_item_price

class BeatVisit(Document):
	@frappe.whitelist()
	def get_tt(self):
		b_plan = frappe.get_doc('Beat Plan',{'name':self.beat_plan})
		sdate = b_plan.beat_start_date
		edate = b_plan.beat_end_date
		dlist = pandas.date_range(sdate,edate-timedelta(days=0),freq='d')
		dates_str = []
		for i in dlist:
			start = i.strftime('%Y-%m-%d')
			dates_str.append(start)
		for dates in dates_str:
			if self.date == dates:
				print("if",dates)
				tty = frappe.db.get_value('Beat Plan Items',{'parent':self.beat_plan,'date':self.date},['territory'])
				if tty:
					self.visit_territory = tty
				else:
					self.visit_territory = " "
					frappe.msgprint("Please Change the selected Date as this date is marked as Holiday in Calendar")
		if self.date not in dates_str:
			self.visit_territory = " "
			frappe.msgprint("Please Select the Date of the Week mentioned in the Respective Beat Plan")


	# @frappe.whitelist()
	# def fill_visit_order(self):
	# 	items = frappe.db.get_all('Item Price',{'price_list':self.price_list},['item_code','item_name','price_list_rate'])
	# 	for i in items:
	# 		self.append('visit_order',{
	# 			"item_code":i.get('item_code'),
	# 			"item_name":i.get('item_name'),
	# 			"rate":i.get('price_list_rate'),
	# 			"amount":i.get('price_list_rate')
				
	# 		})
	@frappe.whitelist()
	def get_item_rate(self):
		v_order = self.visit_order
		for i in v_order:
			get_batch = frappe.db.get_value('Item Price',{'item_code':i.item_code},['batch_no'])
			if get_batch:
				batch_no = get_batch
			else:
				batch_no = ""

			print("*****************",get_batch,batch_no)

			args = {
				"price_list":self.price_list,
				"uom":i.uom,
				"batch_no":batch_no,
				"posting_date":self.date
				
			}
			item_code = i.item_code
			item_price = get_item_price(args,item_code,ignore_party=False)
			for j in item_price:
				i.rate = j[1]
				i.amount = j[1]
			


	
		
		
	
	def before_save(self):
		check = frappe.db.exists({
			'doctype': 'Beat Visit',
			'beat':self.beat,
			'beat_plan':self.beat_plan,
			'sales_person':self.sales_person,
			'date': self.date,
			'visit_territory':self.visit_territory,
			'customer':self.customer,
			'item_group':self.item_group,
			'docstatus':1

		})
		if check:
			frappe.throw("You Have Visited This Customer")


	def on_cancel(self):
		avc = frappe.db.get_value('Beat Plan Items',{'parent':self.beat_plan,'date':self.date,'territory':self.visit_territory},['act_visit_ct','name','sch_visit_ct','completed'])
		doc = frappe.get_doc('Beat Plan Items',avc[1])
		
		sch = int(avc[2])
		actual = doc.act_visit_ct
		doc.act_visit_ct = int(actual)
		doc.act_visit_ct -=1
		frappe.db.set_value('Beat Plan Items',doc.name,'act_visit_ct',doc.act_visit_ct)
		frappe.db.set_value('Beat Plan',self.beat_plan,'status','Partially Completed')
		sch_t = frappe.db.get_list('Beat Plan Items',{'parent':self.beat_plan},['sch_visit_ct','act_visit_ct'])
		sch_lst = []
		ach_lst = []
		for j in sch_t:
			sch_lst.append(int(j.sch_visit_ct))
			ach_lst.append(int(j.act_visit_ct))
		sum_sch = sum(sch_lst)
		sum_act = sum(ach_lst)
		percent = (sum_act/sum_sch)*100
		frappe.db.set_value('Beat Plan',self.beat_plan,'vcp',percent)
		pct = frappe.db.get_value('Beat Plan',self.beat_plan,'vcp')
		print(pct)
		if pct == 100:
			frappe.db.set_value('Beat Plan',self.beat_plan,'status','Completed')

		if doc.act_visit_ct != sch:
			frappe.db.set_value('Beat Plan Items',doc.name,'completed',0)

		act = []
		visitct = frappe.get_doc('Beat Plan',self.beat_plan)
		for i in visitct.beat_plan_items:
			act.append(int(i.act_visit_ct))
		print(act)
		if sum(act)==0:
			frappe.db.set_value('Beat Plan',self.beat_plan,'status','Not Started')

	@frappe.whitelist()
	def fill_vo(self):
		items = frappe.db.get_all('Item',{'item_group':self.item_group,'is_nil_exempt':0},['item_code','item_name','stock_uom'])
		for i in items:
			get_batch = frappe.db.get_value('Item Price',{'item_code':i.get('item_code')},['batch_no'])
			if get_batch:
				batch_no = get_batch
			else:
				batch_no = ""

			args = {
				"price_list":self.price_list,
				"uom":i.get('stock_uom'),
				"batch_no":batch_no,
				"posting_date":self.date
				
			}
			item_code = i.get('item_code')
			item_price = get_item_price(args,item_code,ignore_party=False)
			for j in item_price:
					self.append('visit_order',{
				"item_code":i.get('item_code'),
				"item_name":i.get('item_name'),
				"rate":j[1]
			})

	@frappe.whitelist()
	def fill_vg(self):
		items = frappe.db.get_all('Item',{'is_nil_exempt':1},['item_code','item_name','stock_uom'])
		for i in items:
			get_batch = frappe.db.get_value('Item Price',{'item_code':i.get('item_code')},['batch_no'])
			if get_batch:
				batch_no = get_batch
			else:
				batch_no = ""

			args = {
				"price_list":self.price_list,
				"uom":i.get('stock_uom'),
				"batch_no":batch_no,
				"posting_date":self.date
				
			}
			item_code = i.get('item_code')
			item_price = get_item_price(args,item_code,ignore_party=False)
			for j in item_price:
					self.append('visit_gift',{
				"item_code":i.get('item_code'),
				"item_name":i.get('item_name'),
				"rate":j[1]
			})

	def on_submit(self):
		avc = frappe.db.get_value('Beat Plan Items',{'parent':self.beat_plan,'date':self.date,'territory':self.visit_territory},['act_visit_ct','name','sch_visit_ct','completed'])
		doc = frappe.get_doc('Beat Plan Items',avc[1])
		
		sch = int(avc[2])
		actual = doc.act_visit_ct
		doc.act_visit_ct = int(actual)
		doc.act_visit_ct +=1
		if doc.act_visit_ct <= sch:
			frappe.db.set_value('Beat Plan Items',doc.name,'act_visit_ct',doc.act_visit_ct)
			frappe.db.set_value('Beat Plan',self.beat_plan,'status','Partially Completed')
		else:
			frappe.throw("All The Visits For Selected Date are Completed.Please Change The Date")
		
		if doc.act_visit_ct == sch:
			frappe.db.set_value('Beat Plan Items',doc.name,'completed',1)

		sch_t = frappe.db.get_list('Beat Plan Items',{'parent':self.beat_plan},['sch_visit_ct','act_visit_ct'])
		sch_lst = []
		ach_lst = []
		for j in sch_t:
			sch_lst.append(int(j.sch_visit_ct))
			ach_lst.append(int(j.act_visit_ct))
		sum_sch = sum(sch_lst)
		sum_act = sum(ach_lst)
		percent = (sum_act/sum_sch)*100
		frappe.db.set_value('Beat Plan',self.beat_plan,'vcp',percent)
		pct = frappe.db.get_value('Beat Plan',self.beat_plan,'vcp')
		print(pct)
		if pct == 100:
			frappe.db.set_value('Beat Plan',self.beat_plan,'status','Completed')

		

		if self.pymt>0:
			get_acc = frappe.db.get_value('Mode of Payment Account',{'parent':self.payment_mode,'company':self.company},['default_account'])
			payent = frappe.new_doc('Payment Entry')
			payent.posting_date = self.date
			payent.company = self.company
			payent.mode_of_payment = self.payment_mode
			payent.party_type = 'Customer'
			payent.party = self.customer
			payent.party_name = self.customer
			payent.paid_amount = self.pymt
			payent.received_amount = self.pymt
			payent.source_exchange_rate = 1
			payent.target_exchange_rate = 1
			if self.payment_mode == 'Cheque':
				payent.paid_to = get_acc
				payent.reference_no = self.ref_no
				payent.reference_date = self.ref_date
			elif self.payment_mode == 'Cash':
				payent.paid_to = get_acc
			payent.save()
			payent.submit()
				
		saor = frappe.new_doc('Sales Order')		
		saor.sec_cust = self.customer
		saor.customer = self.primary_customer
		saor.company = self.company
		saor.transaction_date = self.date
		saor.selling_price_list = self.price_list
		for i in self.visit_order:
			saor.append('items',{
				"item_code":i.item_code,
				"delivery_date":i.expected_delivery,
				"qty":i.qty,
				"rate":i.rate,
				"amount":i.amount
			})
		saor.save()
		saor.submit()


	@frappe.whitelist()
	def cust_stats(self):
		last_date = frappe.db.get_value('Beat Visit',{'sales_person':self.sales_person,'customer':self.customer,'item_group':self.item_group,'date':["<", self.date]},['date'])
		if last_date:
			self.last_visit_date_ = last_date
		else:
			self.last_visit_date_ = "No Previous Visit"

		last_order_date = frappe.db.get_value('Sales Order',{'customer':self.primary_customer,'transaction_date':["<",self.date]},['transaction_date'])
		print(last_order_date)
		if last_order_date:
			self.last_order_date_ = last_order_date
			print("yes")
		else:
			self.last_order_date_ = 'No Previous Order'
			print("No")

		year = frappe.get_doc('Fiscal Year',{"year_start_date":["<=",self.date],"year_end_date":[">=",self.date]})
		print(year)
	

		x = getdate(self.date)
		month = calendar.month_name[x.month]
		print(month)
		# month_dis = frappe.get_doc('Monthly Distribution',{'fiscal_year':year.name})	
		
		# ct = frappe.db.get_all('Monthly Distribution Percentage',{'parent':month_dis.name},['month','percentage_allocation'])
		# for j in ct:
		# 	if month == j.get("month"):
		# 		percent = j.get("percentage_allocation")
		# value = frappe.db.get_all('Target Detail',{'parent':self.sales_person,'item_group':self.item_group,'fiscal_year':year.name,'distribution_id':month_dis.name},['target_qty','target_amount'])
		# print("Target",value)
		# t_qty = t_amt = 0
		# for k in value:
		# 	t_qty = k.get("target_qty")
		# 	t_amt = k.get("target_amount")

		# target_quantity = t_qty*(1/percent)
		# target_amount = t_amt*(1/percent)
		# print(target_quantity)

		# self.target_amount = target_amount
		# self.target_quantity = target_quantity

		# # num_days = monthrange(x.year, x.month)[1]
		if self.last_order_date_ == 'No Previous Order':
			self.last_item_ordered = 'No Previous Order'
			print("No Item")
		elif self.last_order_date_ == last_order_date:
			last_item_doc = frappe.get_doc('Sales Order',{'transaction_date':last_order_date})
			last_item_ct = frappe.get_last_doc('Sales Order Item',{'parent':last_item_doc.name})
			print(last_item_ct.item_name)
			self.last_item_ordered = last_item_ct.item_name
			print("Yes Item Present")

		sales_p = frappe.get_doc('Sales Person',self.sales_person)
		sum_tgt = sum_qty = 0
		# for i in sales_
		print(sales_p.targets)
		year = frappe.get_doc('Fiscal Year',{"year_start_date":["<=",self.date],"year_end_date":[">=",self.date]})
		month_dis = frappe.get_doc('Monthly Distribution',{'fiscal_year':year.name})
		ct = frappe.db.get_all('Monthly Distribution Percentage',{'parent':month_dis.name},['month','percentage_allocation'])
		for j in ct:
			if month == j.get("month"):
				percent = j.get("percentage_allocation")
		for i in sales_p.targets:
			print(month_dis.name,year.name)
			if (self.item_group == i.item_group) and (year.name == i.fiscal_year) and (month_dis.name == i.distribution_id):
				sum_tgt+= i.target_amount
				sum_qty+= i.target_qty
				target_quantity = sum_qty*(1/percent)
				target_amount = sum_tgt*(1/percent)
				self.target_amount_ = target_amount
				self.target_quantity_ = target_quantity
				print("Same",sum_tgt,sum_qty)
			else:
				target_quantity = i.target_qty*(1/percent)
				target_amount = i.target_amount*(1/percent)
				self.target_amount = target_amount
				self.target_quantity_ = target_quantity
				print("Not Same",target_quantity,target_amount)


			


		

		



		



		



		
		
		
		
		

		
		

		

		

		

		

			


		

			

	