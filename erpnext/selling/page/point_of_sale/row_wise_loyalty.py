from typing import KeysView
from tomlkit import key
import frappe

@frappe.whitelist()
def row_wise_loyalty_point(name):
	points=00
	excluded_items = []
	excluded_item_groups = []
	included_item_groups = []
	# t_points=00
	pos_in= frappe.get_doc("POS Invoice",{"name":name},["*"])
	print("KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK",pos_in)
	lp=frappe.db.get_value("Customer",{"name":pos_in.customer},["loyalty_program"])
	condition=frappe.get_doc("Loyalty Program",lp)
	

	if lp:
		for ex in condition.exclusion_list:
			if ex.get("item"):

				excluded_items.append(ex.get("item"))
			if ex.get("item_group"):
				parent_ig = frappe.get_doc("Item Group",ex.get("item_group")) 
				child_ig = frappe.db.get_all("Item Groups",{'lft':[">",parent_ig.get("lft")],'rgt':['<',parent_ig.get("rgt")]},['name'])
				if child_ig:
					for all in child_ig:
						excluded_item_groups.append(all.name)
		print("child_ig***********************",excluded_item_groups)
		for r in pos_in.get("items"):
			for i in condition.detailed_item_groups:

				
				print("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMdocid",excluded_item_groups,excluded_items)
				if i.get("item_group") == r.get("item_group") and r.get("item_group") not in excluded_item_groups:
					
					
									# if i.document_id in pos_in.get("items"):
					if r.amount >= i.minimum_total_spend:
						print("con satisfied")
						print("point generation",r.amount,i.collection_factor)
						point=int(r.amount*i.collection_factor)
						print("point generation",point)
						points+=point
			# if i.get("documet_id") == "Item":
				if i.get("document_id") == r.get("item_code") and r.get("item") not in excluded_items:
				# if i.document_id in pos_in.get("items"):
					if r.amount >= i.minimum_total_spend:
						point=int(r.amount/i.collection_factor)
						points+=point		

	for k in condition.pos_invoice_wise_loyalty_points:
		if k.get("field_name") in pos_in.get():
			if pos_in.get(k.field_name) >= k.minimum_total_spend:		
				point1=int(pos_in.get(k.field_name)/k.collection_factor)
				points+=point1


	lpe=frappe.new_doc("Loyalty Point Entry")
	lpe.loyalty_program=pos_in.loyalty_program
	lpe.customer=pos_in.customer
	lpe.invoice_type=pos_in.doctype
	lpe.invoice=pos_in.name
	lpe.loyalty_points=points
	lpe.expiry_date=condition.to_date
	lpe.posting_date=condition.from_date
	lpe.save(ignore_permissions=True)
	lpe.submit()
	return True