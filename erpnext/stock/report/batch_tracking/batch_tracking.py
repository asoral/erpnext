# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


batch_details = []
def execute(filters=None):
	data = []
	columns = get_columns(filters)
	conditions = get_conditions(filters)
	
	level_up_se(filters.get("batch"))
	for d in batch_details:
		# data.append('')
		print("sata", d)
		data.append({
			'level': filters.get('level'),
			'item' : d.get('item_code'),
			'item_name' : d.get('item_name'),
			'type': frappe.get_value('Item', {'name': d.get('item_code')}, ["bom_item_type"]),
			'voucher_type' : frappe.get_value('Stock Entry', { 'name': d.get('parent') }, ['stock_entry_type']),
			'voucher' : d.get('parent'),
			'qty': d.get('qty'),
			'batch': d.get('batch_no')
		})
	# data = get_data(conditions, filters)
	l= 0
	for i in range ( 1, filters.get('level')):
		print('Level', filters.get('level'))

	batch_details.clear()
	return columns,data
	


def get_columns(filters):
	print(" Thisget_columns(filters)")
	
	lst =[
			{
				"fieldname": "level",
				"label": "Level",
				"width": 50,
				"options": 'int',
			},
			{
				"fieldname": "item",
				"label": "Item",
				"width": 100,
				"fieldtype": "Link",
				"options": "Item"
			},			
			{
				"fieldname": "item_name",
				"label": "Item Name",
				"width": 100,
				"fieldtype": "Data",
			},
			{
				"fieldname": "type",
				"label": "Type",
				"width": 50,
				"fieldtype": "Data"
			},
			{
				"fieldname": "voucher_type",
				"label": "Voucher Type",
				"width": 100,
				"fieldtype": "Data"
			},
			{
				"fieldname": "voucher",
				"label": "Voucher",
				"width": 100,
				"fieldtype": "Link",
				"options": "Stock Entry"
			},
			{
				"fieldname": "qty",
				"label": "Qty",
				"width": 80,
				"fieldtype": "Float"
				
			},
			{
				"fieldname": "batch",
				"label": "Batch",
				"width": 100,
				"fieldtype": "Link",
				"options": "Batch"
			}
		]
		
	return lst	


def get_conditions(filters):
	print("get_conditions(filters)")
	conditions = ""
	
	if filters.get("company"):
		conditions += " AND dpi.company = %(company)s"

	if filters.get("batch"):
		conditions += " AND dpi.batch = %(batch)s"

	if filters.get("level"):
		conditions += " AND dpi.level = %(level)s"
		
	if filters.get("workorder"):
		conditions += " AND dpi.workorder = %(workorder)s"

	return conditions	

def get_batch_tracking(company, level, batch, wo= None):
	new_entries = []
	se_item = frappe.db.sql("""
								Select sed.item_code, sed.qty, sed.basic_rate, sed.batch_no, sed.amount, se.name, se.stock_entry_type,
								se.work_order, se.company 
								from `tabStock Entry Detail` sed 
								Join `tabStock Entry` se
								where se.company = "{0}"
								and se.stock_entry_type = "Manufacture"
								and sed.docstatus = 1
								and sed.is_finished_item = 1
								and batch_no = "{1}"
							
								Limit 1
							""".format(company, batch))

	get_material_consumed(se_item.get('company'), se_item.get('workorder'))					


	def get_material_consumed(company, workorder ):		
		se_consumed = frappe.db.sql("""
										Select sed.item_code, sed.qty, sed.basic_rate, sed.batch_no, sed.amount, se.name, 
										se.stock_entry_type, se.work_order 
										from `tabStock Entry Detail` sed 
										Join `tabStock Entry` se 
										where se.company = "{0}"
										and se.stock_entry_type = "Material Consumption for Manufacture"
										and sed.docstatus = 1
										
										and se.work_order = "{1}"
									""".format(''compan)

		for s in se_consumed:
			if s.get('is_finised_item') != 1:
				new_entries.append(s)

	return new_entries			

def level_up_se(se_m):
	
		soi_so = frappe.get_value("Stock Entry Detail", {"batch_no" : se_m}, ['parent'])
		if soi_so:
			print("This is soi_so ", soi_so, se_m)
			soi_se = frappe.get_value("Stock Entry", {"name": soi_so, "stock_entry_type": 'Manufacture'}, ["work_order"])
			se_01 = frappe.get_value("Stock Entry", { "work_order": soi_se, "stock_entry_type" : "Material Transfer for Manufacture" }, ["name"])

			if se_01:
				print(" se 01 ", se_01)
				se_02 = frappe.db.get_all("Stock Entry Detail", {"parent" : se_01}, ['*'])
				
				if se_02:
					print(" se 01 ", se_02)
					for s in se_02:
						
						print('s', s)
						if s.get('is_finished_item'):
							print("inside is finised")
							level_up_se(s.get('batch_no'))	
						else:
							batch_details.append(s)	
							print("neew",s)	

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_com_batch(doctype, txt, searchfield, start, page_len, filters):
	company = filters.get('company')
	batch = frappe.db.sql("""
							Select b.name from `tabBatch` b
							Join `tabStock Entry Detail` sed ON sed.batch_no = b.name
							Join `tabStock Entry` se ON se.name = sed.parent
							Where 
							se.docstatus = 1
							and se.stock_entry_type = "Manufacture"
							and se.company = '{0}'
						""".format(company), as_list=1 )
	return batch			

			