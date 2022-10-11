from typing import KeysView
from tomlkit import key
import frappe

@frappe.whitelist()
def row_wise_loyalty_point(name):
	points=00
	# t_points=00
	pos_in= frappe.get_doc("POS Invoice",{"name":name},["*"])
	print("KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK",pos_in)
	lp=frappe.db.get_value("Customer",{"name":pos_in.customer},["loyalty_program"])
	condition=frappe.get_doc("Loyalty Program",lp)
	if lp:
		for r in pos_in.get("items"):
			for i in condition.row_wise_loyalty_point:
				print("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM",r)
				if i.get("document_id") == r.get("item_group"):
				# if i.document_id in pos_in.get("items"):
					if i.collection_factor >= i.minimum_total_spend:
						point=int(r.amount/i.collection_factor)
						points+=point

				if i.get("document_id") == r.get("item_code"):
				# if i.document_id in pos_in.get("items"):
					if i.collection_factor >= i.minimum_total_spend:
						point=int(r.amount/i.collection_factor)
						points+=point		

	print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@",points)
	for k in condition.pos_invoice_wise_loyalty_point:
		if k.get("field_name") in pos_in.get():
			if k.collection_factor >= k.minimum_total_spend:		
		# for r in pos_in.get("items"):
		# 	for i in condition.row_wise_loyalty_point:
		# 		print("MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM",r.get("item_group"))
		# 		if i.get("document_id") in r.get():
		# 		# if i.document_id in pos_in.get("items"):
		# 			if i.collection_factor >= i.minimum_total_spend:
		# 				point=int(r.amount/i.collection_factor)
		# 				points+=point

			# print("LLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL0",pos_in.get(k.field_name))
				point1=int(pos_in.get(k.field_name)/k.collection_factor)
				points+=point1
	# print("OOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOO",point1)
		# t_points+=pos_pt
		# print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$",pos_pt)
	if points > 0:
		lpe=frappe.new_doc("Loyalty Point Entry")
		lpe.loyalty_program=pos_in.loyalty_program
		lpe.customer=pos_in.customer
		lpe.invoice_type=pos_in.doctype
		lpe.invoice=pos_in.name
		lpe.loyalty_points=points
		lpe.expiry_date=condition.to_date
		lpe.posting_date=condition.from_date
		lpe.save()
		return True
