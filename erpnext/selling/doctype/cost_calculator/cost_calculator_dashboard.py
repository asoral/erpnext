from __future__ import unicode_literals
from frappe import _

def get_data():
	return {
		'fieldname': 'cost_calculator',
		'transactions': [
			{
				'label': _('Quuotation'),
				'items': ['Quotation']
			},
			{
				'label': _('Item'),
				'items': ['Item']
			},
			{
				'label': _('Item'),
				'items': ['BOM']
			}
		]
	}