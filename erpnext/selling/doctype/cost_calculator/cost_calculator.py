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
				"stock_uom":i.stock_uom,
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
				"stock_uom":i.stock_uom,
				"rate":i.rate,
				"amount":i.amount,
				})	
		doc1=frappe.get_doc("Item",self.item_code)
		for i in doc1.add_ons:
			self.append("add_ons",{
				"item_code":i.item_code,
				"qty":i.qty,
				"stock_uom":i.unit_of_measure,
				"factor":i.qty_conversion_factor
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
				if i.scrap > 0:
					i.weight=i.qty*i.wp_unit*(1+i.scrap/100)
				else:
					i.weight=i.qty*i.wp_unit+1
				weight.append(i.weight)
				amount.append(i.amount)
		self.total_raw_material_weight=sum(weight)
		self.raw_material_total_amount=sum(amount)
		sweight=[]
		samount=[]
		for i in self.scrap_items:
			if i.item_code:
				i.amount=i.qty*i.rate
				i.weight=i.qty*i.weight_per_unit
				sweight.append(i.weight)
				samount.append(i.amount)
		self.total_scrap_weight=sum(sweight)
		self.scrap_total_amount_=sum(samount)
		aamount=[]
		for i in self.add_ons:
			i.qty=self.qty
			if i.item_code:
				i.amount=i.qty*i.rate*i.factor
				aamount.append(i.amount)
		self.add_ons_amount_=sum(aamount)

	@frappe.whitelist()
	def calculate_value_raw(self):
		weight=[]
		amount=[]
		for i in self.raw_material_items:
			if i.item_code:
				i.amount=i.qty*i.rate
				if i.scrap > 0:
					i.weight=i.qty*i.wp_unit*(1+i.scrap/100)
				else:
					i.weight=i.qty*i.wp_unit+1
				weight.append(i.weight)
				amount.append(i.amount)
		self.total_raw_material_weight=sum(weight)
		self.raw_material_total_amount=sum(amount)

	@frappe.whitelist()
	def calculate_value_scrap(self):
		sweight=[]
		samount=[]
		for i in self.scrap_items:
			if i.item_code:
				i.amount=i.qty*i.rate
				i.weight=i.qty*i.weight_per_unit
				sweight.append(i.weight)
				samount.append(i.amount)
		self.total_scrap_weight=sum(sweight)
		self.scrap_total_amount_=sum(samount)
		
	@frappe.whitelist()
	def calculate_value_addons(self):
		aamount=[]
		for i in self.add_ons:
			i.qty=self.qty
			if i.item_code:
				i.amount=i.qty*i.rate*i.factor
				aamount.append(i.amount)
		self.add_ons_amount_=sum(aamount)
				
	@frappe.whitelist()
	def calculate_formula(self):
		for j in self.raw_material_items:
			if j.item_attributes:
				d="{"+str(j.item_attributes)+"}"
				c=eval(d)
				lst=[]
				for i in c:
					lst.append(c[i])
				t=tuple(lst)
				if len(t) > 1:
					doc=frappe.db.sql("""select distinct i.name from `tabItem` i join `tabItem Variant Attribute` ia on i.name=ia.parent
								where i.variant_of='{0}' and attribute_value in {1}""".format(j.item_code,t),as_dict=1)
				else:
					ls=c[i].strip(",")
					doc=frappe.db.sql("""select distinct i.name from `tabItem` i join `tabItem Variant Attribute` ia on i.name=ia.parent
								where i.variant_of='{0}' and attribute_value = '{1}'""".format(j.item_code,c[i]),as_dict=1)
				if doc:
					for k in doc:
						tab=frappe.db.get_value("Item Price",{"item_code":k.name,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]},["name"])
						if tab:
							doc1=frappe.get_doc("Item Price",{"item_code":k.name,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
							j.rate=doc1.price_list_rate
				if not doc:
					tab=frappe.db.get_value("Item Price",{"item_code":j.item_code,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]},["name"])
					if tab:
						doc1=frappe.get_doc("Item Price",{"item_code":j.item_code,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
						j.rate=doc1.price_list_rate
		for j in self.raw_material_items:
			weight=[]
			amount=[]
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
		return True
	@frappe.whitelist()
	def calculate_formula_scrap_item(self):
		for j in self.scrap_items:
			if j.item_attributes:
				d="{"+str(j.item_attributes)+"}"
				c=eval(d)
				lst=[]
				for i in c:
					lst.append(c[i])
				t=tuple(lst)
				if len(t) > 1:
					doc=frappe.db.sql("""select distinct i.name from `tabItem` i join `tabItem Variant Attribute` ia on i.name=ia.parent
								where i.variant_of='{0}' and attribute_value in {1}""".format(j.item_code,t),as_dict=1)
				if len(t) == 1:
					ls=c[i].strip(",")
					doc=frappe.db.sql("""select distinct i.name from `tabItem` i join `tabItem Variant Attribute` ia on i.name=ia.parent
								where i.variant_of='{0}' and attribute_value = '{1}'""".format(j.item_code,c[i]),as_dict=1)
				if doc:
					for k in doc:
						tab=frappe.db.get_value("Item Price",{"item_code":k.name,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]},["name"])
						if tab:
							doc1=frappe.get_doc("Item Price",{"item_code":k.name,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
							j.rate=doc1.price_list_rate
				if not doc:
					tab=frappe.db.get_value("Item Price",{"item_code":j.item_code,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]},["name"])
					if tab:
						doc1=frappe.get_doc("Item Price",{"item_code":j.item_code,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
						j.rate=doc1.price_list_rate
		sweight=[]
		samount=[]
		for j in self.scrap_items:
			try:
				if j.formula:
					formula= j.formula
					d="{"+str(j.item_attributes)+"}"
					c=eval(d)
					for i in c:
						formula=formula.replace(i,str(c[i]))
					formu=eval(formula)
					j.weight_per_unit=formu
					print("***********************",formu)
			except:
				print("")
		return True

	# @frappe.whitelist()
	# def calculate_formula_scrap_item(self):
	# 	try:
	# 		if self.formula:
	# 			formula= self.formula
	# 			d="{"+str(self.item_attributes)+"}"
	# 			c=eval(d)
	# 			for i in c:
	# 				formula=formula.replace(i,str(c[i]))
	# 			formu=eval(formula)
	# 			self.wp_unit=formu
	# 	except:
	# 			print("")

		