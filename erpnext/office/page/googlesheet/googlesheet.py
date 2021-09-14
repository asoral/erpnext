import frappe
import json
import math
# from frappe.utils import getdate
def get_context(context):
    context.items = frappe.get_list("Quotation", filters={'show_in_website': 1}, fields=["name", "sheet_id"])
    #context.warehouse = order_warehouse()
