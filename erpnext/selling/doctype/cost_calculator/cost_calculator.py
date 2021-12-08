# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from datetime import date, datetime
from erpnext.setup.utils import get_exchange_rate
import frappe
from frappe.model.document import Document
# from erpnext.controllers.accounts_controller import set_print_templates_for_taxes

class CostCalculator(Document):
	def validate(self):
		self.set_price_list_currency()
		self.size_formula()
		
	@frappe.whitelist()
	def get_bom(self):
		cd=[]
		doc=frappe.db.sql("""Select b.name from `tabBOM` b join `tabItem` i on b.item=i.item_code where b.docstatus=1 and i.has_variants=1 """,as_dict=1)
		for i in doc:
			cd.append(i.name)
		return cd

	@frappe.whitelist()
	def get_all_value(self):
		lst=frappe.db.get_value("BOM",{"name":self.template_bom},["name"])
		if lst:
			doc=frappe.get_doc("BOM",self.template_bom)
			for i in doc.items:
				itm=frappe.get_doc("Item",i.item_code)
				self.append("raw_material_items",{
					"item_code":i.item_code,
					"item_name":i.item_name,
					"qty":i.qty,
					"type":i.type,
					"operation":i.operation,
					"stock_uom":i.stock_uom,
					"weight_uom":i.weight_uom,
					"rate":i.rate,
					"formula":itm.cost_calculator_formula,
					"include_item_in_manufacturing":i.include_item_in_manufacturing,
					"allow_alternative_item":i.allow_alternative_item,
					"allow_to_change_qty_in_wo_":i.allowed_to_change_qty_in_wo,
					"bom_no":i.bom_no,
					"source_warehouse":i.source_warehouse,
					"amount":i.amount,
					"scrap":i.scrap
				})
			for i in doc.scrap_items:
				itm=frappe.get_doc("Item",i.item_code)					
				self.append("scrap_items",{
					"item_code":i.item_code,
					"item_name":i.item_name,
					"qty":i.stock_qty,
					"formula":itm.cost_calculator_formula,
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
			self.with_operations=doc.with_operations
			self.transfer_material_against=doc.transfer_material_against
			self.routing=doc.routing
			for i in doc.operations:
				self.append("operations",{
					"operation":i.operation,
					"workstation":i.workstation,
					"time_in_mins":i.time_in_mins,
					"hour_rate":i.hour_rate,
					"base_hour_rate":i.base_hour_rate,
					"operating_cost":i.operating_cost,
					"base_operating_cost":i.base_operating_cost,
					"batch_size":i.batch_size,
					"set_cost_based_on_bom_qty":i.set_cost_based_on_bom_qty,
					"cost_per_unit":i.cost_per_unit,
					"base_cost_per_unit":i.base_cost_per_unit,
					"description":i.description,
					"image":i.image,
					"sequence_id":i.sequence_id
				})
		
	
	def before_submit(self):
		for i in self.operations:
			i.time_in_mins=i.time_in_mins*self.qty
			hour=i.time_in_mins*i.hour_rate/60
			i.operating_cost=hour
		idoc=frappe.get_doc("Item",self.item_code)
		variant=frappe.get_doc("Item Variant Settings")
		itemdoc=frappe.db.sql("""select fieldname from `tabDocField` where parent="Item" """,as_dict=1)
		itemvalue=frappe.new_doc("Item")
		itemvalue.variant_of=self.item_code
		itemvalue.cost_calculator=self.name
		itemvalue.item_code=str(self.item_code)+str(self.name)
		itemvalue.item_group=idoc.item_group
		itemvalue.stock_uom=idoc.stock_uom
		itemvalue.end_of_life=idoc.end_of_life
		itemvalue.shelf_life_in_days=idoc.shelf_life_in_days
		d="{"+str(self.item_attribute)+"}"
		c=eval(d)
		for i in c:
			itemvalue.append("attributes",{
					"attribute":i,
					"attribute_value":c[i]
				})
		for field in variant.fields:
			for i in itemdoc:
				if field.field_name==i.fieldname:
					op=field.field_name
					itemvalue.set(op, idoc.get(op))
		itemvalue.insert(ignore_permissions=True)
		self.variant_item_code=itemvalue.name
		frappe.db.commit()

	
	@frappe.whitelist()
	def make_quotation(self):
		doc=frappe.new_doc("Quotation")
		doc.quotation_to=self.quotation_to
		doc.party_name=self.party_name
		doc.cost_calculator=self.name
		doc.append("items",{
			"item_code":self.variant_item_code,
			"qty":self.qty,
			"rate":self.rate_per_unit,
			"weight_per_unit":self.weight_per_unit		
			})
		doc.save()
		frappe.db.commit()
		return True

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
		self.add_ons_amount=sum(aamount)
		total_amount=self.raw_material_total_amount+self.scrap_total_amount_+self.add_ons_amount
		total_weight=self.total_scrap_weight+self.total_raw_material_weight
		if self.qty > 0:
			self.rate_per_unit=total_amount/self.qty
			self.weight_per_unit=total_weight/self.qty
		

			
	@frappe.whitelist()
	def set_price_list_currency(self):
		if self.meta.get_field("posting_date"):
			transaction_date = self.posting_date
		else:
			transaction_date = self.transaction_date
		d=frappe.get_doc("Company",self.company)
		if self.meta.get_field("currency"):
			# price list part
			# if buying_or_selling.lower() == "selling":
			fieldname = "price_list"
			args = "for_buying"
			# else:
			# 	fieldname = "buying_price_list"
			# 	args = "for_buying"

			if self.meta.get_field(fieldname) and self.get(fieldname):
				self.price_list_currency = frappe.db.get_value("Price List",
															   self.get(fieldname), "currency")

				if self.price_list_currency == self.company_currency:
					self.plc_conversion_rate = 1.0

				elif not self.plc_conversion_rate:
					self.plc_conversion_rate = get_exchange_rate(self.price_list_currency,
																 self.company_currency, transaction_date, args)

			# currency
			if not self.currency:
				self.currency = self.price_list_currency
				self.conversion_rate = self.plc_conversion_rate
			elif self.currency == self.company_currency:
				self.conversion_rate = 1.0
			elif not self.conversion_rate:
				self.conversion_rate = get_exchange_rate(self.currency,
														 self.company_currency, transaction_date, args)
		self.base_rate_per_unit=self.conversion_rate*self.rate_per_unit
		self.base_raw_material_total_amount=self.conversion_rate*self.raw_material_total_amount
		self.base_scrap_total_amount=self.conversion_rate*self.scrap_total_amount_
		self.base_add_ons_amount=self.conversion_rate*self.add_ons_amount
		for i in self.raw_material_items:
			i.base_amount=i.amount*self.conversion_rate
		for i in self.scrap_items:
			i.base_amount=i.amount*self.conversion_rate
		for i in self.add_ons:
			i.base_amount=i.amount*self.conversion_rate

	@frappe.whitelist()
	def calculate_value_raw(self):
		weight=[]
		amount=[]
		for i in self.raw_material_items:
			if i.item_code:
				if i.qty and i.rate:
					i.amount=i.qty*i.rate
					if i.scrap > 0:
						i.weight=i.qty*i.wp_unit*(1+i.scrap/100)
					else:
						i.weight=i.qty*i.wp_unit+1
					weight.append(i.weight)
					amount.append(i.amount)
		self.total_raw_material_weight=sum(weight)
		self.raw_material_total_amount=sum(amount)
		total_amount=self.raw_material_total_amount+self.scrap_total_amount_+self.add_ons_amount
		total_weight=self.total_scrap_weight+self.total_raw_material_weight
		if self.qty > 0:
			if total_amount > 0:
				self.rate_per_unit=total_amount/self.qty
			if total_weight > 0:
				self.weight_per_unit=total_weight/self.qty

	@frappe.whitelist()
	def make_bom(self):
		for i in self.raw_material_items:
			
			idoc=frappe.get_doc("Item",i.item_code)
			if idoc.has_variants==1:
				variant=frappe.get_doc("Item Variant Settings")
				itemdoc=frappe.db.sql("""select fieldname from `tabDocField` where parent="Item" """,as_dict=1)
				itemvalue=frappe.new_doc("Item")
				itemvalue.variant_of=i.item_code
				itemvalue.cost_calculator=self.name
				itemvalue.item_code=str(idoc.name)+"-"+str(self.name)
				itemvalue.item_group=idoc.item_group
				itemvalue.stock_uom=idoc.stock_uom
				itemvalue.scope_of_supply=self.name
				itemvalue.end_of_life=idoc.end_of_life
				itemvalue.shelf_life_in_days=idoc.shelf_life_in_days
				d="{"+str(i.item_attributes)+"}"
				c=eval(d)
				for i in c:
					itemvalue.append("attributes",{
							"attribute":i,
							"attribute_value":c[i]
						})
				for field in variant.fields:
					for i in itemdoc:
						if field.field_name==i.fieldname:
							op=field.field_name
							itemvalue.set(op, idoc.get(op))
				itemvalue.insert(ignore_permissions=True)
		for i in self.scrap_items:
			idoc=frappe.get_doc("Item",i.item_code)
			if idoc.has_variants==1:
				variant=frappe.get_doc("Item Variant Settings")
				itemdoc=frappe.db.sql("""select fieldname from `tabDocField` where parent="Item" """,as_dict=1)
				itemvalue=frappe.new_doc("Item")
				itemvalue.variant_of=i.item_code
				itemvalue.item_code=str(idoc.name)+"-"+str(self.name)
				itemvalue.item_group=idoc.item_group
				itemvalue.cost_calculator=self.name
				itemvalue.stock_uom=idoc.stock_uom
				itemvalue.scope_of_supply=self.name
				itemvalue.end_of_life=idoc.end_of_life
				itemvalue.shelf_life_in_days=idoc.shelf_life_in_days
				d="{"+str(i.item_attributes)+"}"
				c=eval(d)
				for i in c:
					itemvalue.append("attributes",{
							"attribute":i,
							"attribute_value":c[i]
						})
				for field in variant.fields:
					for i in itemdoc:
						if field.field_name==i.fieldname:
							op=field.field_name
							itemvalue.set(op, idoc.get(op))
				itemvalue.insert(ignore_permissions=True)
		bom=frappe.get_doc("BOM",self.template_bom)
		bdoc=frappe.new_doc("BOM")
		bdoc.cost_calculator=self.name
		bdoc.item=self.variant_item_code
		bdoc.location=bom.location
		bdoc.quantity=self.qty
		bdoc.currency=self.currency
		bdoc.rm_cost_as_per="Price List"
		bdoc.buying_price_list=self.price_list
		bdoc.with_operations=self.with_operations
		bdoc.transfer_material_against=self.transfer_material_against
		bdoc.routing==self.routing
		for i in self.operations:
			bdoc.append("operations",{
				"operation":i.operation,
				"workstation":i.workstation,
				"time_in_mins":i.time_in_mins,
				"hour_rate":i.hour_rate,
				"base_hour_rate":i.base_hour_rate,
				"operating_cost":i.operating_cost,
				"base_operating_cost":i.base_operating_cost,
				"batch_size":i.batch_size,
				"set_cost_based_on_bom_qty":i.set_cost_based_on_bom_qty,
				"cost_per_unit":i.cost_per_unit,
				"base_cost_per_unit":i.base_cost_per_unit,
				"description":i.description,
				"image":i.image,
				"sequence_id":i.sequence_id
			})
		bdoc.inspection_required=bom.inspection_required
		bdoc.quality_inspection_template=bom.quality_inspection_template
		for i in self.raw_material_items:
			item=frappe.get_doc("Item",i.item_code)
			if item.has_variants==1:
				bdoc.append("items",{
					"item_code":str(i.item_code)+"-"+str(self.name),
					"type":i.type,
					"operation":i.operation,
					"bom_no":i.bom_no,
					"source_warehouse":i.source_warehouse,
					"instruction_":i.instruction_,
					"allow_alternative_item":i.allow_alternative_item,
					"allowed_to_change_qty_in_wo":i.allow_to_change_qty_in_wo_,
					"qty":i.qty,
					"uom":i.stock_uom,
					"rate":i.rate,
					"scrap":i.scrap,
					"weight_per_unit":i.wp_unit,
					"weight_uom":i.weight_uom,
					"include_item_in_manufacturing":i.include_item_in_manufacturing,
					"sourced_by_supplier":i.sourced_by_supplier

				})
			else:
				bdoc.append("items",{
					"item_code":str(i.item_code),
					"type":i.type,
					"operation":i.operation,
					"bom_no":i.bom_no,
					"source_warehouse":i.source_warehouse,
					"instruction_":i.instruction_,
					"allow_alternative_item":i.allow_alternative_item,
					"allowed_to_change_qty_in_wo":i.allow_to_change_qty_in_wo_,
					"qty":i.qty,
					"uom":i.stock_uom,
					"rate":i.rate,
					"scrap":i.scrap,
					"weight_per_unit":i.wp_unit,
					"weight_uom":i.weight_uom,
					"include_item_in_manufacturing":i.include_item_in_manufacturing,
					"sourced_by_supplier":i.sourced_by_supplier

				})
		for i in self.scrap_items:
			item=frappe.get_doc("Item",i.item_code)
			if item.has_variants==1:
				bdoc.append("scrap_items",{
					"item_code":str(i.item_code)+"-"+str(self.name),
					"is_process_loss":i.is_process_loss,
					"qty":i.qty,
					"stock_uom":i.stock_uom,
					"rate":i.rate

				})
		for i in self.add_ons:
			bdoc.append("items",{
				"item_code":str(i.item_code),
				"type":i.type,
				"operation":i.operation,
				"bom_no":i.bom_no,
				"source_warehouse":i.source_warehouse,
				# "instruction_":i.instruction_,
				"allow_alternative_item":i.allow_alternative_item,
				"allowed_to_change_qty_in_wo":i.allow_to_change_qty_in_wo,
				"qty":i.qty,
				"uom":i.stock_uom,
				"rate":i.rate,
				"include_item_in_manufacturing":i.include_item_in_manufacturing,
				"sourced_by_supplier":i.sourced_by_supplier

				})
		bdoc.save()

	@frappe.whitelist()
	def calculate_value_scrap(self):
		sweight=[]
		samount=[]
		for i in self.scrap_items:
			if i.item_code:
				if i.qty and i.rate:
					i.amount=i.qty*i.rate
					i.weight=i.qty*i.weight_per_unit
					sweight.append(i.weight)
					samount.append(i.amount)
		self.total_scrap_weight=sum(sweight)
		self.scrap_total_amount_=sum(samount)
		total_amount=self.raw_material_total_amount+self.scrap_total_amount_+self.add_ons_amount
		total_weight=self.total_scrap_weight+self.total_raw_material_weight
		if self.qty > 0:
			if total_amount:
				self.rate_per_unit=total_amount/self.qty
			if total_weight:
				self.weight_per_unit=total_weight/self.qty


	@frappe.whitelist()
	def calculate_value_addons(self):
		aamount=[]
		for i in self.add_ons:
			# i.qty=self.qty
			if i.item_code:
				if i.qty and i.rate and i.factor:
					i.amount=i.qty*i.rate*i.factor
					aamount.append(i.amount)
		self.add_ons_amount=sum(aamount)
		total_amount=self.raw_material_total_amount+self.scrap_total_amount_+self.add_ons_amount
		total_weight=self.total_scrap_weight+self.total_raw_material_weight
		if self.qty > 0:
			if total_amount:
				self.rate_per_unit=total_amount/self.qty
			if total_weight:
				self.weight_per_unit=total_weight/self.qty	



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
					if not self.price_list:
						for k in doc:
							tab=frappe.db.get_value("Item Price",{"item_code":k.name,"buying":1,"valid_from":["<=",self.posting_date]},["name","valid_upto"],order_by='valid_from desc, batch_no desc, uom desc',as_dict=1)
							tab1=frappe.db.get_value("Item Price",{"item_code":k.name,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]},["name"],order_by='valid_from desc, batch_no desc, uom desc')
							if tab1:
								if tab.valid_upto:
									doc1=frappe.get_doc("Item Price",{"item_code":k.name,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
									j.rate=doc1.price_list_rate
								else:
									if tab:
										docname=frappe.get_doc("Item Price",tab.name)
										a="2150-12-31"
										date=datetime.strptime(a, "%Y-%m-%d")
										docname.valid_upto=date.date()
										docname.save()
										doc1=frappe.get_doc("Item Price",{"item_code":k.name,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
										j.rate=doc1.price_list_rate
					if self.price_list:
						for k in doc:
							tab=frappe.db.get_value("Item Price",{"item_code":k.name,"price_list":self.price_list,"valid_from":["<=",self.posting_date]},["name","valid_upto"],order_by='valid_from desc, batch_no desc, uom desc',as_dict=1)
							tab1=frappe.db.get_value("Item Price",{"item_code":k.name,"price_list":self.price_list,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]},["name"],order_by='valid_from desc, batch_no desc, uom desc')
							if tab1:
								print(tab1)
								if tab.valid_upto:
									doc1=frappe.get_doc("Item Price",{"item_code":k.name,"price_list":self.price_list,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
									j.rate=doc1.price_list_rate
							else:
								if tab:
									docname=frappe.get_doc("Item Price",tab.name)
									a="2150-12-31"
									date=datetime.strptime(a, "%Y-%m-%d")
									docname.valid_upto=date.date()
									docname.save()
									doc1=frappe.get_doc("Item Price",{"item_code":k.name,"price_list":self.price_list,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
									j.rate=doc1.price_list_rate

				if not doc:
					if not self.price_list:
						tab=frappe.db.get_value("Item Price",{"item_code":j.item_code,"buying":1,"valid_from":["<=",self.posting_date]},["name","valid_upto"],order_by='valid_from desc, batch_no desc, uom desc',as_dict=1)
						tab1=frappe.db.get_value("Item Price",{"item_code":j.item_code,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]},["name"],order_by='valid_from desc, batch_no desc, uom desc')
						if tab1 and tab.valid_upto:
							doc1=frappe.get_doc("Item Price",{"item_code":j.item_code,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
							j.rate=doc1.price_list_rate
						else:
							if tab:
								docname=frappe.get_doc("Item Price",tab.name)
								a="2150-12-31"
								date=datetime.strptime(a, "%Y-%m-%d")
								docname.valid_upto=date.date()
								docname.save()
								doc1=frappe.get_doc("Item Price",{"item_code":j.item_code,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
								j.rate=doc1.price_list_rate
					if self.price_list:
						tab=frappe.db.get_value("Item Price",{"item_code":j.item_code,"price_list":self.price_list,"valid_from":["<=",self.posting_date]},["name","valid_upto"],order_by='valid_from desc, batch_no desc, uom desc',as_dict=1)
						tab1=frappe.db.get_value("Item Price",{"item_code":j.item_code,"price_list":self.price_list,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]},["name"],order_by='valid_from desc, batch_no desc, uom desc')
						if tab1 and tab.valid_upto:
							doc1=frappe.get_doc("Item Price",{"item_code":j.item_code,"price_list":self.price_list,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
							j.rate=doc1.price_list_rate
						else:
							if tab:
								docname=frappe.get_doc("Item Price",tab.name)
								a="2150-12-31"
								date=datetime.strptime(a, "%Y-%m-%d")
								docname.valid_upto=date.date()
								docname.save()
								doc1=frappe.get_doc("Item Price",{"item_code":j.item_code,"price_list":self.price_list,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
								j.rate=doc1.price_list_rate
		for j in self.raw_material_items:
			print("$$$$$$$$$$$$$$$$$$$$$",j.idx,"****************************")
			weight=[]
			amount=[]
			try:
				if j.formula:
					formula= j.formula
					d="{"+str(j.item_attributes)+"}"
					c=eval(d)
					print("$$$$$$$$$$$",c)
					for i in c:
						formula=formula.replace(i,str(c[i]))
					print("^^^^^^^^^^^^^^^^^",formula)
					formu=eval(formula)
					print("*********************",formu)
					j.wp_unit=formu
			except:
				print("")
		return True

	@frappe.whitelist()
	def size_formula(self):
		for j in self.raw_material_items:
			try:
				if j.fab_size_formula:
					formula= j.fab_size_formula
					d="{"+str(j.item_attributes)+"}"
					c=eval(d)
					for i in c:
						formula=formula.replace(i,str(c[i]))
					formu=eval(formula)
					j.fab_size=formu
			except:
				print("")


			try:
				if j.cut_size_formula:
					formula= j.cut_size_formula
					d="{"+str(j.item_attributes)+"}"
					c=eval(d)
					for i in c:
						formula=formula.replace(i,str(c[i]))
					formu=eval(formula)
					j.cut_size=formu
			except:
				print("")
		

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
					if not self.price_list:
						for k in doc:
							tab=frappe.db.get_value("Item Price",{"item_code":k.name,"buying":1,"valid_from":["<=",self.posting_date]},["name","valid_upto"],order_by='valid_from desc, batch_no desc, uom desc',as_dict=1)
							tab1=frappe.db.get_value("Item Price",{"item_code":k.name,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]},["name"],order_by='valid_from desc, batch_no desc, uom desc')
							if tab1:
								if tab.valid_upto:
									doc1=frappe.get_doc("Item Price",{"item_code":k.name,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
									j.rate=doc1.price_list_rate
								else:
									if tab:
										docname=frappe.get_doc("Item Price",tab.name)
										a="2150-12-31"
										date=datetime.strptime(a, "%Y-%m-%d")
										docname.valid_upto=date.date()
										docname.save()
										doc1=frappe.get_doc("Item Price",{"item_code":k.name,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
										j.rate=doc1.price_list_rate
					if self.price_list:
						for k in doc:
							tab=frappe.db.get_value("Item Price",{"item_code":k.name,"price_list":self.price_list,"valid_from":["<=",self.posting_date]},["name","valid_upto"],order_by='valid_from desc, batch_no desc, uom desc',as_dict=1)
							tab1=frappe.db.get_value("Item Price",{"item_code":k.name,"price_list":self.price_list,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]},["name"],order_by='valid_from desc, batch_no desc, uom desc')
							if tab1 and tab.valid_upto:
								doc1=frappe.get_doc("Item Price",{"item_code":k.name,"price_list":self.price_list,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
								j.rate=doc1.price_list_rate
							else:
								if tab:
									docname=frappe.get_doc("Item Price",tab.name)
									a="2150-12-31"
									date=datetime.strptime(a, "%Y-%m-%d")
									docname.valid_upto=date.date()
									docname.save()
									doc1=frappe.get_doc("Item Price",{"item_code":k.name,"price_list":self.price_list,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
									j.rate=doc1.price_list_rate

				if not doc:
					if not self.price_list:
						tab=frappe.db.get_value("Item Price",{"item_code":j.item_code,"buying":1,"valid_from":["<=",self.posting_date]},["name","valid_upto"],order_by='valid_from desc, batch_no desc, uom desc',as_dict=1)
						tab1=frappe.db.get_value("Item Price",{"item_code":j.item_code,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]},["name"],order_by='valid_from desc, batch_no desc, uom desc')
						if tab1 and tab.valid_upto:
							doc1=frappe.get_doc("Item Price",{"item_code":j.item_code,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
							j.rate=doc1.price_list_rate
							print(doc1)
						else:
							if tab:
								docname=frappe.get_doc("Item Price",tab.name)
								a="2150-12-31"
								date=datetime.strptime(a, "%Y-%m-%d")
								docname.valid_upto=date.date()
								docname.save()
								doc1=frappe.get_doc("Item Price",{"item_code":j.item_code,"buying":1,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
								j.rate=doc1.price_list_rate
					if self.price_list:
						tab=frappe.db.get_value("Item Price",{"item_code":j.item_code,"price_list":self.price_list,"valid_from":["<=",self.posting_date]},["name","valid_upto"],order_by='valid_from desc, batch_no desc, uom desc',as_dict=1)
						tab1=frappe.db.get_value("Item Price",{"item_code":j.item_code,"price_list":self.price_list,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]},["name"],order_by='valid_from desc, batch_no desc, uom desc')
						if tab1 and tab.valid_upto:
							doc1=frappe.get_doc("Item Price",{"item_code":j.item_code,"price_list":self.price_list,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
							j.rate=doc1.price_list_rate
						else:
							if tab:
								docname=frappe.get_doc("Item Price",tab.name)
								a="2150-12-31"
								date=datetime.strptime(a, "%Y-%m-%d")
								docname.valid_upto=date.date()
								docname.save()
								doc1=frappe.get_doc("Item Price",{"item_code":j.item_code,"price_list":self.price_list,"valid_from":["<=",self.posting_date],"valid_upto":[">=",self.posting_date]})
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
			except:
				print("")
		return True

	@frappe.whitelist()
	def set_value(self):
		d="{"+str(self.item_attribute)+"}"
		c=eval(d)
		if self.bom_item_attribute_set_to_raw_material_scrap:
			for i in self.raw_material_items:
				doc=frappe.get_doc("Item",i.item_code)
				a=""
				for k in doc.attributes:
					for j in c:
						if k.attribute==j:
							a+="'"+j+"'"+":"+"'"+c[j]+"'"+","+"\n"
				i.item_attributes=a

			for i in self.scrap_items:
				doc=frappe.get_doc("Item",i.item_code)
				a=""
				for k in doc.attributes:
					for j in c:
						if k.attribute==j:
							a+="'"+j+"'"+":"+"'"+c[j]+"'"+","+"\n"
				i.item_attributes=a
		
		return True
			