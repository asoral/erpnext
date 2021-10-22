# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ContainerSettings(Document):
	@frappe.whitelist()
	def account_query(self):
		accounts = frappe.db.sql("""
			SELECT name
			FROM `tabAccount`
			WHERE `tabAccount`.docstatus!=2
				AND account_type in ('Tax', 'Chargeable', 'Income Account', 'Expenses Included In Valuation')
				AND is_group = 0
				AND company = '{0}'
				""".format(self.company),as_dict=1)
		a=[]
		for i in accounts:
			a.append(i.get("name"))
		print(a)
		return a



	
		

