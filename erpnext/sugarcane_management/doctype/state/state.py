# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class State(Document):
	@frappe.whitelist()
	def set_state(self):
		doc = frappe.db.sql("""
							SELECT state 
							FROM `tabState`
							WHERE 'country'= '%s' 
							""".format(self.country),as_dict=1)
		print(doc)
		return doc
		

