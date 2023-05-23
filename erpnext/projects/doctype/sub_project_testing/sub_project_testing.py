# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
import frappe

@frappe.whitelist()
def sub_project(project):
	proj_name = project
	filters = {'name': proj_name}
	fields = ("`tabSub Project`.sub_project")
	return frappe.get_all("Project", filters=filters,fields=fields)

@frappe.whitelist()
def sub_project_s_date(sub_project):
	sub_proj_name = sub_project
	filters = {'name': proj_name}
	fields = ("`tabSub Project`.sub_project")
	return frappe.get_all("Project", filters=filters,fields=fields)
