# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CaneSurvey(Document):
	def before_save(self):
		loc = frappe.db.get_value('Cane Survey','US-CS0007','cfl')
		print("*******************",loc)
		