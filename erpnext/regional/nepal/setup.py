import os
import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.permissions import add_permission, update_permission_property



def setup(company=None, patch=True):
    add_custom_roles_for_reports()
    
def add_custom_roles_for_reports():
	"""Add Access Control to Month wise Purchase VAT Register."""
	if not frappe.db.get_value('Custom Role', dict(report='Month wise Purchase VAT Register')):
		frappe.get_doc(dict(
			doctype='Custom Role',
			report='Month wise Purchase VAT Register',
			roles= [
					dict(role='Accounts User'),
					dict(role='Accounts Manager')
				]
		)).insert()
        
def add_permissions():
	for doctype in ('VAT RETURN'):
		add_permission(doctype, 'All', 0)
		for role in ('Accounts Manager', 'Accounts User', 'System Manager'):
			add_permission(doctype, role, 0)
			update_permission_property(doctype, role, 0, 'write', 1)
			update_permission_property(doctype, role, 0, 'create', 1)
