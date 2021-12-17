
import frappe
from frappe import _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from frappe.utils import flt, date_diff


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
				"width": 140
			},
			{
				"label": _("Date"),
				"fieldname": "posting_date",
				"fieldtype": "Data",
				"width": 100
			},
			{
				"label": _("PP No"),
				"fieldname": 'pp_no',
				"fieldtype": "data",
				"width": 120
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
				"label": _("Naming series"),
				"fieldname": 'invoice_no',
				"fieldtype": "Link",
				"options": "Purchase Invoice",
				"width": 180
			},
			{
				"label": _("Supplier Name"),
				"fieldname": 'supplier_name',
				"fieldtype": "Data",
				"width": 180
			},
			{
				"label": _("Supplier Pan No"),
				"fieldname": 'supplier_pan_no',
				"fieldtype": "Data",
				"width": 120
			},
			{
				"label": _("Goods/Service imported or Purchase"),
				"fieldname": 'gsi_or_purchase',
				"fieldtype": "Data",
				"width": 150
			},
			{
				"label": _("Quantity"),
				"fieldname": 'total_qty',
				"fieldtype": "float",
				"width": 80
			},

			{
				"label": _("Total Purchase Amount"),
				"fieldname": 'total',
				"fieldtype": "float",
				"width": 100
			},
			{
				"label": _("Exempted/ Non-Taxable Purchase"),
				"fieldname": 'exempted_purchase',
				"fieldtype": "float",
				"width": 100
			},
			{
				"label": _("Exempted/ Non-Taxable Import"),
				"fieldname": 'exempted_import',
				"fieldtype": "float",
				"width": 100
			},
			# {
			# 	"label": _("Country"),
			# 	"fieldname": 'country',
			# 	"fieldtype": "data",
			# 	"width": 100
			# },
			# {
			# 	"label": _("Is Service"),
			# 	"fieldname": 'is_service',
			# 	"fieldtype": "check",
			# 	"width": 100
			# },

			{
				"label": _("Taxable Purchase"),
				"fieldname": 'taxable_purchase',
				"fieldtype": "float",
				"width": 100
			},
			{
				"label": _("Local Tax"),
				"fieldname": 'local_tax',
				"fieldtype": "float",
				"width": 100
			},

			{
				"label": _("Taxable Import"),
				"fieldname": 'taxable_import',
				"fieldtype": "float",
				"width": 100
			},
			{
				"label": _("Vat On Import"),
				"fieldname": 'import_tax',
				"fieldtype": "float",
				"width": 100
			},
			{
				"label": _("Capital Purchase"),
				"fieldname": 'capital_purchase',
				"fieldtype": "float",
				"width": 100
			},
			{
				"label": _("Capital Tax"),
				"fieldname": 'capital_tax',
				"fieldtype": "float",
				"width": 100
			}			

	]
	return columns	

def get_condition(filters):

	conditions=" "
	if filters.get("year"):
		conditions += " AND year(pi.posting_date)='%s'" % filters.get('year')

	if filters.get("company"):
		conditions += " AND pi.company='%s'" % filters.get('company')

	if filters.get("from_date") and filters.get("to_date"):
		conditions += " AND pi.posting_date between '{0}' and '{1}' ".format(filters.get("from_date"), filters.get("to_date"))

	return conditions

def get_data(filters):
	conditions = get_condition(filters)	
	head = "Vat claim due"
	vat = "Vat on Import"
	doc = frappe.db.sql("""
		Select 
		pi.company,
		posting_date,
		monthname(pi.posting_date) as month,
		year(pi.posting_date) as year,
		pi.name as invoice_no,
		pi.supplier_name,
		s.pan as supplier_pan_no,
		pi.is_import_services as is_service,

		CASE 
		WHEN pi.total >= 0 THEN
		(SELECT pii.item_name from `tabPurchase Invoice Item` as pii  
		Left join `tabPurchase Invoice` as pd on pd.name  = pii.parent 
		where pd.posting_date = pi.posting_date 
		and pd.docstatus=1  
		and pd.name = pi.name 
		order by pii.idx asc LIMIT 1)
		END as gsi_or_purchase,

		pi.total_qty,
		
		CASE
		WHEN pi.country != "Nepal" and pi.is_import_services = 0
		THEN 
		(select je.custom_valuation_amount from `tabJournal Entry` as je
		Left Join `tabPurchase Invoice` as pd on pd.name = je.purchase_invoice_no
		where pd.docstatus = 1
        and voucher_type = "Import Purchase"
		and pd.name = pi.name
		LIMIT 1)

		WHEN pi.country = "Nepal" or pi.is_import_services = 1
		THEN pi.total
		
		ELSE 0 
		END as total,
		IF(pi.exempted_from_tax > 1 and pi.country = "Nepal", pi.total, 0) as exempted_purchase,

		IF(pi.exempted_from_tax > 1 and pi.country != "Nepal", pi.total, 0) as exempted_import,

		pi.country,
		
		CASE  
		WHEN pi.country = "Nepal" and pii.is_fixed_asset = 0 and pi.exempted_from_tax = 0 THEN
		(select sum(pii.amount) from `tabPurchase Invoice Item` as pii  
		Left join `tabPurchase Invoice` as pd on pd.name  = pii.parent 
		where pd.posting_date = pi.posting_date 
		and pii.is_fixed_asset = 0 
		and pd.name = pi.name
		and pd.docstatus=1)

		Else 0
		END as taxable_purchase,

		CASE  
		WHEN pi.country = "Nepal" and pii.is_fixed_asset = 0 and pi.exempted_from_tax = 0 THEN
		(select ROUND(sum(pii.amount)*13/100) from `tabPurchase Invoice Item` as pii  
		Left join `tabPurchase Invoice` as pd on pd.name  = pii.parent 
		where pd.posting_date = pi.posting_date 
		and pii.is_fixed_asset = 0 
		and pd.name = pi.name
		and pd.exempted_from_tax = 0
		and pd.docstatus=1)

		ELSE 0
		END as local_tax,

		CASE  
		WHEN pi.country != "Nepal" and pi.exempted_from_tax = 0 
		and pii.is_fixed_asset = 0 and pi.is_import_services = 0
		THEN	
		(select je.custom_valuation_amount from `tabJournal Entry` as je
		Left Join `tabPurchase Invoice` as pd on pd.name = je.purchase_invoice_no
		where pd.docstatus = 1
        and voucher_type = "Import Purchase"
		and pd.name = pi.name
		LIMIT 1)
  
		WHEN pi.country != "Nepal" and pi.exempted_from_tax = 0
		and pii.is_fixed_asset = 0 and pi.is_import_services = 1
		THEN	
		(Select pd.total from `tabPurchase Invoice` pd 
		where pd.name = pi.name)

		ELSE 0	
		END as taxable_import,

		CASE  
		WHEN pi.country != "Nepal" and pi.exempted_from_tax = 0 
		and pii.is_fixed_asset = 0 and pi.is_import_services = 0
		THEN	
		(Select Round(jea.debit) from `tabJournal Entry Account`  jea
		Join `tabJournal Entry` je on je.name = jea.parent
		where je.docstatus = 1
       
        and je.voucher_type = "Import Purchase"
		and je.purchase_invoice_no = pi.name
		and jea.account Like '{0}%' 
		)

		WHEN pi.country != "Nepal" and pi.exempted_from_tax = 0
		and pii.is_fixed_asset = 0 and pi.is_import_services = 1
		THEN	
		(Select ptc.tax_amount from `tabPurchase Taxes and Charges` as ptc
		Join  `tabPurchase Invoice` as pd on pd.name = ptc.parent 
		where pd.docstatus =1
		and pd.name = pi.name		
		and ptc.account_head Like '{1}%' 
 	  	Order by pd.docstatus desc
		limit 1)

		ELSE 0
		END as import_tax,
	
		CASE  
		WHEN pi.country = "Nepal" and pi.exempted_from_tax = 0 and pii.is_fixed_asset = 1 THEN
		(select sum(pii.amount) from `tabPurchase Invoice Item` as pii  
		inner join `tabPurchase Invoice` as pd on pd.name  = pii.parent 
		where pd.posting_date = pi.posting_date 
		and pd.name = pi.name
		and pii.is_fixed_asset = 1 
		and pd.docstatus=1
		LIMIT 1 )
		
		Else 0
		END as capital_purchase,

		
		CASE  
		WHEN pi.country = "Nepal" and pi.exempted_from_tax = 0 and pii.is_fixed_asset = 1  THEN
		(select ROUND((sum(pii.amount))*13/100) from `tabPurchase Invoice Item` as pii  
		inner join `tabPurchase Invoice` as pd on pd.name  = pii.parent 
		where pd.posting_date = pi.posting_date 
		and pd.name = pi.name
		and pii.is_fixed_asset = 1 
		and pd.docstatus=1
		LIMIT 1)

		ELSE 0
		END as capital_tax,

		pp_no as pp_no,
		bill_date as pp_date

		from `tabPurchase Invoice` as pi
		left join `tabSupplier` as s
		on s.name = pi.supplier
		left join `tabPurchase Invoice Item` as pii
		on pii.parent = pi.name		

		where pi.docstatus=1 {2}

		group by 
		pi.posting_date asc,
		monthname(pi.posting_date) asc, 
		pi.company,
		year,
		invoice_no,
		pi.supplier_name,
		supplier_pan_no,
		pi.total_qty,
		pi.total,
		exempted_purchase,
		taxable_purchase,
		local_tax,
		taxable_import,
		import_tax,
		capital_purchase,
		capital_tax,
		gsi_or_purchase

		""".format(vat, head, conditions), as_dict=1)

	# print(doc)
	return doc

# Old column K Taxable Import
	# CASE  
		# WHEN pi.country != "Nepal" and pi.exempted_from_tax = 0 and pii.is_fixed_asset = 0 THEN	
		# (select sum(pii.amount) from `tabPurchase Invoice Item` as pii  
		# inner join `tabPurchase Invoice` as pd on pd.name  = pii.parent 
		# where pd.posting_date = pi.posting_date 
		# and pii.is_fixed_asset = 0 
		# and pd.name = pi.name
		# and pd.docstatus=1)

		# ELSE 0	
		# END as taxable_import,