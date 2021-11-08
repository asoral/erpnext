# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from frappe.utils import flt, date_diff, getdate

def execute(filters=None):
	validate_filters(filters)
	columns=get_columns(filters)
	data = get_data(filters)
	return columns,data

def validate_filters(filters):
	from_date, to_date = filters.get("from_date"), filters.get("to_date")

	if date_diff(to_date, from_date) < 0:
		frappe.throw(_("To Date cannot be before From Date."))

def get_columns(filters):
	columns=[
			{
				"label": _("Company"),
				"fieldname":"company",
				"fieldtype":"Link",
				"options":"Company",
				"width": 150
			},
			{
				"label": _("Date"),
				"fieldname": "posting_date",
				"fieldtype": "Data",
				"width": 100
			},
			# {
			# 	"label": _("Month"),
			# 	"fieldname": "month",
			# 	"fieldtype": "Data",
			# 	"width": 90
			# },
			# {
			# 	"label": _("Year"),
			# 	"fieldname": "year",
			# 	"fieldtype": "Data",
			# 	"width": 50
			# },
			{
				"label": _("Invoices No/ PP No"),
				"fieldname": 'invoice_no',
				"fieldtype": "Link",
				"options": "Sales Invoice",
				"width": 150
			},
			{
				"label": _("Customer Name"),
				"fieldname": 'customer_name',
				"fieldtype": "Data",
				"width": 150
			},
			{
				"label": _("Customer Pan No"),
				"fieldname": 'customer_pan_no',
				"fieldtype": "Data",
				"width": 110
			},
			{
				"label": _("Goods/Services"),
				"fieldname": 'goods',
				"fieldtype": "Data",
				"width": 200
			},
			{
				"label": _("Quantity"),
				"fieldname": 'total_qty',
				"fieldtype": "float",
				"width": 80
			},

			{
				"label": _("Total Sales"),
				"fieldname": 'total',
				"fieldtype": "float",
				"width": 100
			},
			{
				"label": _("Exempted Sales"),
				"fieldname": 'exempted_sales',
				"fieldtype": "float",
				"width": 100
			},

			{
				"label": _("Taxable Sales"),
				"fieldname": 'taxable_sales',
				"fieldtype": "float",
				"width": 120
			},
			{
				"label": _("Local Tax"),
				"fieldname": 'local_tax',
				"fieldtype": "float",
				"width": 100
			},

			{
				"label": _("Export Sales"),
				"fieldname": 'export_sales',
				"fieldtype": "float",
				"width": 100
			},
			{
				"label": _("Export Country"),
				"fieldname": 'country',
				"fieldtype": "data",
				"width": 100
			},
			{
				"label": _("PP No"),
				"fieldname": 'pp_no',
				"fieldtype": "data",
				"width": 100
			},
			{
				"label": _("PP Date"),
				"fieldname": 'pp_date',
				"fieldtype": "Date",
				"width": 100
			}		
		
	]
	return columns	

def get_condition(filters):

	conditions=" "
	if filters.get("year"):
		conditions += " AND year(posting_date)='%s'" % filters.get('year')

	if filters.get("company"):
		conditions += " AND company='%s'" % filters.get('company')

	if filters.get("from_date") and filters.get("to_date"):
		conditions += " AND si.posting_date between %(from_date)s and %(to_date)s"

	return conditions

def get_data(filters):
	conditions = get_condition(filters)	

	doc = frappe.db.sql("""
		Select 
		si.company,
		si.posting_date,
		monthname(si.posting_date) as month,
		year(si.posting_date) as year,
		si.name as invoice_no,
		si.customer_name,
		c.pan as customer_pan_no,

		CASE 
		WHEN si.total_qty > 0 THEN
		(SELECT sii.item_name from `tabSales Invoice Item` as sii  
		inner join `tabSales Invoice` as sd on sd.name  = sii.parent 
		where sd.posting_date = si.posting_date 
		and sd.docstatus=1  LIMIT 1)
		END as goods,

		si.total_qty,
		si.total,
		si.exempted_from_tax,
		IF(si.exempted_from_tax > 0, si.total, 0) as exempted_sales,
		IF(si.exempted_from_tax = 0 AND si.country = 'Nepal' , si.total, 0 ) as taxable_sales,
		IF(si.exempted_from_tax = 0 AND si.country = 'Nepal' , si.total*13/100 , 0) as local_tax,
		si.country,

		IF(si.country != "Nepal", si.total, 0) as export_sales,
		IF(si.country != "Nepal" , si.country, " ") as country,
		si.pp_no ,
		si.pp_date 
		

		from `tabSales Invoice` as si
		left join `tabCustomer` as c 
		on c.name = si.customer

		where si.docstatus = 1 {conditions} 
		group by 
		si.posting_date asc,
		month asc, 
		si.company,
		year,
		si.name ,
		si.customer_name,
		c.pan,
		si.total_qty,
		si.total,
		exempted_sales,
		taxable_sales,
		local_tax,
		export_sales,
		country,
		si.pp_no ,
		si.pp_date 

		""".format(conditions=conditions),filters, as_dict=1)

	# print(doc)
	return doc