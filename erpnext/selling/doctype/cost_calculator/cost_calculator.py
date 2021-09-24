# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CostCalculator(Document):
	@frappe.whitelist()
	def get_bom(self):
		cd=[]
		doc=frappe.db.sql("""Select b.name from `tabBOM` b join `tabItem` i on b.item=i.item_code where b.docstatus=1 and i.has_variants=1 """,as_dict=1)
		for i in doc:
			cd.append(i.name)
		return cd

	@frappe.whitelist()
	def get_all_value(self):
		doc=frappe.get_doc("BOM",self.template_bom)
		for i in doc.items:
			self.append("raw_material_items",{
				"item_code":i.item_code,
				"item_name":i.item_name,
				"qty":i.qty,
				"weight_uom":i.weight_uom,
				"rate":i.rate,
				"amount":i.amount,
				"scrap":i.scrap
			})
		for i in doc.scrap_items:					
			self.append("scrap_items",{
				"item_code":i.item_code,
				"item_name":i.item_name,
				"qty":i.stock_qty,
				"weight_uom":i.stock_uom,
				"rate":i.rate,
				"amount":i.amount,
				})


	@frappe.whitelist()
	def get_qty(self):
		for i in self.raw_material_items:
			i.qty=self.qty
		for i in self.scrap_items:
			i.qty=self.qty
		weight=[]
		amount=[]
		for i in self.raw_material_items:
			if i.item_code:
				i.amount=i.qty*i.rate
				i.weight=i.qty*i.wp_unit
				weight.append(i.weight)
				amount.append(i.amount)
		self.total_raw_material_weight=sum(weight)
		self.raw_material_total_amount=sum(amount)
		sweight=[]
		samount=[]
		for i in self.scrap_items:
			if i.item_code:
				i.amount=i.qty*i.rate
				i.weight=i.qty*i.wp_unit
				sweight.append(i.weight)
				samount.append(i.amount)
		self.total_scrap_weight=sum(sweight)
		self.scrap_total_amount_=sum(samount)
		for i in self.add_ons:
			i.qty=self.qty
			if i.item_code:
				i.amount=i.qty*i.rate*i.factor
				
	@frappe.whitelist()
	def calculate_formula(self):
		for j in self.raw_material_items:
			try:
				if j.formula:
					formula= j.formula
					d="{"+str(j.item_attributes)+"}"
					c=eval(d)
					for i in c:
						formula=formula.replace(i,str(c[i]))
					formu=eval(formula)
					j.wp_unit=formu
			except:
				print("")

	@frappe.whitelist()
	def calculate_formula_bom_item(self):
		for j in self.scrap_items:
			try:
				if j.formula:
					formula= j.formula
					d="{"+str(j.item_attributes)+"}"
					c=eval(d)
					for i in c:
						formula=formula.replace(i,str(c[i]))
					formu=eval(formula)
					j.wp_unit=formu
			except:
				print("")



	@frappe.whitelist()
	def calculate_formula_scrap_item(self):
		try:
			if self.formula:
				formula= self.formula
				d="{"+str(self.item_attributes)+"}"
				c=eval(d)
				for i in c:
					formula=formula.replace(i,str(c[i]))
				formu=eval(formula)
				self.wp_unit=formu
		except:
				print("")