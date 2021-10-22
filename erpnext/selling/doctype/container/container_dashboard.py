from __future__ import unicode_literals

from frappe import _


def get_data():
	return {
		'fieldname': 'container',
        'transactions': [
			{
				'label': _('Delivery Note'),
				'items': ['Delivery Note']
			},
			{
				'label': _('Purchase Receipt'),
				'items': ['Purchase Receipt']
			},
			{
				'label': _('Landed Cost Voucher'),
				'items': ['Landed Cost Voucher']
			},
        ]
    }