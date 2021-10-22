# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import erpnext
from frappe.model.document import Document

class Container(Document):
	def validate(self):
		self.weight_cbm_percentage()

	@frappe.whitelist()
	def delivery_note(self):
		adoc=[]
		for i in self.ventures_list:
			adoc.append(i.venture_id)
		adoc=set(adoc)
		adoc=list(adoc)
		for j in adoc:
			cdoc=frappe.db.get_all("Ventures",{"parent":self.name,"venture_id":j},["name"])
			for k in cdoc:
				vdoc=frappe.get_doc("Ventures",{"name":k.name})
				sdoc=frappe.get_doc("Sales Order",vdoc.order_no)
				doc=frappe.new_doc("Delivery Note")
				doc.customer=vdoc.venture_id
				doc.container = self.name
				doc.transporter = sdoc.transporter
				idoc=frappe.get_doc("Item",vdoc.product)
				doc.append('items', {
						'item_code': vdoc.product,
						'warehouse': self.warehouse,
						'qty': vdoc.venture_qty,
						'stock_qty': vdoc.venture_qty,
						'uom': idoc.stock_uom,
						'stock_uom': idoc.stock_uom,
						'conversion_factor':1,
						'against_sales_order': vdoc.order_no,
						# "warehouse":vdoc.warehouse
					})

				if sdoc.additional_discount_percentage:
					doc.additional_discount_percentage = sdoc.additional_discount_percentage

				if sdoc.apply_discount_on:	
					doc.apply_dicount_on = sdoc.apply_discount_on

				if sdoc.taxes_and_charges:
					doc.taxes_and_charges = sdoc.taxes_and_charges

				
				if sdoc.tc_name:	
					doc.tc_name = sdoc.tc_name

				
				if sdoc.transporter:	
					doc.transporter = sdoc.transporter

				for i in sdoc.taxes:
					doc.append('taxes', {
						"category":i.category,
						"add_deduct_tax":i.add_deduct_tax,
						"charge_type":i.charge_type,
						"row_id":i.row_id,
						"included_in_print_rate":i.included_in_print_rate,
						"included_in_paid_amount":i.included_in_paid_amount,
						"description":i.description,
						"account_head":i.account_head,
						"cost_center":i.cost_center
					})
				
				doc._action = "save"
				doc.validate()
				doc.insert()

			
				
				frappe.db.commit()				
				

		return True
	
				
	
	@frappe.whitelist()
	def purchase_receipt(self):
		adoc=[]
		for i in self.ventures_list:
			adoc.append(i.venture_id)
		adoc=set(adoc)
		adoc=list(adoc)
		for j in adoc:
			cdoc=frappe.db.get_all("Ventures",{"parent":self.name,"venture_id":j},["name"])
			for k in cdoc:
				vdoc=frappe.get_doc("Ventures",{"name":k.name})
				pdoc=frappe.get_doc("Purchase Order",vdoc.order_no)
				doc=frappe.new_doc("Purchase Receipt")
				doc.supplier=vdoc.venture_id
				doc.container = self.name
				# doc.transporter = pdoc.transporter
				idoc=frappe.get_doc("Item",vdoc.product)
				doc.append('items', {
						'item_code': vdoc.product,
						'warehouse': self.warehouse,
						'qty': vdoc.venture_qty,
						'stock_qty': vdoc.venture_qty,
						'uom': idoc.stock_uom,
						'stock_uom': idoc.stock_uom,
						'conversion_factor':1,
						'purchase_order': vdoc.order_no,
						# "warehouse":vdoc.warehouse
					})

				if pdoc.additional_discount_percentage:
					doc.additional_discount_percentage = pdoc.additional_discount_percentage

				if pdoc.apply_discount_on:	
					doc.apply_dicount_on = pdoc.apply_discount_on

				if pdoc.taxes_and_charges:
					doc.taxes_and_charges = pdoc.taxes_and_charges
				for i in pdoc.taxes:
					doc.append('taxes', {
						"category":i.category,
						"add_deduct_tax":i.add_deduct_tax,
						"charge_type":i.charge_type,
						"row_id":i.row_id,
						"included_in_print_rate":i.included_in_print_rate,
						"included_in_paid_amount":i.included_in_paid_amount,
						"description":i.description,
						"account_head":i.account_head,
						"cost_center":i.cost_center
					})
				if pdoc.tc_name:	
					doc.tc_name = pdoc.tc_name

				
				# if pdoc.transporter:	
				# 	doc.transporter = pdoc.transporter

				
				doc._action = "save"
				doc.validate()
				doc.insert()

			
				
				frappe.db.commit()				
				

		return True
	
				

	def weight_cbm_percentage(self):
		if self.container_type:
			doc=frappe.get_doc("Container Type",self.container_type)
			weight=[]
			cbm=[]
			for i in self.ventures_list:
				weight.append(i.total_weight)
				cbm.append(i.total_cbm)
			a=sum(weight)
			b=sum(cbm)
			tweight=a/doc.max_allowed_weight*100
			tcbm=b/doc.max_cbm*100
			print(tweight)
			print(tcbm)
			if tweight  < 100 and tcbm <100:
				self.weight_percentage=tweight
				self.cbm_percentage=tcbm
			else:
				frappe.throw("Container weight percentage Or cbm percentage should be <=100")

	@frappe.whitelist()
	def set_updating_qty(self):
		for i in self.ventures_list:
			if self.warehouse and i.product:
				doc=frappe.db.get_all("Bin",{"item_code":i.product,"warehouse":self.warehouse},["projected_qty"])
				for j in doc:
					qty=[]
					qty.append(j.projected_qty)
					i.qty_ordered=sum(qty)
		return True



	@frappe.whitelist()
	def make_landed_cost_voucher(self):
		pdoc=frappe.db.get_all("Purchase Receipt",{"container":self.name},["name"])
		for i in pdoc:
			doc=frappe.new_doc("Landed Cost Voucher")
			doc.distribute_charges_based_on="Qty"
			doc.container=self.container
			purchase=frappe.get_doc("Purchase Receipt",i.name)
			doc.append('purchase_receipts', {
				"receipt_document_type":"Purchase Receipt",
				"receipt_document":purchase.name,
				"supplier":purchase.supplier,
				"grand_total":purchase.grand_total,
				"posting_date":purchase.posting_date
				
			})
			self.set("items", [])
			if i.name:
				pr_items = frappe.db.sql("""select pr_item.item_code, pr_item.description,
					pr_item.qty, pr_item.base_rate, pr_item.base_amount, pr_item.name,
					pr_item.cost_center, pr_item.is_fixed_asset
					from `tabPurchase Receipt Item` pr_item where parent = '{0}'
					and exists(select name from tabItem
						where name = pr_item.item_code and (is_stock_item = 1 or is_fixed_asset=1))
					""".format(i.name), as_dict=True)

				for d in pr_items:
					item = doc.append("items")
					item.item_code = d.item_code
					item.description = d.description
					item.qty = d.qty
					item.rate = d.base_rate
					item.cost_center = d.cost_center or \
						erpnext.get_default_cost_center(self.company)
					item.amount = d.base_amount
					item.receipt_document_type = "Purchase Receipt"
					item.receipt_document = i.name
					item.purchase_receipt_item = d.name
					item.is_fixed_asset = d.is_fixed_asset
					# item.applicable_charges=0
			cdoc=frappe.get_doc("Container Settings")
			if self.oceanair_freight > 0:
				doc.append("taxes",{
					"expense_account":cdoc.oceanair_freight,
					"amount":self.oceanair_freight
				})
			if self.cargo_insurance > 0:
				doc.append("taxes",{
					"expense_account":cdoc.cargo_insurance,
					"amount":self.cargo_insurance
				})
			if self.customs_broker_fee > 0:
				doc.append("taxes",{
					"expense_account":cdoc.customs_broker_fee,
					"amount":self.customs_broker_fee
				})
			if self.incidentalmisc > 0:
				doc.append("taxes",{
					"expense_account":cdoc.incidentalmisc,
					"amount":self.incidentalmisc
				})
			if self.drayage >0:
				doc.append("taxes",{
					"expense_account":cdoc.drayage,
					"amount":self.drayage
				})
			if self.warehousing > 0:
				doc.append("taxes",{
					"expense_account":cdoc.warehousing,
					"amount":self.warehousing
				})
			if self.bank_charge > 0:
				doc.append("taxes",{
					"expense_account":cdoc.bank_charge,
					"amount":self.bank_charge
				})
			if self.finance_charge > 0:
				doc.append("taxes",{
					"expense_account":cdoc.finance_charge,
					"amount":self.finance_charge
				})
			doc.insert(ignore_mandatory=True)
			return True
		