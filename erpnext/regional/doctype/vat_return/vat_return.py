# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import os
import json
from erpnext.regional.germany.utils.datev.datev_csv import get_datev_csv
import frappe
from frappe.utils.data import getdate
from six import iteritems
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cstr
from erpnext.regional.india import state_numbers
import nepali_datetime
import datetime
from datetime import  timedelta

class VATRETURN(Document):
	m_year = ""
	@frappe.whitelist()
	def on_nepal_from_date(self, n_date):
		
		f_date = nepali_datetime.date(int(n_date[6:10]), int(n_date[3:5]), int(n_date[:2]))
		# print(f_date.to_datetime_date(), type(f_date.to_datetime_date()))
		# print(" dt.strftime(%A, %d. %B %Y %I:%M%p)", f_date.strftime("%B %Y"))
		# self.m_year = f_date.strftime("%B %Y")
		return f_date.to_datetime_date()	

	@frappe.whitelist()
	def on_nepal_month_year(self):
		# print(" this is month year")
		return nepali_datetime.date(int(self.nepal_from_date[6:10]), int(self.nepal_from_date[3:5]), int(self.nepal_from_date[:2])).strftime("%B %Y")

	def validate(self):
		if not self.from_date :
			# print(" this is error")
			frappe.throw(" Invalid Nepal From Date")
		if not self.to_date:	
			# print(" this is error")
			frappe.throw(" Invalid Nepal To Date")
		# print(" this is magh", self.m_year)	
		self.nepal_month = nepali_datetime.date(int(self.nepal_from_date[6:10]), int(self.nepal_from_date[3:5]), int(self.nepal_from_date[:2])).strftime("%B-%Y")
		self.get_data()

	def get_data(self):
		# print(" this is magh", self.m_year)
		self.report_dict = json.loads(get_json('vat_return_template'))
		self.report_dict["company_name"]=self.company
		self.report_dict["pan_no"]=1234
		self.report_dict["ret_period"] = nepali_datetime.date(int(self.nepal_from_date[6:10]), int(self.nepal_from_date[3:5]), int(self.nepal_from_date[:2])).strftime("%B %Y")
		# self.report_dict["ret_period"] = get_period(self.month, self.year)
		self.month_no = get_period(self.month)
		self.get_sales()
		self.json_output = frappe.as_json(self.report_dict)

	def get_sales(self):
		# doc=frappe.db.sql("""select
		# si.company,
		# monthname(si.posting_date) as month,
		# year(si.posting_date) as year,
		# count(si.name) as no_of_invoice,
		# (sum(total) + (select sum(grand_total) from `tabSales Invoice` as xsi where month(xsi.posting_date)=month(si.posting_date)
		# 	and xsi.total_taxes_and_charges=0 and si.company=xsi.company and year(xsi.posting_date)=year(si.posting_date) group by month(xsi.posting_date) desc, year(xsi.posting_date)
		# 	)) as total,
		# (select sum(grand_total) from `tabSales Invoice` as xsi where month(xsi.posting_date)=month(si.posting_date)
		# 	and xsi.total_taxes_and_charges=0 and si.company=xsi.company and xsi.docstatus = 1 and 
		# 	year(xsi.posting_date)=year(si.posting_date) group by month(xsi.posting_date) desc, year(xsi.posting_date)
		# 	)
		# 		as exempted_sales,

		# (select count(name) from `tabSales Invoice` as xsi where month(xsi.posting_date)=month(si.posting_date)
		# 	and year(xsi.posting_date)=year(si.posting_date) and si.company=xsi.company and xsi.is_return=1 
		# 	and   xsi.docstatus = 1 and xsi.company=si.company  
		# 	 group by month(xsi.posting_date) desc, year(xsi.posting_date)  ) as no_credit_note,

		# (select count(name) from `tabSales Invoice` as xsi where month(xsi.posting_date)=month(si.posting_date)
		# 	and year(xsi.posting_date)=year(si.posting_date) and si.company=xsi.company and
		# 	 xsi.docstatus = 1 and xsi.is_debit_note=1 and xsi.company=si.company  
		# 	 group by month(xsi.posting_date) desc, year(xsi.posting_date)  ) as no_debit_note,

		# CASE WHEN si.currency != "NPR" THEN
		# (select sum(xsi.total) from `tabSales Invoice` as xsi where xsi.currency != "NPR" and year(xsi.posting_date)=year(si.posting_date) 
		# and si.company=xsi.company and month(xsi.posting_date)=month(si.posting_date) and xsi.docstatus=1 group by month(xsi.posting_date) desc, year(xsi.posting_date) )
		# END as export,

		# sum(total) as taxable_sales,
		# sum(total_taxes_and_charges) as tax
		# from `tabSales Invoice` as si
		# where si.docstatus=1 
		# group by year(si.posting_date) desc,
		# monthname(si.posting_date) asc,
		# company 
		# 	""",as_dict=1)
		# print(doc)

		doc=frappe.db.sql("""select
		si.company,
		
		count(si.name) as no_of_invoice,

		(select sum(grand_total) from `tabSales Invoice` as xsi 
		where xsi.total_taxes_and_charges=0 and xsi.company = "CAS Trading House Pvt Ltd" 
		and xsi.posting_date Between '{0}' AND '{1}') as total,

		(select sum(grand_total) from `tabSales Invoice` as xsi 
		where xsi.total_taxes_and_charges=0 and xsi.company = si.company and xsi.docstatus = 1
		and xsi.posting_date Between '{0}' AND '{1}') as exempted_sales,

		(select count(name) from `tabSales Invoice` as xsi where 
			 xsi.is_return=1 
			and xsi.docstatus = 1 and xsi.company = "CAS Trading House Pvt Ltd"
			and xsi.posting_date Between '{0}' AND '{1}' ) as no_credit_note,

		(select count(name) from `tabSales Invoice` as xsi
			where xsi.docstatus = 1 and xsi.is_debit_note = 1 and xsi.company = si.company  
			and xsi.posting_date Between '{0}' AND '{1}' ) as no_debit_note,

		CASE WHEN si.currency != "NPR" THEN
		(select sum(xsi.total) from `tabSales Invoice` as xsi where xsi.currency != "NPR"  
		and xsi.company = si.company and xsi.docstatus=1
        and xsi.posting_date Between '{0}' AND '{1}'  )
		END as export,

		sum(total) as taxable_sales,
		sum(total_taxes_and_charges) as tax
		from `tabSales Invoice` as si
		where si.docstatus=1 
		and company = '{2}'
		and si.posting_date Between '{0}' AND '{1}'
		
			""".format(self.from_date, self.to_date, self.company),as_dict=1)

		# print(" this is dioc", doc)
		last_month=["January" ,"February","March","April","May","June","July","August","September","October","November","December"]
		new_a_date = datetime.datetime.strftime(getdate(self.from_date), "%B")
		new_a_year = datetime.datetime.strftime(getdate(self.from_date), "%Y")
		index =last_month.index(new_a_date)
		last=last_month[index-1]
		high=0
		for i in doc:
			# if i.month==self.month and i.company==self.company and i.year==int(self.year):
			if i.company==self.company :
				self.report_dict["particular"]["sales"][0]["tv"]=flt(i.taxable_sales)+flt(i.exempted_sales)+flt(i.export)
				# self.report_dict["particular"]["sales"][0]["tv"]=""
				self.report_dict["particular"]["sales"][0]["tc"]=(flt(i.taxable_sales)*13)/100
				# self.report_dict["particular"]["sales"][0]["tc"]=""
				self.report_dict["particular"]["export"][0]["tv"]=i.export
				self.report_dict["particular"]["taxable_sales"][0]["tv"]=i.taxable_sales
				# self.report_dict["particular"]["taxable_sales"][0]["tc"]=i.tax
				self.report_dict["particular"]["taxable_sales"][0]["tc"]= (flt(i.taxable_sales)*13)/100
				self.report_dict["particular"]["exempted_sales"][0]["tv"]=i.exempted_sales
				self.report_dict["particular"]["total"][0]["tc"]=(flt(i.taxable_sales)*13)/100+flt(self.adjusted_tax_paid_on_sales)
				self.report_dict["particular"]["other_adj"][0]["tc"]=self.adjusted_tax_paid_on_sales
				self.report_dict["particular"]["no_of_sales_invoice"][0]["tc"]=i.no_of_invoice
				self.report_dict["particular"]["no_of_credit_note"][0]["tc"]=i.no_credit_note
				self.report_dict["particular"]["no_of_debit_note"][0]["tc"]=i.no_debit_note
			# if i.month==last and i.company==self.company and i.year==int(self.year) and i.month!="January":
			if self.from_date and i.company==self.company and new_a_year and last!="January":
				high = (flt(i.taxable_sales)*13)/100 + flt(self.adjusted_tax_paid_on_sales)
				# print(high)
			# if i.month=="January" and i.company==self.company and i.year==int(self.year)-1:
			if last == "January" and i.company == self.company and new_a_year == int(new_a_year)-1:
				high=(flt(i.taxable_sales)*13)/100 + flt(self.adjusted_tax_paid_on_sales)
		c_tax=high
		a=self.report_dict["particular"]["total"][0]["tc"]
		total=self.report_dict["particular"]["sales"][0]["tv"]
		head = "Vat claim due"
		vat = "Vat on Import"
		# doc1 = frappe.db.sql("""
		
		# select
		# company,
		# monthname(posting_date) as month,
		# year(posting_date) as year,
		# count(si.name) as no_of_invoices,
		# CASE  WHEN si.currency = "NPR" THEN
		# (ifnull((select sum(grand_total) from `tabPurchase Invoice` as xsi where month(xsi.posting_date)=month(si.posting_date)
		# and xsi.total_taxes_and_charges=0 and year(xsi.posting_date)=year(si.posting_date) and si.company=xsi.company and xsi.docstatus=1 group by month(xsi.posting_date) desc, year(xsi.posting_date)
		# ), 0) + ifnull((select sum(total) from `tabPurchase Invoice` as xsi where month(xsi.posting_date)=month(si.posting_date)
		# and xsi.total_taxes_and_charges != 0 and xsi.docstatus=1 and year(xsi.posting_date)=year(si.posting_date) and si.company=xsi.company group by month(xsi.posting_date) desc, year(xsi.posting_date)
		# ), 0) + ifnull( (select sum(xsi.total) from`tabPurchase Invoice` as xsi where xsi.currency != "NPR" and year(xsi.posting_date)=year(si.posting_date) 
		# and si.company=xsi.company and month(xsi.posting_date)=month(si.posting_date) and xsi.docstatus=1 group by month(xsi.posting_date) desc, year(xsi.posting_date)),0)
		# +ifnull((select sum(pii.amount) from `tabPurchase Invoice` as pd 
		# inner join `tabPurchase Invoice Item` as pii on pd.name=pii.parent 
		# where  month(pd.posting_date)= month(si.posting_date) and year(pd.posting_date)=year(si.posting_date) and pd.docstatus=1
		# and pii.is_fixed_asset=1 and si.company=pd.company  group by month(pd.posting_date) desc, year(pd.posting_date)),0)) 
		
		# WHEN si.currency != "NPR" THEN
		# (ifnull((select sum(base_grand_total) from `tabPurchase Invoice` as xsi where month(xsi.posting_date)=month(si.posting_date)
		# and xsi.total_taxes_and_charges=0 and year(xsi.posting_date)=year(si.posting_date) and si.company=xsi.company and xsi.docstatus=1 group by month(xsi.posting_date) desc, year(xsi.posting_date)
		# ), 0) + ifnull((select sum(base_total) from `tabPurchase Invoice` as xsi where month(xsi.posting_date)=month(si.posting_date)
		# and xsi.base_total_taxes_and_charges != 0 and year(xsi.posting_date)=year(si.posting_date) and xsi.docstatus=1 and si.company=xsi.company group by month(xsi.posting_date) desc, year(xsi.posting_date)
		# ), 0) + ifnull( (select sum(xsi.total) from`tabPurchase Invoice` as xsi where xsi.currency != "NPR" and year(xsi.posting_date)=year(si.posting_date) 
		# and si.company=xsi.company and month(xsi.posting_date)=month(si.posting_date) and xsi.docstatus=1 group by month(xsi.posting_date) desc, year(xsi.posting_date)),0)
		# +ifnull((select sum(pii.base_amount) from `tabPurchase Invoice` as pd 
		# inner join `tabPurchase Invoice Item` as pii on pd.name=pii.parent 
		# where  month(pd.posting_date)= month(si.posting_date) and year(pd.posting_date)=year(si.posting_date) 
		# and pii.is_fixed_asset=1 and si.company=pd.company and pd.docstatus=1 group by month(pd.posting_date) desc, year(pd.posting_date)),0)) 
		# END as total,

		# CASE  WHEN si.currency != "NPR" and si.exempted_from_tax = 1 THEN
		# (select sum(xsi.grand_total) from `tabPurchase Invoice` as xsi where month(xsi.posting_date)=month(si.posting_date)
		# 	and xsi.total_taxes_and_charges=0 and year(xsi.posting_date)=year(si.posting_date) and si.company=xsi.company and xsi.docstatus=1 group by month(xsi.posting_date) desc, year(xsi.posting_date)
		# 	)
        #   END as   exempted_import,
		
        # CASE
		# WHEN si.currency = "NPR" and si.exempted_from_tax = 1  THEN
		# (select sum(xsi.base_grand_total) from `tabPurchase Invoice` as xsi where month(xsi.posting_date)=month(si.posting_date)
		# 	and xsi.base_total_taxes_and_charges=0 and year(xsi.posting_date)=year(si.posting_date) and si.company=xsi.company and xsi.docstatus=1  group by month(xsi.posting_date) desc, year(xsi.posting_date))
		# END as exempted_purchase,

		# CASE  
		# WHEN si.currency = "NPR" THEN
		# (select sum(xsi.total) from `tabPurchase Invoice` as xsi where month(xsi.posting_date)=month(si.posting_date)
		# 	and xsi.total_taxes_and_charges != 0 and year(xsi.posting_date)=year(si.posting_date) and si.company=xsi.company and xsi.docstatus=1 group by month(xsi.posting_date) desc, year(xsi.posting_date)) 
		# END as taxable_purchase,

		# CASE  WHEN si.currency = "NPR" and si.exempted_from_tax = 0 THEN
		# (select abs(sum(xsi.total_taxes_and_charges)) from `tabPurchase Invoice` as xsi where month(xsi.posting_date)=month(si.posting_date)
		# 	and xsi.total_taxes_and_charges != 0 and year(xsi.posting_date)=year(si.posting_date) and si.company=xsi.company and xsi.docstatus=1  group by month(xsi.posting_date) desc, year(xsi.posting_date)
		# 	) 
		# END as local_tax,

		# CASE  WHEN si.currency != "NPR" and si.is_import_services = 1 THEN
        # (select abs(sum(xsi.total)) from`tabPurchase Invoice` as xsi where xsi.currency != "NPR" and year(xsi.posting_date)=year(si.posting_date) 
		# and si.company=xsi.company and month(xsi.posting_date)=month(si.posting_date) and xsi.docstatus=1 group by month(xsi.posting_date) desc, year(xsi.posting_date)) 
		
        # ELSE 0
        # END as taxable_import_2,

		# CASE  WHEN si.currency != "NPR" and si.is_import_services = 1 THEN
		# (Select sum(ptc.tax_amount) from `tabPurchase Taxes and Charges` as ptc
		# Join  `tabPurchase Invoice` as xsi on xsi.name = ptc.parent 
		# where xsi.name = si.name	
		# and ptc.account_head like '{1}%'
 	  	# and xsi.currency != "NPR" and year(xsi.posting_date)=year(si.posting_date) 
		# and si.company=xsi.company and month(xsi.posting_date)=month(si.posting_date) and xsi.docstatus=1 
        # group by month(xsi.posting_date) desc, year(xsi.posting_date)) 
		
        # ELSE 0
        # END as taxable_import_2_tax,
        
		# CASE
		# WHEN si.currency != "NPR" and si.is_import_services = 0 THEN
        # (select sum(je.custom_valuation_amount) from `tabJournal Entry` as je
		# Left Join `tabPurchase Invoice` as xsi on xsi.name = je.purchase_invoice_no
		# where xsi.currency != "NPR" and year(xsi.posting_date)=year(si.posting_date) 
		# and si.company=xsi.company and month(xsi.posting_date)=month(si.posting_date) and xsi.docstatus=1 
        # group by month(xsi.posting_date) desc, year(xsi.posting_date)) 
		#  ELSE 0
        # END as taxable_import_1,
        
        # CASE
		# WHEN si.currency != "NPR" and si.is_import_services = 0 THEN
        # (Select sum(jea.debit) from `tabJournal Entry Account`  jea 
		# join `tabJournal Entry` as je on je.name = jea.parent
		# Left Join `tabPurchase Invoice` as xsi on xsi.name = je.purchase_invoice_no
		# where 
		# je.docstatus = 1
        # and je.voucher_type = "Import Purchase"
		# and jea.account Like '{0}%' 
		# and xsi.currency != "NPR" and year(xsi.posting_date)=year(si.posting_date) 
		# and si.company=xsi.company and month(xsi.posting_date)=month(si.posting_date) and xsi.docstatus=1
        # group by month(xsi.posting_date) desc, year(xsi.posting_date)) 

		# ELSE 0
        # END as taxable_import_1_tax,


		# CASE  WHEN si.currency != "NPR" THEN
		# (select sum(pii.base_amount) from `tabPurchase Invoice` as pd 
		# inner join `tabPurchase Invoice Item` as pii on pd.name=pii.parent 
		# where  month(pd.posting_date)= month(si.posting_date) and year(pd.posting_date)=year(si.posting_date) 
		# and pii.is_fixed_asset=1 and pd.docstatus=1 and si.company=pd.company group by month(pd.posting_date) desc, year(pd.posting_date))

		# WHEN si.currency = "NPR" THEN
		# (select sum(pii.amount) from `tabPurchase Invoice` as pd 
		# inner join `tabPurchase Invoice Item` as pii on pd.name=pii.parent 
		# where  month(pd.posting_date)= month(si.posting_date) and year(pd.posting_date)=year(si.posting_date) 
		# and pii.is_fixed_asset=1 and pd.docstatus=1 and si.company=pd.company  group by month(pd.posting_date) desc, year(pd.posting_date))
		
        # ELSE 0
        # END as capital_purchase,

		# CASE  WHEN si.currency = "NPR" THEN
		# (select sum(pii.amount)*13/100 from `tabPurchase Invoice Item` as pii  
		# inner join `tabPurchase Invoice` as pd on pd.name=pii.parent 
		# where month(pd.posting_date)=month(si.posting_date) and year(pd.posting_date)=year(si.posting_date)
		# and pii.is_fixed_asset=1 and pd.docstatus=1 and si.company=pd.company group by month(pd.posting_date) desc, year(pd.posting_date)) 

		# WHEN si.currency != "NPR" THEN
		# (select sum(pii.base_amount)*13/100 from `tabPurchase Invoice Item` as pii  
		# inner join `tabPurchase Invoice` as pd on pd.name=pii.parent 
		# where month(pd.posting_date)=month(si.posting_date) and year(pd.posting_date)=year(si.posting_date)
		# and pii.is_fixed_asset=1 and pd.docstatus=1   and si.company=pd.company group by month(pd.posting_date) desc, year(pd.posting_date)) 
		
		# ELSE 0
        # END as capital_tax
		# from
		# `tabPurchase Invoice` as si
		# where si.docstatus=1
		# group by year(si.posting_date) desc,
		# monthname(si.posting_date) asc,
		# company

		# """.format(vat, head),as_dict=1)
		# print(doc1)

		doc1 = frappe.db.sql("""
		
		select
		company,
		
		count(si.name) as no_of_invoices,

		CASE  WHEN si.currency = "NPR" THEN
		(ifnull((select sum(grand_total) from `tabPurchase Invoice` as xsi 
		where xsi.total_taxes_and_charges=0 and  si.company=xsi.company and xsi.docstatus=1 
		and xsi.posting_date Between '{3}' AND '{4}'), 0)
		 + ifnull((select sum(total) from `tabPurchase Invoice` as xsi 
		where  xsi.total_taxes_and_charges != 0 and xsi.docstatus=1 and si.company=xsi.company 
		and xsi.posting_date Between '{3}' AND '{4}' ), 0) 
		 + ifnull( (select sum(xsi.total) from`tabPurchase Invoice` as xsi 
		where xsi.currency != "NPR" and si.company=xsi.company  and xsi.docstatus=1 
		and xsi.posting_date Between '{3}' AND '{4}'),0)
		+ifnull((select sum(pii.amount) from `tabPurchase Invoice` as pd 
		inner join `tabPurchase Invoice Item` as pii on pd.name=pii.parent 
		where  pd.docstatus=1 and pii.is_fixed_asset=1 and si.company=pd.company 
		and pd.posting_date Between '{3}' AND '{4}'),0)) 
		
		WHEN si.currency != "NPR" THEN
		(ifnull((select sum(base_grand_total) from `tabPurchase Invoice` as xsi 
		where 
		xsi.total_taxes_and_charges=0 and si.company=xsi.company and xsi.docstatus=1 
		and xsi.posting_date Between '{3}' AND '{4}'), 0) 
		 + ifnull((select sum(base_total) from `tabPurchase Invoice` as xsi 
		where xsi.base_total_taxes_and_charges != 0 and xsi.docstatus=1 and si.company=xsi.company 
		and xsi.posting_date Between '{3}' AND '{4}'), 0)
		 + ifnull( (select sum(xsi.total) from`tabPurchase Invoice` as xsi 
		where xsi.currency != "NPR"	and si.company=xsi.company and xsi.docstatus=1 
		and xsi.posting_date Between '{3}' AND '{4}'),0)
		+ifnull((select sum(pii.base_amount) from `tabPurchase Invoice` as pd 
		inner join `tabPurchase Invoice Item` as pii on pd.name=pii.parent 
		where  pii.is_fixed_asset=1 and si.company=pd.company and pd.docstatus=1 
		and pd.posting_date Between '{3}' AND '{4}'),0)) 
		END as total,

		CASE  WHEN si.currency != "NPR" and si.exempted_from_tax = 1 THEN
		(select sum(xsi.grand_total) from `tabPurchase Invoice` as xsi 
		where xsi.total_taxes_and_charges=0  and si.company=xsi.company and xsi.docstatus=1 
		and xsi.posting_date Between '{3}' AND '{4}')
        END as   exempted_import,
		
        CASE
		WHEN si.currency = "NPR" and si.exempted_from_tax = 1  THEN
		(select sum(xsi.base_grand_total) from `tabPurchase Invoice` as xsi 
		where xsi.base_total_taxes_and_charges=0  and si.company=xsi.company and xsi.docstatus=1 
		and xsi.posting_date Between '{3}' AND '{4}')
		END as exempted_purchase,

		CASE  
		WHEN si.currency = "NPR" THEN

		(select sum(pii.amount) from `tabPurchase Invoice Item` as pii
        left join `tabPurchase Invoice` as xsi on pii.parent = xsi.name
		where xsi.total_taxes_and_charges != 0 
        and pii.is_fixed_asset = 0
        and xsi.company = si.company and xsi.docstatus=1 
        and xsi.country = "Nepal"
		and xsi.posting_date Between '{3}' AND '{4}') 
		END as taxable_purchase,

		CASE  WHEN si.currency = "NPR" and si.exempted_from_tax = 0 THEN
		(select abs(sum(xsi.total_taxes_and_charges)) from `tabPurchase Invoice` as xsi 
		where xsi.total_taxes_and_charges != 0  and si.company=xsi.company and xsi.docstatus=1  
		and xsi.posting_date Between '{3}' AND '{4}') 
		END as local_tax,

		
        (select abs(sum(xsi.total)) from`tabPurchase Invoice` as xsi
        where xsi.company = si.company and xsi.docstatus=1 
        and	xsi.is_import_services = 1	
		and xsi.posting_date Between '{3}' AND '{4}') 
		as taxable_import_2,

		(select sum(je.custom_valuation_amount) from `tabJournal Entry` as je
		Join `tabPurchase Invoice` as xsi on xsi.name = je.purchase_invoice_no
		where xsi.company = si.company and xsi.docstatus=1 
        and xsi.country != "Nepal"
		and xsi.is_import_services = 0 and je.voucher_type = "Import Purchase"
			and xsi.posting_date Between '{3}' AND '{4}') 

		as taxable_import_1,
        
			(Select sum(jea.debit) from `tabJournal Entry Account`  jea 
			join `tabJournal Entry` as je on je.name = jea.parent
			Left Join `tabPurchase Invoice` as xsi on xsi.name = je.purchase_invoice_no
			and xsi.is_import_services = 0
			where je.docstatus = 1 and je.voucher_type = "Import Purchase"
			and jea.account Like 'Vat on Import%' and xsi.company = si.company
			and xsi.docstatus=1 and xsi.posting_date Between '{3}' AND '{4}') 
        +
			(Select sum(ptc.tax_amount) from `tabPurchase Taxes and Charges` as ptc
			Join  `tabPurchase Invoice` as xsi on xsi.name = ptc.parent 
			where  ptc.account_head like 'Vat claim due%'
			and xsi.is_import_services = 1   
			and xsi.company=  si.company and xsi.docstatus=1 and xsi.posting_date Between '{3}' AND '{4}')
			
        as taxable_import_1_tax,


		(select sum(pii.base_amount) from `tabPurchase Invoice` as pd 
		inner join `tabPurchase Invoice Item` as pii on pd.name=pii.parent 
		where   
		pii.is_fixed_asset=1 and pd.docstatus=1 and si.company=pd.company 
		and pd.posting_date Between '{3}' AND '{4}')
		
		as capital_purchase,


		(select sum(pii.amount)*13/100 from `tabPurchase Invoice Item` as pii  
		inner join `tabPurchase Invoice` as pd on pd.name=pii.parent 
		where pii.is_fixed_asset=1 and pd.docstatus=1 and si.company=pd.company 
		and pd.posting_date Between '{3}' AND '{4}')
		+
		(select sum(pii.base_amount)*13/100 from `tabPurchase Invoice Item` as pii  
		inner join `tabPurchase Invoice` as pd on pd.name=pii.parent 
		where 
		pii.is_fixed_asset=1 and pd.docstatus=1   and si.company=pd.company 
		and pd.posting_date Between '{3}' AND '{4}')
		as capital_tax

		from `tabPurchase Invoice` as si
		where si.docstatus=1
		and si.company = '{2}'
		and si.posting_date Between '{3}' AND '{4}'
		

		""".format(vat, head, self.company, self.from_date, self.to_date),as_dict=1)
		# print(doc1)
		top=0
		for i in doc1:
			if i.company==self.company :
				self.report_dict["particular"]["purchase"][0]["tv"]=flt(i.taxable_purchase)+ flt(i.taxable_import) + flt(i.exempted_purchase)+flt(i.exempted_import)+ flt(i.capital_purchase)
				# self.report_dict["particular"]["purchase"][0]["tv"]=""
				self.report_dict["particular"]["taxcable_purchase"][0]["tv"]=flt(i.taxable_purchase) + flt(i.capital_purchase)
				# self.report_dict["particular"]["taxcable_purchase"][0]["tv"]=flt(i.taxable_purchase) 

				# self.report_dict["particular"]["taxcable_purchase"][0]["tp"]=flt(i.local_tax) + flt(i.capital_tax)
				self.report_dict["particular"]["taxcable_purchase"][0]["tp"]= ((flt(i.taxable_purchase) + flt(i.capital_purchase)) * 13)/100 
				self.report_dict["particular"]["taxcable_import"][0]["tv"]= flt(i.taxable_import_1) + flt(i.taxable_import_2)
				self.report_dict["particular"]["taxcable_import"][0]["tp"]=flt(i.taxable_import_1_tax) 
				self.report_dict["particular"]["exempted_purchase"][0]["tv"]=i.exempted_purchase
				self.report_dict["particular"]["exempted_import"][0]["tv"]=i.exempted_import
				
				self.report_dict["particular"]["other_adj"][0]["tp"]=self.adjusted_tax_paid_on_purchase
				self.report_dict["particular"]["total"][0]["tp"]= flt(self.adjusted_tax_paid_on_purchase) + flt(i.taxable_import_1_tax)+((flt(i.taxable_purchase)  * 13)/100 )
				self.report_dict["particular"]["no_of_purchase_invoice"][0]["tc"]=i.no_of_invoices
				self.report_dict["particular"]["no_of_debit_advice"][0]["tc"]=flt(self.no_debit_advice)
				self.report_dict["particular"]["no_of_credit_advice"][0]["tc"]=flt(self.no_credit_advice)
			if self.from_date and i.company==self.company and new_a_year and last!="January":	
			# if i.month==last and i.company==self.company and i.year==int(self.year) and i.month != "January":
				top=flt(i.local_tax) + flt(i.import_tax)+flt(self.adjusted_tax_paid_on_purchase)
			if last == "January" and i.company == self.company and new_a_year == int(new_a_year)-1:	
			# if i.month=="January" and i.company==self.company and i.year==int(self.year)-1:
				top=flt(i.local_tax) + flt(i.import_tax)+flt(self.adjusted_tax_paid_on_purchase)
		t_tax=top
		tot=self.report_dict["particular"]["purchase"][0]["tv"]
		b=self.report_dict["particular"]["total"][0]["tp"]
		self.report_dict["particular"]["debit_credit"][0]["tc"]	=a-b
		self.report_dict["particular"]["total"][0]["tv"]=total+tot
		# print(c_tax)
		# print(t_tax)

		new_from_date = getdate(self.from_date) - timedelta(days=30)
		new_to_date = getdate(self.to_date) - timedelta(days=30)

		sale_tax = 0
		purchase_tax = 0
		top = frappe.db.sql("""
							Select 
							if ((sum(total)*13/100), (sum(total)*13/100), 0)as taxable_sales 
							from `tabSales Invoice` si
							where si.docstatus=1 
							and company = '{0}'
							and si.posting_date Between '{1}' and '{2}'
							Limit 1
						""".format(self.company, new_to_date, self.from_date), as_dict=1)
		# print(" thi si wen etad  ", new_from_date.self.from_date)
		print(" = = = =  = = = = = = = =", top[0].get("taxable_sales"))
		if top[0].get("taxable_sales"):
			sale_tax = flt(top[0].get("taxable_sales"))

		bott = frappe.db.sql("""
							 Select 
								CASE  
								WHEN si.currency = "NPR" 
								THEN
								(select sum(pii.amount) from `tabPurchase Invoice Item` as pii
								left join `tabPurchase Invoice` as xsi on pii.parent = xsi.name
								where xsi.total_taxes_and_charges != 0 
								and pii.is_fixed_asset = 0
								and xsi.company = si.company and xsi.docstatus=1 
								and xsi.country = "Nepal"
								and xsi.posting_date Between '{1}' AND '{2}')
								
								END as taxable_purchase,
								
								(select sum(pii.base_amount) from `tabPurchase Invoice` as pd 
								inner join `tabPurchase Invoice Item` as pii on pd.name=pii.parent 
								where   
								pii.is_fixed_asset=1 and pd.docstatus=1 and pd.company = si.company 
								and si.posting_date Between '{1}' AND '{2}')
								as capital_purchase
								
								from `tabPurchase Invoice` as si
								where si.docstatus=1
								
								and company = '{0}'
								and si.posting_date Between '{1}' and '{2}'
								Limit 1
						""".format(self.company, new_from_date, self.from_date), as_dict= 1)


		print(" = = = =  = = = = = = = =", bott)
		if bott:
			tp = cp = 0
			print(" >>>>>>>>>>>>>", bott[0].get("taxable_purchase"), bott[0].get("capital_purchase"))
			if bott[0].get("taxable_purchase"): tp = bott[0].get("taxable_purchase")
			if bott[0].get("capital_purchase") : cp = bott[0].get("capital_purchase")

			purchase_tax = (flt(tp)+flt(cp))*13/100
		print(" subraction", sale_tax - purchase_tax , sale_tax - purchase_tax)

		if (a-b)< 0:
			# self.report_dict["particular"]["vat_adj_last_mon"][0]["tc"]=c_tax-t_tax
			self.report_dict["particular"]["vat_adj_last_mon"][0]["tc"]= sale_tax - purchase_tax
			self.report_dict["particular"]["net_tax"][0]["tc"]=flt(self.report_dict["particular"]["vat_adj_last_mon"][0]["tc"])+flt(self.report_dict["particular"]["debit_credit"][0]["tc"])
		if (a-b) > 0:
			self.report_dict["particular"]["vat_adj_last_mon"][0]["tc"]=0
			# self.report_dict["particular"]["vat_adj_last_mon"][0]["tc"] = sale_tax - purchase_tax
			self.report_dict["particular"]["net_tax"][0]["tc"]=flt(self.report_dict["particular"]["vat_adj_last_mon"][0]["tc"])+flt(self.report_dict["particular"]["debit_credit"][0]["tc"])
		self.report_dict["particular"]["total_payment"][0]["tv"]=self.report_dict["particular"]["net_tax"][0]["tc"]
		self.report_dict["particular"]["total_payment"][0]["tp"]="Voucher No:"
		self.report_dict["particular"]["total_payment"][0]["tc"]=self.voucher_no
		



def get_json(template):
	file_path = os.path.join(os.path.dirname(__file__), '{template}.json'.format(template=template))
	with open(file_path, 'r') as f:
		return cstr(f.read())


def get_period(month, year=None):
	month_no = {
		"January": 1,
		"February": 2,
		"March": 3,
		"April": 4,
		"May": 5,
		"June": 6,
		"July": 7,
		"August": 8,
		"September": 9,
		"October": 10,
		"November": 11,
		"December": 12
	}.get(month)

	if year:
		return str(month).zfill(2) +"-"+ str(year)
	else:
		return month_no

@frappe.whitelist()
def view_report(name):
	json_data = frappe.get_value("VAT RETURN", name, 'json_output')
	return json.loads(json_data)

@frappe.whitelist()
def make_json(name):
	json_data = frappe.get_value("VAT RETURN", name, 'json_output')
	file_name = "vat_return.json"
	frappe.local.response.filename = file_name
	frappe.local.response.filecontent = json_data
	frappe.local.response.type = "download"
