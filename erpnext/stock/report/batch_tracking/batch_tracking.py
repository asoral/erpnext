# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe


batch_details = []
def execute(filters=None):
	data = []
	data1 = []
	columns = get_columns(filters)
	conditions = get_conditions(filters)
	if filters.get('company') and filters.get('batch'):
		level_up_se(filters.get("batch"), data1)
	for d in data1:
		# data.append('')
		
		print("sata", d.get('batch_no'))
		if d.get('indent')+ 1 <= filters.get('level'):
				data.append({
					'level': d.get('indent') + 1,
					'item' : d.get('item_code'),
					'item_name' : d.get('item_name'),
					'type': frappe.get_value('Item', {'name': d.get('item_code')}, ["bom_item_type"]),
					'voucher_type' : frappe.get_value('Stock Entry', { 'name': d.get('parent') }, ['stock_entry_type']),
					'voucher' : d.get('parent'),
					'qty': d.get('qty'),
					'batch': d.get('batch_no')
				})
	# print(" this i sbatch details", batch_details)			
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
				"width": 150,
				"fieldtype": "Link",
				"options": "Item"
			},			
			{
				"fieldname": "item_name",
				"label": "Item Name",
				"width": 200,
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
				"width": 200,
				"fieldtype": "Data"
			},
			{
				"fieldname": "voucher",
				"label": "Voucher",
				"width": 200,
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
				"width": 200,
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
									""".format('company'))

		for s in se_consumed:
			if s.get('is_finised_item') != 1:
				new_entries.append(s)

	return new_entries			

def level_up_se(se_m, data):
		get_manufacture(se_m, data)

				

def get_manufacture(batch, data, indent=0):
			print(" this is Level_up ")
		
			soi_se = frappe.db.sql("""
									Select se.work_order from `tabStock Entry Detail` sed
									Join `tabStock Entry` se ON se.name = sed.parent
									where sed.batch_no = "{0}"
									and se.stock_entry_type = "Manufacture"
										""".format(batch), as_dict=1)	
			if soi_se:
				print(" workorder ", soi_se[0].get('work_order'))
				se_01 = frappe.get_value("Stock Entry", { "work_order": soi_se[0].get('work_order'), "stock_entry_type" : "Material Transfer for Manufacture" }, ["name"])

				if se_01:
					print(" se 01 ", se_01)
					se_02 = frappe.db.get_all("Stock Entry Detail", {"parent" : se_01}, ['*'])
					
					if se_02:
						# print(" se 012222222222 ")
						for s in se_02:
							s["indent"] = indent
							batch_new = s.get('batch_no')

							data.append({
								'item_code': s.item_code,
								'item_name': s.item_name,
								'parent' : s.parent,
								'indent': indent,
								'bom_level': indent,
								"stock_uom" : s.stock_uom,
								"required_qty" : s.qty,
								"qty_to_be_consumed" : s.qty,
								"rate" : s.basic_rate,
								"amount" : s.amount,
								"batch_no" : s.batch_no,
								"consumed_qty" : s.qty,
								'qty': s.qty ,
								'uom': s.uom,
								'description': s.description,
								})

							new_entry = frappe.db.sql("""
														Select se.name from `tabStock Entry Detail` sed
														Join `tabStock Entry` se ON se.name = sed.parent
														where sed.batch_no = "{0}"
														and se.stock_entry_type = "Manufacture"
													""".format(batch_new), as_dict=1)
							# if new_entry:
							print(" new_ entry", new_entry)	
							if new_entry:
								get_manufacture(batch_new, data, indent= indent + 1)
							batch_details.append(s)	

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_com_batch(doctype, txt, searchfield, start, page_len, filters):
	company = filters.get('company')
	batch = frappe.db.sql("""
							Select sed.batch_no from `tabStock Entry Detail` sed 
							Join `tabStock Entry` se ON se.name = sed.parent
							Where 
							se.docstatus = 1
							and se.stock_entry_type = "Manufacture"
							and se.company = '{0}'
						""".format(company), as_list=1 )
	return batch			

			