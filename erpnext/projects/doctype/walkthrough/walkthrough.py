# Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Walkthrough(Document):
	# pass
	def before_save(self):
		doc=frappe.get_doc("Project",{"name":self.project})
		for i in doc.site_details:
			doc.append("site_walkthrough",{
				"site_name":i.full_name,
				"walkthrough_id":self.name,
				"walkthrough_name":self.room_name
			})
			doc.save(ignore_permissions=True)	
