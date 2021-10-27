# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals

import frappe
from frappe.utils import cint, cstr, nowdate

from erpnext.setup.doctype.item_group.item_group import get_item_for_list_in_html

no_cache = 1

def get_context(context):
	context.show_search = True

@frappe.whitelist(allow_guest=True)
def get_product_list(search=None, start=0, limit=12):
	data = get_product_data(search, start, limit)

	for item in data:
		set_product_info_for_website(item)

	return [get_item_for_list_in_html(r) for r in data]

def get_product_data(search=None, start=0, limit=12):
	# limit = 12 because we show 12 items in the grid view
	# base query
	query = """
		SELECT
			web_item_name, item_name, item_code, brand, route,
			website_image, thumbnail, item_group,
			description, web_long_description as website_description,
			website_warehouse, ranking
		FROM `tabWebsite Item`
		WHERE published = 1
		"""

	# search term condition
	if search:
		query += """ and (item_name like %(search)s
				or web_item_name like %(search)s
				or brand like %(search)s
				or web_long_description like %(search)s)"""
		search = "%" + cstr(search) + "%"

	# order by
	query += """ ORDER BY ranking desc, modified desc limit %s, %s""" % (cint(start), cint(limit))

	return frappe.db.sql(query, {
		"search": search
	}, as_dict=1)

@frappe.whitelist(allow_guest=True)
def search(query):
	product_results = product_search(query)
	category_results = get_category_suggestions(query)

	return [get_item_for_list_in_html(r) for r in data]
