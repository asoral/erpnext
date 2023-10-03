# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _, throw
from frappe.desk.notifications import clear_doctype_notifications
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cint, flt, getdate, nowdate
from six import iteritems

import erpnext
from erpnext.accounts.utils import get_account_currency
from erpnext.assets.doctype.asset.asset import get_asset_account, is_cwip_accounting_enabled
from erpnext.assets.doctype.asset_category.asset_category import get_asset_category_account
from erpnext.buying.utils import check_on_hold_or_closed_status
from erpnext.controllers.buying_controller import BuyingController
from erpnext.stock.doctype.delivery_note.delivery_note import make_inter_company_transaction

form_grid_templates = {"items": "templates/form_grid/item_grid.html"}


class PurchaseReceipt(BuyingController):
	def before_submit(self):
		if self.is_subcontracted == "Yes":
			if len(self.supplied_items)< 0:
				frappe.throw("Supplied Items Table Mandatory For Subcontracted Item Entry")
			d=frappe.db.sql("""select item_code,sum(qty) ,sum(amount) from `tabPurchase Receipt Item` where parent='{0}' group by item_code """.format(self.name),as_dict=1)
			val1=[]
			amount=[]
			k=frappe.db.sql("""select main_item_code,sum(amount) from `tabPurchase Receipt Item Supplied` where parent='{0}' group by main_item_code """.format(self.name),as_dict=1)

			for i in d:
				for o in k:
					for j in self.items:
						if i.get("item_code") == j.item_code and o.get("main_item_code") == j.item_code:
							j.valuation_rate=o.get("sum(amount)")/flt(i.get("sum(qty)"))

	@frappe.whitelist()
	def get_items(self):
		if self.is_subcontracted == "Yes":
			self.supplied_items=[]
			xy=get_data(self.name,self.company)
			print("xy******************************************************",xy)
			for i in xy:
				item=frappe.db.get_value("Item",{"intercompany_item":i.get("item_code")},["name"])
				item_doc=frappe.get_doc("Item",item)
				if i.get("original_challan_number_issued_by_principal"):
					se=frappe.get_doc("Stock Entry",i.get("original_challan_number_issued_by_principal"))
					for k in se.items:
						if item==k.item_code:
							self.append("supplied_items",
								{
									"main_item_code":i.get("production_item"),
									"rm_item_code":item,
									"item_name":item_doc.item_name,
									"batch_no":k.batch_no,
									"required_qty":i.get("quantity"),
									"qty_to_be_consumed":i.get("quantity"),
									"rate":k.basic_rate,
									"amount": flt(i.get("quantity"))* flt(k.basic_rate),
									"reference_challan":i.get("original_challan_number_issued_by_principal")

								}
							)
						
				else:
					
					self.append("supplied_items",
						{
							"main_item_code":i.get("production_item"),
							"rm_item_code":item,
							"item_name":item_doc.item_name,
							"required_qty":i.get("quantity"),
							"qty_to_be_consumed":i.get("quantity"),
							"rate":i.get("rate"),
							"amount": flt(i.get("quantity"))* flt(i.get("rate")),
							"reference_challan":i.get("original_challan_number_issued_by_principal")

						}
					)
			self.save(ignore_permissions=True)
		return True
		# for row in self.supplied_items:
		# 	if row.qty_to_be_consumed:
		# 		if row.consumed_qty > 0 and row.qty_to_be_consumed <= 0 and self.is_new():
		# 			row.qty_to_be_consumed = row.consumed_qty
		# 	elif not row.qty_to_be_consumed and self.is_new():
		# 		if row.consumed_qty > 0:
		# 			row.qty_to_be_consumed = row.consumed_qty
		# 	if row.qty_to_be_consumed:
		# 		if row.consumed_qty != row.qty_to_be_consumed and row.loss_qty != 0:
		# 			row.consumed_qty = row.qty_to_be_consumed + row.loss_qty

	# New Code for Kroslink TASK TASK-2022-00015, Field challan_number_issues_by_job_worker
	data2 = []
	@frappe.whitelist()
	def on_get_items_button(self, po):
		ref_challan = ""
		ref_date = ""
		# s_company = frappe.db.get_value("Supplier", self.supplier, )
		# print(" this is on get items click", frappe.get_doc("Purchase Receipt", "MAT-PRE-2022-00022-1").get_signature())
		count = 0
		# 1st get item_code , challan_number_issues_by_job_worker (name of soi) 
		pr_items = frappe.db.get_all("Purchase Receipt Item", {"parent": self.name}, ['item_code', 'challan_number_issues_by_job_worker', 'challan_date_issues_by_job_worker', 'nature_of_job_work_done', 'purchase_order','idx', 'received_qty'])
		# print("1 LIST OF PR ITEMS", pr_items)
		for i in self.items:
			main_item = i.get("item_code")
			main_item_challan = i.get("challan_number_issues_by_job_worker")
			main_item_cdate = i.get("challan_date_issues_by_job_worker"),
			main_item_nature = i.get("nature_of_job_work_done")
			# print(" main ITEMS", i.get("item_code"), main_item_challan, main_item_cdate, main_item_nature)
			
			# Getting Batch no from SOIorder
			if i.challan_number_issues_by_job_worker:
				soi_item = frappe.db.get_value("Sales Invoice Item", i.challan_number_issues_by_job_worker, ['item_code', 'batch_no', 'sales_order'], as_dict= 1)
				# 3rd From Sales invoice to Sales Order and Sales Order to Work Order
				# print("soi_item.get(batch_no) ",soi_item.get("batch_no"))
				
				st_entry = frappe.db.sql("""
											Select se.name from `tabStock Entry Detail` sed
											Join `tabStock Entry` se ON se.name = sed.parent
											where sed.batch_no = "{0}"
											and se.stock_entry_type = "Manufacture"
										""".format(soi_item.get("batch_no")), as_dict=1)


				# print("st entry", st_entry)
				if st_entry:
					se_bom = frappe.get_doc("Stock Entry", st_entry[0].get("name"))

					# print(" thid id filters : - ", se_bom.get("to_warehouse"), se_bom.get("bom_no"), se_bom.get("work_order"))
					se_01 = frappe.get_value("Stock Entry", { "work_order": se_bom.get("work_order"), "stock_entry_type" : "Material Transfer for Manufacture" }, ["to_warehouse"])

					stock_filter = { 'bom':se_bom.get("bom_no"), 
								'qty_to_produce': i.get("qty"),
								'show_exploded_view' :1,
								'warehouse': se_01 }
				# level_up_se('WOKPPL2203-0106-01', self.data2)
					# print(" stick filter", stock_filter)
					# bom_stock = get_bom_stock(stock_filter)

					# print(" this is bom", bom_stock)	

					level_up_se(soi_item.get("batch_no"), data2)			
					# print("level_ip called", self.data2)

					new_list = []
					for s in data2:
						# for j in bom_stock:
							# print(" s j", s , j)
							if frappe.db.get_value("Item", s.get('item_code'), ["intercompany_item"]):
								# new_list.append({"main_item_code" : main_item,	
								# 				"rm_item_code" : frappe.db.get_value("Item", s.get("item_code"), ["intercompany_item"]) if frappe.db.get_value("Item", s.get("item_code"), ["intercompany_item"]) else s.get('item_code'),
								# 				"stock_uom" : s.get('stock_uom'),
								# 				"required_qty" : j.get('req_qty'),
								# 				"qty_to_be_consumed" : j.get('req_qty'),
								# 				"rate" : s.get('basic_rate'),
								# 				"amount" : s.get('amount'),
								# 				"item_name" :  frappe.db.get_value("Item", 
								# 				s.get('item_code'), ["intercompany_item_name"]) if frappe.db.get_value("Item", s.get('item_code'), 
								# 				["intercompany_item_name"]) else s.get('item_name'),
								# 				"description" : s.get('description'),
								# 				"batch_no" : frappe.get_value("Batch", s.get('batch_no'), 'original_batch_no'),
								# 				"consumed_qty" : j.get('req_qty')			
								# })
								new_list.append({
									"main_item_code" : main_item,
									"rm_item_code" : frappe.db.get_value("Item", s.get("item_code"), ["intercompany_item"]) if frappe.db.get_value("Item", s.get("item_code"), ["intercompany_item"]) else s.get('item_code'),
									"batch_no" : s.get('batch_no')
								})

					# print(" new list", new_list)

					res_list = [i for n, i in enumerate(new_list) if i not in new_list[n + 1:]]
					# print(" mnew set , ", res_list)

					for r in res_list:
						r_batch =  r.get('batch_no') 
						# r_batch = frappe.get_value("Batch", { 'original_batch_no': 'TANKER/P1735/21-22'}, ['name'])
						
						# print(" r_batch no", r_batch)
						
						# print(" ref dare", ref_date, ref_challan)
						if r_batch :
							stock_e = frappe.db.sql("""
													Select se.reference_challan, se.posting_date from `tabStock Entry` se 
													join `tabStock Entry Detail` sed on sed.parent = se.name 
													where se.stock_entry_type = "Material Receipt"
													and sed.batch_no = '{0}'
													""".format(r_batch), as_dict=1)
							# print("stock EEE", stock_e[0].get('reference_challan'), stock_e[0].get('posting_date'))	
							if stock_e:
								# print("this is reference challan Number and date ", stock_e)
								for item in self.supplied_items:
									# print(" this is Supplied Item ", item)
									# frappe.db.set_value("")
									frappe.db.set_value('Purchase Receipt Item Supplied', item.name, 'reference_challan', stock_e[0].reference_challan, update_modified=False)
								
								self.reload()
								return stock_e 
		
		
	@frappe.whitelist()
	def on_challan_date(self, item):
		# print("THi i new deu daye")
		due_date = frappe.db.sql("""
								Select si.posting_date, soi.new_name from `tabSales Invoice Item` soi , `tabSales Invoice` si
								Where soi.parent = si.name and soi.name = '{0}'	""".format(item), as_dict = 1)

		return due_date

	@frappe.whitelist()
	def on_challan_number_save(self):
		for i in self.items:
			pr_item = frappe.db.sql("""
									Select name, parent from `tabPurchase Receipt Item` where 
									challan_number_issues_by_job_worker = "{0}"
									and docstatus = 1
								""".format(i.challan_number_issues_by_job_worker), as_dict =1)

			if pr_item:
				frappe.throw(" Purchase Receipt {1} already created with Challan Number {0}".format(i.challan_number_issues_by_job_worker, pr_item[0].get("parent")))				
			

	# New Code for Kroslink TASK TASK-2022-00015, Field challan_number_issues_by_job_worker
	@frappe.whitelist()
	def on_challan_number(self, item_code):
		# print("this is Inside on_challan_number")
		new_company = frappe.get_value("Supplier", self.supplier, 'represents_company')

		new_code = (frappe.get_value("Item", item_code, "intercompany_item") or item_code)

		# print(" new cm , new code", new_company, new_code)
		soi = frappe.db.sql("""
			select soi.name, si.name as si_name from `tabSales Invoice Item` soi , `tabSales Invoice` si
				Where soi.parent = si.name
				AND si.docstatus = 1
				AND soi.item_code = "{0}" OR soi.item_code = "{3}"
				AND si.company = "{1}"
				AND si.represents_company = "{2}"
		""".format(new_code, new_company, self.company, item_code), as_dict = 1)
		
		new_soi = []
		for s in soi:
			pr_item = frappe.db.sql("""
									Select name from `tabPurchase Receipt Item` where 
									challan_number_issues_by_job_worker = "{0}"
									and docstatus = 1
								""".format( s.get("name")))
			
			if pr_item:
				print(" this is pr item", pr_item)	
			else: 				
				new_soi.append(s["name"])

		new_list = list(set(new_soi))		
		
		
		return set(new_list)

	def __init__(self, *args, **kwargs):
		super(PurchaseReceipt, self).__init__(*args, **kwargs)
		self.status_updater = [
			{
				"target_dt": "Purchase Order Item",
				"join_field": "purchase_order_item",
				"target_field": "received_qty",
				"target_parent_dt": "Purchase Order",
				"target_parent_field": "per_received",
				"target_ref_field": "qty",
				"source_dt": "Purchase Receipt Item",
				"source_field": "received_qty",
				"second_source_dt": "Purchase Invoice Item",
				"second_source_field": "received_qty",
				"second_join_field": "po_detail",
				"percent_join_field": "purchase_order",
				"overflow_type": "receipt",
				"second_source_extra_cond": """ and exists(select name from `tabPurchase Invoice`
				where name=`tabPurchase Invoice Item`.parent and update_stock = 1)""",
			},
			{
				"source_dt": "Purchase Receipt Item",
				"target_dt": "Material Request Item",
				"join_field": "material_request_item",
				"target_field": "received_qty",
				"target_parent_dt": "Material Request",
				"target_parent_field": "per_received",
				"target_ref_field": "stock_qty",
				"source_field": "stock_qty",
				"percent_join_field": "material_request",
			},
			{
				"source_dt": "Purchase Receipt Item",
				"target_dt": "Purchase Invoice Item",
				"join_field": "purchase_invoice_item",
				"target_field": "received_qty",
				"target_parent_dt": "Purchase Invoice",
				"target_parent_field": "per_received",
				"target_ref_field": "qty",
				"source_field": "received_qty",
				"percent_join_field": "purchase_invoice",
				"overflow_type": "receipt",
			},
		]

		if cint(self.is_return):
			self.status_updater.extend(
				[
					{
						"source_dt": "Purchase Receipt Item",
						"target_dt": "Purchase Order Item",
						"join_field": "purchase_order_item",
						"target_field": "returned_qty",
						"source_field": "-1 * qty",
						"second_source_dt": "Purchase Invoice Item",
						"second_source_field": "-1 * qty",
						"second_join_field": "po_detail",
						"extra_cond": """ and exists (select name from `tabPurchase Receipt`
						where name=`tabPurchase Receipt Item`.parent and is_return=1)""",
						"second_source_extra_cond": """ and exists (select name from `tabPurchase Invoice`
						where name=`tabPurchase Invoice Item`.parent and is_return=1 and update_stock=1)""",
					},
					{
						"source_dt": "Purchase Receipt Item",
						"target_dt": "Purchase Receipt Item",
						"join_field": "purchase_receipt_item",
						"target_field": "returned_qty",
						"target_parent_dt": "Purchase Receipt",
						"target_parent_field": "per_returned",
						"target_ref_field": "received_stock_qty",
						"source_field": "-1 * received_stock_qty",
						"percent_join_field_parent": "return_against",
					},
				]
			)

	def before_validate(self):
		from erpnext.stock.doctype.putaway_rule.putaway_rule import apply_putaway_rule

		if self.get("items") and self.apply_putaway_rule and not self.get("is_return"):
			apply_putaway_rule(self.doctype, self.get("items"), self.company)


	def before_save(self):	
		if len(self.supplied_items)>0:
			for i in self.supplied_items:
				i.amount=flt(i.qty_to_be_consumed)* flt(i.rate)
	def validate(self):
		# self.on_challan_number_save()
		self.validate_posting_time()
		super(PurchaseReceipt, self).validate()

		if self._action == "submit":
			self.make_batches("warehouse")
		else:
			self.set_status()

		if self._action == "save":
			pass
		self.po_required()
		# self.validate_items_quality_inspection()
		self.validate_with_previous_doc()
		self.validate_uom_is_integer("uom", ["qty", "received_qty"])
		self.validate_uom_is_integer("stock_uom", "stock_qty")
		self.validate_cwip_accounts()
		self.validate_provisional_expense_account()

		self.check_on_hold_or_closed_status()

		if getdate(self.posting_date) > getdate(nowdate()):
			throw(_("Posting Date cannot be future date"))

		self.reset_default_field_value("set_warehouse", "items", "warehouse")
		self.reset_default_field_value("rejected_warehouse", "items", "rejected_warehouse")
		self.reset_default_field_value("set_from_warehouse", "items", "from_warehouse")
		if self.is_subcontracted == "Yes":
			for i in self.items:
				if not i.challan_number_issues_by_job_worker:
					frappe.throw("challan_number_issues_by_job_worker not set in Row:{0} ".format(i.idx))				

		# self.validate_challan_number_issue_by_job_worker()

	def validate_challan_number_issue_by_job_worker(self):
		for row in self.items:
			# print("row.nature_of_job_work_done -------------",row.nature_of_job_work_done )
			str_nature = row.nature_of_job_work_done
			# if row.is_subcontracted == "Yes" and not row.challan_number_issues_by_job_worker and not row.challan_date_issues_by_job_worker and not str_nature:
			# 		frappe.throw("Challan Number Issues by Job Worker, Challan Date Issues by Job Worker"
			# 					 "and Nature of Job Work Done Is Mandatory at row "+str(row.idx))

	def validate_cwip_accounts(self):
		for item in self.get("items"):
			if item.is_fixed_asset and is_cwip_accounting_enabled(item.asset_category):
				# check cwip accounts before making auto assets
				# Improves UX by not giving messages of "Assets Created" before throwing error of not finding arbnb account
				arbnb_account = self.get_company_default("asset_received_but_not_billed")
				cwip_account = get_asset_account(
					"capital_work_in_progress_account", asset_category=item.asset_category, company=self.company
				)
				break

	def validate_provisional_expense_account(self):
		provisional_accounting_for_non_stock_items = cint(
			frappe.db.get_value(
				"Company", self.company, "enable_provisional_accounting_for_non_stock_items"
			)
		)

		if not provisional_accounting_for_non_stock_items:
			return

		default_provisional_account = self.get_company_default("default_provisional_account")
		for item in self.get("items"):
			if not item.get("provisional_expense_account"):
				item.provisional_expense_account = default_provisional_account

	def validate_with_previous_doc(self):
		super(PurchaseReceipt, self).validate_with_previous_doc(
			{
				"Purchase Order": {
					"ref_dn_field": "purchase_order",
					"compare_fields": [["supplier", "="], ["company", "="], ["currency", "="]],
				},
				"Purchase Order Item": {
					"ref_dn_field": "purchase_order_item",
					"compare_fields": [["project", "="], ["uom", "="], ["item_code", "="]],
					"is_child_table": True,
					"allow_duplicate_prev_row_id": True,
				},
			}
		)

		if (
			cint(frappe.db.get_single_value("Buying Settings", "maintain_same_rate")) and not self.is_return
		):
			self.validate_rate_with_reference_doc(
				[["Purchase Order", "purchase_order", "purchase_order_item"]]
			)

	def po_required(self):
		if frappe.db.get_value("Buying Settings", None, "po_required") == "Yes":
			for d in self.get("items"):
				if not d.purchase_order:
					frappe.throw(_("Purchase Order number required for Item {0}").format(d.item_code))

	def validate_items_quality_inspection(self):
		for item in self.get("items"):
			if item.quality_inspection:
				qi = frappe.db.get_value(
					"Quality Inspection",
					item.quality_inspection,
					["reference_type", "reference_name", "item_code"],
					as_dict=True,
				)

				if qi.reference_type != self.doctype or qi.reference_name != self.name:
					msg = f"""Row #{item.idx}: Please select a valid Quality Inspection with Reference Type
						{frappe.bold(self.doctype)} and Reference Name {frappe.bold(self.name)}."""
					frappe.throw(_(msg))

				if qi.item_code != item.item_code:
					msg = f"""Row #{item.idx}: Please select a valid Quality Inspection with Item Code
						{frappe.bold(item.item_code)}."""
					frappe.throw(_(msg))

	def get_already_received_qty(self, po, po_detail):
		qty = frappe.db.sql(
			"""select sum(qty) from `tabPurchase Receipt Item`
			where purchase_order_item = %s and docstatus = 1
			and purchase_order=%s
			and parent != %s""",
			(po_detail, po, self.name),
		)
		return qty and flt(qty[0][0]) or 0.0

	def get_po_qty_and_warehouse(self, po_detail):
		po_qty, po_warehouse = frappe.db.get_value(
			"Purchase Order Item", po_detail, ["qty", "warehouse"]
		)
		return po_qty, po_warehouse

	# Check for Closed status
	def check_on_hold_or_closed_status(self):
		check_list = []
		for d in self.get("items"):
			if (
				d.meta.get_field("purchase_order") and d.purchase_order and d.purchase_order not in check_list
			):
				check_list.append(d.purchase_order)
				check_on_hold_or_closed_status("Purchase Order", d.purchase_order)

	# on submit
	def on_submit(self):
		super(PurchaseReceipt, self).on_submit()

		# Check for Approving Authority
		frappe.get_doc("Authorization Control").validate_approving_authority(
			self.doctype, self.company, self.base_grand_total
		)

		self.update_prevdoc_status()
		if flt(self.per_billed) < 100:
			self.update_billing_status()
		else:
			self.db_set("status", "Completed")

		# Updating stock ledger should always be called after updating prevdoc status,
		# because updating ordered qty, reserved_qty_for_subcontract in bin
		# depends upon updated ordered qty in PO
		self.update_stock_ledger()

		from erpnext.stock.doctype.serial_no.serial_no import update_serial_nos_after_submit

		update_serial_nos_after_submit(self, "items")

		self.make_gl_entries()
		self.repost_future_sle_and_gle()
		self.set_consumed_qty_in_po()
		
		if self.is_subcontracted == "Yes":
			doc=frappe.new_doc("Stock Entry")
			doc.stock_entry_type="Material Issue"
			doc.naming_series="JWR-.abbr.-.FY.-.####"
			doc.from_warehouse=self.supplier_warehouse
			doc.company=self.company
			doc.purchase_receipt=self.name
			for i in self.supplied_items:
				doc.append("items",{
					"s_warehouse":self.supplier_warehouse,
					"item_code":i.rm_item_code,
					"qty":i.required_qty,
					"basic_rate":i.rate,
					"batch_no":i.batch_no

				})
			doc.save(ignore_permissions=True)
			doc.submit()

	def check_next_docstatus(self):
		submit_rv = frappe.db.sql(
			"""select t1.name
			from `tabPurchase Invoice` t1,`tabPurchase Invoice Item` t2
			where t1.name = t2.parent and t2.purchase_receipt = %s and t1.docstatus = 1""",
			(self.name),
		)
		if submit_rv:
			frappe.throw(_("Purchase Invoice {0} is already submitted").format(self.submit_rv[0][0]))

	def on_cancel(self):
		super(PurchaseReceipt, self).on_cancel()

		self.check_on_hold_or_closed_status()
		# Check if Purchase Invoice has been submitted against current Purchase Order
		submitted = frappe.db.sql(
			"""select t1.name
			from `tabPurchase Invoice` t1,`tabPurchase Invoice Item` t2
			where t1.name = t2.parent and t2.purchase_receipt = %s and t1.docstatus = 1""",
			self.name,
		)
		if submitted:
			frappe.throw(_("Purchase Invoice {0} is already submitted").format(submitted[0][0]))

		self.update_prevdoc_status()
		self.update_billing_status()

		# Updating stock ledger should always be called after updating prevdoc status,
		# because updating ordered qty in bin depends upon updated ordered qty in PO
		self.update_stock_ledger()
		self.make_gl_entries_on_cancel()
		self.repost_future_sle_and_gle()
		self.ignore_linked_doctypes = ("GL Entry", "Stock Ledger Entry", "Repost Item Valuation")
		self.delete_auto_created_batches()
		self.set_consumed_qty_in_po()

	@frappe.whitelist()
	def get_current_stock(self):
		for d in self.get("supplied_items"):
			if self.supplier_warehouse:
				bin = frappe.db.sql(
					"select actual_qty from `tabBin` where item_code = %s and warehouse = %s",
					(d.rm_item_code, self.supplier_warehouse),
					as_dict=1,
				)
				d.current_stock = bin and flt(bin[0]["actual_qty"]) or 0

	def get_gl_entries(self, warehouse_account=None):
		from erpnext.accounts.general_ledger import process_gl_map

		gl_entries = []

		self.make_item_gl_entries(gl_entries, warehouse_account=warehouse_account)
		self.make_tax_gl_entries(gl_entries)
		self.get_asset_gl_entry(gl_entries)

		return process_gl_map(gl_entries)

	def make_item_gl_entries(self, gl_entries, warehouse_account=None):
		if erpnext.is_perpetual_inventory_enabled(self.company):
			stock_rbnb = self.get_company_default("stock_received_but_not_billed")
			landed_cost_entries = get_item_account_wise_additional_cost(self.name)
			expenses_included_in_valuation = self.get_company_default("expenses_included_in_valuation")

		warehouse_with_no_account = []
		stock_items = self.get_stock_items()
		provisional_accounting_for_non_stock_items = cint(
			frappe.db.get_value(
				"Company", self.company, "enable_provisional_accounting_for_non_stock_items"
			)
		)

		for d in self.get("items"):
			if d.item_code in stock_items and flt(d.valuation_rate) and flt(d.qty):
				if warehouse_account.get(d.warehouse):
					stock_value_diff = frappe.db.get_value(
						"Stock Ledger Entry",
						{
							"voucher_type": "Purchase Receipt",
							"voucher_no": self.name,
							"voucher_detail_no": d.name,
							"warehouse": d.warehouse,
							"is_cancelled": 0,
						},
						"stock_value_difference",
					)

					warehouse_account_name = warehouse_account[d.warehouse]["account"]
					warehouse_account_currency = warehouse_account[d.warehouse]["account_currency"]
					supplier_warehouse_account = warehouse_account.get(self.supplier_warehouse, {}).get("account")
					supplier_warehouse_account_currency = warehouse_account.get(self.supplier_warehouse, {}).get(
						"account_currency"
					)
					remarks = self.get("remarks") or _("Accounting Entry for Stock")

					# If PR is sub-contracted and fg item rate is zero
					# in that case if account for source and target warehouse are same,
					# then GL entries should not be posted
					if (
						flt(stock_value_diff) == flt(d.rm_supp_cost)
						and warehouse_account.get(self.supplier_warehouse)
						and warehouse_account_name == supplier_warehouse_account
					):
						continue

					self.add_gl_entry(
						gl_entries=gl_entries,
						account=warehouse_account_name,
						cost_center=d.cost_center,
						debit=stock_value_diff,
						credit=0.0,
						remarks=remarks,
						against_account=stock_rbnb,
						account_currency=warehouse_account_currency,
						item=d,
					)

					# GL Entry for from warehouse or Stock Received but not billed
					# Intentionally passed negative debit amount to avoid incorrect GL Entry validation
					credit_currency = (
						get_account_currency(warehouse_account[d.from_warehouse]["account"])
						if d.from_warehouse
						else get_account_currency(stock_rbnb)
					)

					credit_amount = (
						flt(d.base_net_amount, d.precision("base_net_amount"))
						if credit_currency == self.company_currency
						else flt(d.net_amount, d.precision("net_amount"))
					)

					outgoing_amount = d.base_net_amount
					if self.is_internal_transfer() and d.valuation_rate:
						outgoing_amount = abs(
							frappe.db.get_value(
								"Stock Ledger Entry",
								{
									"voucher_type": "Purchase Receipt",
									"voucher_no": self.name,
									"voucher_detail_no": d.name,
									"warehouse": d.from_warehouse,
									"is_cancelled": 0,
								},
								"stock_value_difference",
							)
						)
						credit_amount = outgoing_amount

					if credit_amount:
						account = warehouse_account[d.from_warehouse]["account"] if d.from_warehouse else stock_rbnb

						self.add_gl_entry(
							gl_entries=gl_entries,
							account=account,
							cost_center=d.cost_center,
							debit=-1 * flt(outgoing_amount, d.precision("base_net_amount")),
							credit=0.0,
							remarks=remarks,
							against_account=warehouse_account_name,
							debit_in_account_currency=-1 * credit_amount,
							account_currency=credit_currency,
							item=d,
						)

					# Amount added through landed-cos-voucher
					if d.landed_cost_voucher_amount and landed_cost_entries:
						for account, amount in iteritems(landed_cost_entries[(d.item_code, d.name)]):
							account_currency = get_account_currency(account)
							credit_amount = (
								flt(amount["base_amount"])
								if (amount["base_amount"] or account_currency != self.company_currency)
								else flt(amount["amount"])
							)

							self.add_gl_entry(
								gl_entries=gl_entries,
								account=account,
								cost_center=d.cost_center,
								debit=0.0,
								credit=credit_amount,
								remarks=remarks,
								against_account=warehouse_account_name,
								credit_in_account_currency=flt(amount["amount"]),
								account_currency=account_currency,
								project=d.project,
								item=d,
							)

					# sub-contracting warehouse
					if flt(d.rm_supp_cost) and warehouse_account.get(self.supplier_warehouse):
						self.add_gl_entry(
							gl_entries=gl_entries,
							account=supplier_warehouse_account,
							cost_center=d.cost_center,
							debit=0.0,
							credit=flt(d.rm_supp_cost),
							remarks=remarks,
							against_account=warehouse_account_name,
							account_currency=supplier_warehouse_account_currency,
							item=d,
						)

					# divisional loss adjustment
					valuation_amount_as_per_doc = (
						flt(outgoing_amount, d.precision("base_net_amount"))
						+ flt(d.landed_cost_voucher_amount)
						+ flt(d.rm_supp_cost)
						+ flt(d.item_tax_amount)
					)

					divisional_loss = flt(
						valuation_amount_as_per_doc - flt(stock_value_diff), d.precision("base_net_amount")
					)

					if divisional_loss:
						if self.is_return or flt(d.item_tax_amount):
							loss_account = expenses_included_in_valuation
						else:
							loss_account = (
								self.get_company_default("default_expense_account", ignore_validation=True) or stock_rbnb
							)

						cost_center = d.cost_center or frappe.get_cached_value(
							"Company", self.company, "cost_center"
						)

						self.add_gl_entry(
							gl_entries=gl_entries,
							account=loss_account,
							cost_center=cost_center,
							debit=divisional_loss,
							credit=0.0,
							remarks=remarks,
							against_account=warehouse_account_name,
							account_currency=credit_currency,
							project=d.project,
							item=d,
						)

				elif (
					d.warehouse not in warehouse_with_no_account
					or d.rejected_warehouse not in warehouse_with_no_account
				):
					warehouse_with_no_account.append(d.warehouse)
			elif (
				d.item_code not in stock_items
				and not d.is_fixed_asset
				and flt(d.qty)
				and provisional_accounting_for_non_stock_items
				and d.get("provisional_expense_account")
			):
				self.add_provisional_gl_entry(
					d, gl_entries, self.posting_date, d.get("provisional_expense_account")
				)

		if warehouse_with_no_account:
			frappe.msgprint(
				_("No accounting entries for the following warehouses")
				+ ": \n"
				+ "\n".join(warehouse_with_no_account)
			)

	def add_provisional_gl_entry(
		self, item, gl_entries, posting_date, provisional_account, reverse=0
	):
		credit_currency = get_account_currency(provisional_account)
		debit_currency = get_account_currency(item.expense_account)
		expense_account = item.expense_account
		remarks = self.get("remarks") or _("Accounting Entry for Service")
		multiplication_factor = 1

		if reverse:
			multiplication_factor = -1
			expense_account = frappe.db.get_value(
				"Purchase Receipt Item", {"name": item.get("pr_detail")}, ["expense_account"]
			)

		self.add_gl_entry(
			gl_entries=gl_entries,
			account=provisional_account,
			cost_center=item.cost_center,
			debit=0.0,
			credit=multiplication_factor * item.amount,
			remarks=remarks,
			against_account=expense_account,
			account_currency=credit_currency,
			project=item.project,
			voucher_detail_no=item.name,
			item=item,
			posting_date=posting_date,
		)

		self.add_gl_entry(
			gl_entries=gl_entries,
			account=expense_account,
			cost_center=item.cost_center,
			debit=multiplication_factor * item.amount,
			credit=0.0,
			remarks=remarks,
			against_account=provisional_account,
			account_currency=debit_currency,
			project=item.project,
			voucher_detail_no=item.name,
			item=item,
			posting_date=posting_date,
		)

	def make_tax_gl_entries(self, gl_entries):

		if erpnext.is_perpetual_inventory_enabled(self.company):
			expenses_included_in_valuation = self.get_company_default("expenses_included_in_valuation")

		negative_expense_to_be_booked = sum([flt(d.item_tax_amount) for d in self.get("items")])
		# Cost center-wise amount breakup for other charges included for valuation
		valuation_tax = {}
		for tax in self.get("taxes"):
			if tax.category in ("Valuation", "Valuation and Total") and flt(
				tax.base_tax_amount_after_discount_amount
			):
				if not tax.cost_center:
					frappe.throw(
						_("Cost Center is required in row {0} in Taxes table for type {1}").format(
							tax.idx, _(tax.category)
						)
					)
				valuation_tax.setdefault(tax.name, 0)
				valuation_tax[tax.name] += (tax.add_deduct_tax == "Add" and 1 or -1) * flt(
					tax.base_tax_amount_after_discount_amount
				)

		if negative_expense_to_be_booked and valuation_tax:
			# Backward compatibility:
			# If expenses_included_in_valuation account has been credited in against PI
			# and charges added via Landed Cost Voucher,
			# post valuation related charges on "Stock Received But Not Billed"
			# introduced in 2014 for backward compatibility of expenses already booked in expenses_included_in_valuation account

			negative_expense_booked_in_pi = frappe.db.sql(
				"""select name from `tabPurchase Invoice Item` pi
				where docstatus = 1 and purchase_receipt=%s
				and exists(select name from `tabGL Entry` where voucher_type='Purchase Invoice'
					and voucher_no=pi.parent and account=%s)""",
				(self.name, expenses_included_in_valuation),
			)

			against_account = ", ".join([d.account for d in gl_entries if flt(d.debit) > 0])
			total_valuation_amount = sum(valuation_tax.values())
			amount_including_divisional_loss = negative_expense_to_be_booked
			stock_rbnb = self.get_company_default("stock_received_but_not_billed")
			i = 1
			for tax in self.get("taxes"):
				if valuation_tax.get(tax.name):

					if negative_expense_booked_in_pi:
						account = stock_rbnb
					else:
						account = tax.account_head

					if i == len(valuation_tax):
						applicable_amount = amount_including_divisional_loss
					else:
						applicable_amount = negative_expense_to_be_booked * (
							valuation_tax[tax.name] / total_valuation_amount
						)
						amount_including_divisional_loss -= applicable_amount

					self.add_gl_entry(
						gl_entries=gl_entries,
						account=account,
						cost_center=tax.cost_center,
						debit=0.0,
						credit=applicable_amount,
						remarks=self.remarks or _("Accounting Entry for Stock"),
						against_account=against_account,
						item=tax,
					)

					i += 1

	def add_gl_entry(
		self,
		gl_entries,
		account,
		cost_center,
		debit,
		credit,
		remarks,
		against_account,
		debit_in_account_currency=None,
		credit_in_account_currency=None,
		account_currency=None,
		project=None,
		voucher_detail_no=None,
		item=None,
		posting_date=None,
	):

		gl_entry = {
			"account": account,
			"cost_center": cost_center,
			"debit": debit,
			"credit": credit,
			"against": against_account,
			"remarks": remarks,
		}

		if voucher_detail_no:
			gl_entry.update({"voucher_detail_no": voucher_detail_no})

		if debit_in_account_currency:
			gl_entry.update({"debit_in_account_currency": debit_in_account_currency})

		if credit_in_account_currency:
			gl_entry.update({"credit_in_account_currency": credit_in_account_currency})

		if posting_date:
			gl_entry.update({"posting_date": posting_date})

		gl_entries.append(self.get_gl_dict(gl_entry, item=item))

	def get_asset_gl_entry(self, gl_entries):
		for item in self.get("items"):
			if item.is_fixed_asset:
				if is_cwip_accounting_enabled(item.asset_category):
					self.add_asset_gl_entries(item, gl_entries)
				if flt(item.landed_cost_voucher_amount):
					self.add_lcv_gl_entries(item, gl_entries)
					# update assets gross amount by its valuation rate
					# valuation rate is total of net rate, raw mat supp cost, tax amount, lcv amount per item
					self.update_assets(item, item.valuation_rate)
		return gl_entries

	def add_asset_gl_entries(self, item, gl_entries):
		arbnb_account = self.get_company_default("asset_received_but_not_billed")
		# This returns category's cwip account if not then fallback to company's default cwip account
		cwip_account = get_asset_account(
			"capital_work_in_progress_account", asset_category=item.asset_category, company=self.company
		)

		asset_amount = flt(item.net_amount) + flt(item.item_tax_amount / self.conversion_rate)
		base_asset_amount = flt(item.base_net_amount + item.item_tax_amount)
		remarks = self.get("remarks") or _("Accounting Entry for Asset")

		cwip_account_currency = get_account_currency(cwip_account)
		# debit cwip account
		debit_in_account_currency = (
			base_asset_amount if cwip_account_currency == self.company_currency else asset_amount
		)

		self.add_gl_entry(
			gl_entries=gl_entries,
			account=cwip_account,
			cost_center=item.cost_center,
			debit=base_asset_amount,
			credit=0.0,
			remarks=remarks,
			against_account=arbnb_account,
			debit_in_account_currency=debit_in_account_currency,
			item=item,
		)

		asset_rbnb_currency = get_account_currency(arbnb_account)
		# credit arbnb account
		credit_in_account_currency = (
			base_asset_amount if asset_rbnb_currency == self.company_currency else asset_amount
		)

		self.add_gl_entry(
			gl_entries=gl_entries,
			account=arbnb_account,
			cost_center=item.cost_center,
			debit=0.0,
			credit=base_asset_amount,
			remarks=remarks,
			against_account=cwip_account,
			credit_in_account_currency=credit_in_account_currency,
			item=item,
		)

	def add_lcv_gl_entries(self, item, gl_entries):
		expenses_included_in_asset_valuation = self.get_company_default(
			"expenses_included_in_asset_valuation"
		)
		if not is_cwip_accounting_enabled(item.asset_category):
			asset_account = get_asset_category_account(
				asset_category=item.asset_category, fieldname="fixed_asset_account", company=self.company
			)
		else:
			# This returns company's default cwip account
			asset_account = get_asset_account("capital_work_in_progress_account", company=self.company)

		remarks = self.get("remarks") or _("Accounting Entry for Stock")

		self.add_gl_entry(
			gl_entries=gl_entries,
			account=expenses_included_in_asset_valuation,
			cost_center=item.cost_center,
			debit=0.0,
			credit=flt(item.landed_cost_voucher_amount),
			remarks=remarks,
			against_account=asset_account,
			project=item.project,
			item=item,
		)

		self.add_gl_entry(
			gl_entries=gl_entries,
			account=asset_account,
			cost_center=item.cost_center,
			debit=flt(item.landed_cost_voucher_amount),
			credit=0.0,
			remarks=remarks,
			against_account=expenses_included_in_asset_valuation,
			project=item.project,
			item=item,
		)

	def update_assets(self, item, valuation_rate):
		assets = frappe.db.get_all(
			"Asset", filters={"purchase_receipt": self.name, "item_code": item.item_code}
		)

		for asset in assets:
			frappe.db.set_value("Asset", asset.name, "gross_purchase_amount", flt(valuation_rate))
			frappe.db.set_value("Asset", asset.name, "purchase_receipt_amount", flt(valuation_rate))

	def update_status(self, status):
		self.set_status(update=True, status=status)
		self.notify_update()
		clear_doctype_notifications(self)

	def update_billing_status(self, update_modified=True):
		updated_pr = [self.name]
		for d in self.get("items"):
			if d.get("purchase_invoice") and d.get("purchase_invoice_item"):
				d.db_set("billed_amt", d.amount, update_modified=update_modified)
			elif d.purchase_order_item:
				updated_pr += update_billed_amount_based_on_po(d.purchase_order_item, update_modified)

		for pr in set(updated_pr):
			pr_doc = self if (pr == self.name) else frappe.get_doc("Purchase Receipt", pr)
			update_billing_percentage(pr_doc, update_modified=update_modified)

		self.load_from_db()


def update_billed_amount_based_on_po(po_detail, update_modified=True):
	# Billed against Sales Order directly
	billed_against_po = frappe.db.sql(
		"""select sum(amount) from `tabPurchase Invoice Item`
		where po_detail=%s and (pr_detail is null or pr_detail = '') and docstatus=1""",
		po_detail,
	)
	billed_against_po = billed_against_po and billed_against_po[0][0] or 0

	# Get all Purchase Receipt Item rows against the Purchase Order Item row
	pr_details = frappe.db.sql(
		"""select pr_item.name, pr_item.amount, pr_item.parent
		from `tabPurchase Receipt Item` pr_item, `tabPurchase Receipt` pr
		where pr.name=pr_item.parent and pr_item.purchase_order_item=%s
			and pr.docstatus=1 and pr.is_return = 0
		order by pr.posting_date asc, pr.posting_time asc, pr.name asc""",
		po_detail,
		as_dict=1,
	)

	updated_pr = []
	for pr_item in pr_details:
		# Get billed amount directly against Purchase Receipt
		billed_amt_agianst_pr = frappe.db.sql(
			"""select sum(amount) from `tabPurchase Invoice Item`
			where pr_detail=%s and docstatus=1""",
			pr_item.name,
		)
		billed_amt_agianst_pr = billed_amt_agianst_pr and billed_amt_agianst_pr[0][0] or 0

		# Distribute billed amount directly against PO between PRs based on FIFO
		if billed_against_po and billed_amt_agianst_pr < pr_item.amount:
			pending_to_bill = flt(pr_item.amount) - billed_amt_agianst_pr
			if pending_to_bill <= billed_against_po:
				billed_amt_agianst_pr += pending_to_bill
				billed_against_po -= pending_to_bill
			else:
				billed_amt_agianst_pr += billed_against_po
				billed_against_po = 0

		frappe.db.set_value(
			"Purchase Receipt Item",
			pr_item.name,
			"billed_amt",
			billed_amt_agianst_pr,
			update_modified=update_modified,
		)

		updated_pr.append(pr_item.parent)

	return updated_pr


def update_billing_percentage(pr_doc, update_modified=True):
	# Reload as billed amount was set in db directly
	pr_doc.load_from_db()

	# Update Billing % based on pending accepted qty
	total_amount, total_billed_amount = 0, 0
	for item in pr_doc.items:
		return_data = frappe.get_all(
			"Purchase Receipt",
			fields=["sum(abs(`tabPurchase Receipt Item`.qty)) as qty"],
			filters=[
				["Purchase Receipt", "docstatus", "=", 1],
				["Purchase Receipt", "is_return", "=", 1],
				["Purchase Receipt Item", "purchase_receipt_item", "=", item.name],
			],
		)

		returned_qty = return_data[0].qty if return_data else 0
		returned_amount = flt(returned_qty) * flt(item.rate)
		pending_amount = flt(item.amount) - returned_amount
		total_billable_amount = pending_amount if item.billed_amt <= pending_amount else item.billed_amt

		total_amount += total_billable_amount
		total_billed_amount += flt(item.billed_amt)

	percent_billed = round(100 * (total_billed_amount / (total_amount or 1)), 6)
	pr_doc.db_set("per_billed", percent_billed)
	pr_doc.load_from_db()

	if update_modified:
		pr_doc.set_status(update=True)
		pr_doc.notify_update()


@frappe.whitelist()
def make_purchase_invoice(source_name, target_doc=None):
	from erpnext.accounts.party import get_payment_terms_template

	doc = frappe.get_doc("Purchase Receipt", source_name)
	returned_qty_map = get_returned_qty_map(source_name)
	invoiced_qty_map = get_invoiced_qty_map(source_name)

	def set_missing_values(source, target):
		if len(target.get("items")) == 0:
			frappe.throw(_("All items have already been Invoiced/Returned"))

		doc = frappe.get_doc(target)
		doc.payment_terms_template = get_payment_terms_template(
			source.supplier, "Supplier", source.company
		)
		doc.run_method("onload")
		doc.run_method("set_missing_values")
		doc.run_method("calculate_taxes_and_totals")
		doc.set_payment_schedule()

	def update_item(source_doc, target_doc, source_parent):
		target_doc.qty, returned_qty = get_pending_qty(source_doc)
		if frappe.db.get_single_value(
			"Buying Settings", "bill_for_rejected_quantity_in_purchase_invoice"
		):
			target_doc.rejected_qty = 0
		target_doc.stock_qty = flt(target_doc.qty) * flt(
			target_doc.conversion_factor, target_doc.precision("conversion_factor")
		)
		returned_qty_map[source_doc.name] = returned_qty

	def get_pending_qty(item_row):
		qty = item_row.qty
		if frappe.db.get_single_value(
			"Buying Settings", "bill_for_rejected_quantity_in_purchase_invoice"
		):
			qty = item_row.received_qty
		pending_qty = qty - invoiced_qty_map.get(item_row.name, 0)
		returned_qty = flt(returned_qty_map.get(item_row.name, 0))
		if returned_qty:
			if returned_qty >= pending_qty:
				pending_qty = 0
				returned_qty -= pending_qty
			else:
				pending_qty -= returned_qty
				returned_qty = 0
		return pending_qty, returned_qty

	doclist = get_mapped_doc(
		"Purchase Receipt",
		source_name,
		{
			"Purchase Receipt": {
				"doctype": "Purchase Invoice",
				"field_map": {
					"supplier_warehouse": "supplier_warehouse",
					"is_return": "is_return",
					"bill_date": "bill_date",
				},
				"validation": {
					"docstatus": ["=", 1],
				},
			},
			"Purchase Receipt Item": {
				"doctype": "Purchase Invoice Item",
				"field_map": {
					"name": "pr_detail",
					"parent": "purchase_receipt",
					"purchase_order_item": "po_detail",
					"purchase_order": "purchase_order",
					"is_fixed_asset": "is_fixed_asset",
					"asset_location": "asset_location",
					"asset_category": "asset_category",
				},
				"postprocess": update_item,
				"filter": lambda d: get_pending_qty(d)[0] <= 0
				if not doc.get("is_return")
				else get_pending_qty(d)[0] > 0,
			},
			"Purchase Taxes and Charges": {"doctype": "Purchase Taxes and Charges", "add_if_empty": True},
		},
		target_doc,
		set_missing_values,
	)

	doclist.set_onload("ignore_price_list", True)
	return doclist


def get_invoiced_qty_map(purchase_receipt):
	"""returns a map: {pr_detail: invoiced_qty}"""
	invoiced_qty_map = {}

	for pr_detail, qty in frappe.db.sql(
		"""select pr_detail, qty from `tabPurchase Invoice Item`
		where purchase_receipt=%s and docstatus=1""",
		purchase_receipt,
	):
		if not invoiced_qty_map.get(pr_detail):
			invoiced_qty_map[pr_detail] = 0
		invoiced_qty_map[pr_detail] += qty

	return invoiced_qty_map


def get_returned_qty_map(purchase_receipt):
	"""returns a map: {so_detail: returned_qty}"""
	returned_qty_map = frappe._dict(
		frappe.db.sql(
			"""select pr_item.purchase_receipt_item, abs(pr_item.qty) as qty
		from `tabPurchase Receipt Item` pr_item, `tabPurchase Receipt` pr
		where pr.name = pr_item.parent
			and pr.docstatus = 1
			and pr.is_return = 1
			and pr.return_against = %s
	""",
			purchase_receipt,
		)
	)

	return returned_qty_map


@frappe.whitelist()
def make_purchase_return(source_name, target_doc=None):
	from erpnext.controllers.sales_and_purchase_return import make_return_doc

	return make_return_doc("Purchase Receipt", source_name, target_doc)


@frappe.whitelist()
def update_purchase_receipt_status(docname, status):
	pr = frappe.get_doc("Purchase Receipt", docname)
	pr.update_status(status)


@frappe.whitelist()
def make_stock_entry(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.stock_entry_type = "Material Transfer"
		target.purpose = "Material Transfer"
		target.set_missing_values()

	doclist = get_mapped_doc(
		"Purchase Receipt",
		source_name,
		{
			"Purchase Receipt": {
				"doctype": "Stock Entry",
			},
			"Purchase Receipt Item": {
				"doctype": "Stock Entry Detail",
				"field_map": {
					"warehouse": "s_warehouse",
					"parent": "reference_purchase_receipt",
					"batch_no": "batch_no",
				},
			},
		},
		target_doc,
		set_missing_values,
	)

	return doclist


@frappe.whitelist()
def make_inter_company_delivery_note(source_name, target_doc=None):
	return make_inter_company_transaction("Purchase Receipt", source_name, target_doc)


def get_item_account_wise_additional_cost(purchase_document):
	landed_cost_vouchers = frappe.get_all(
		"Landed Cost Purchase Receipt",
		fields=["parent"],
		filters={"receipt_document": purchase_document, "docstatus": 1},
	)

	if not landed_cost_vouchers:
		return

	item_account_wise_cost = {}

	for lcv in landed_cost_vouchers:
		landed_cost_voucher_doc = frappe.get_doc("Landed Cost Voucher", lcv.parent)

		# Use amount field for total item cost for manually cost distributed LCVs
		if landed_cost_voucher_doc.distribute_charges_based_on == "Distribute Manually":
			based_on_field = "amount"
		else:
			based_on_field = frappe.scrub(landed_cost_voucher_doc.distribute_charges_based_on)

		total_item_cost = 0

		for item in landed_cost_voucher_doc.items:
			total_item_cost += item.get(based_on_field)

		for item in landed_cost_voucher_doc.items:
			if item.receipt_document == purchase_document:
				for account in landed_cost_voucher_doc.taxes:
					item_account_wise_cost.setdefault((item.item_code, item.purchase_receipt_item), {})
					item_account_wise_cost[(item.item_code, item.purchase_receipt_item)].setdefault(
						account.expense_account, {"amount": 0.0, "base_amount": 0.0}
					)

					if total_item_cost > 0:
						item_account_wise_cost[(item.item_code, item.purchase_receipt_item)][
							account.expense_account
						]["amount"] += (
							account.amount * item.get(based_on_field) / total_item_cost
						)

						item_account_wise_cost[(item.item_code, item.purchase_receipt_item)][
							account.expense_account
						]["base_amount"] += (
							account.base_amount * item.get(based_on_field) / total_item_cost
						)
					else:
						item_account_wise_cost[(item.item_code, item.purchase_receipt_item)][
							account.expense_account
						]["amount"] += item.applicable_charges
						item_account_wise_cost[(item.item_code, item.purchase_receipt_item)][
							account.expense_account
						]["base_amount"] += item.applicable_charges

	return item_account_wise_cost


def on_doctype_update():
	frappe.db.add_index("Purchase Receipt", ["supplier", "is_return", "return_against"])


#New Code for ITC 
def level_up_se(se_m, data):
		get_manufacture(se_m, data)

def get_manufacture(batch, data, indent=0):
			# print(" this is Level_up ")
		
			soi_se = frappe.db.sql("""
									Select se.work_order from `tabStock Entry Detail` sed
									Join `tabStock Entry` se ON se.name = sed.parent
									where sed.batch_no = "{0}"
									and se.stock_entry_type = "Manufacture"
										""".format(batch), as_dict=1)	
			if soi_se:
				# print(" workorder ", soi_se[0].get('work_order'))
				se_01 = frappe.get_value("Stock Entry", { "work_order": soi_se[0].get('work_order'), "stock_entry_type" : "Material Transfer for Manufacture" }, ["name"])

				if se_01:
					# print(" se 01 ", se_01)
					se_02 = frappe.db.get_all("Stock Entry Detail", {"parent" : se_01}, ['*'])
					
					if se_02:
						# print(" se 012222222222 ")
						for s in se_02:
							s["indent"] = indent
							batch_new = s.get('batch_no')

							
							new_entry = frappe.db.sql("""
														Select se.name from `tabStock Entry Detail` sed
														Join `tabStock Entry` se ON se.name = sed.parent
														where sed.batch_no = "{0}"
														and se.stock_entry_type = "Manufacture"
													""".format(batch_new), as_dict=1)
							# if new_entry:
							# print(" new_ entry", new_entry)	
							if new_entry:
								get_manufacture(batch_new, data, indent= indent + 1)

							else:
								data.append({
								'item_code': s.item_code,
								'item_name': s.item_name,
								'parent' : s.parent,
								'indent': indent,
								'bom_level': indent,
								"stock_uom" : s.stock_uom,
								"required_qty" : s.qty,
								"qty_to_be_consumed" : s.qty,
								"rate" : s.basic_rate,
								"amount" : s.amount,
								"batch_no" : s.batch_no,
								"consumed_qty" : s.qty,
								'qty': s.qty ,
								'uom': s.uom,
								'description': s.description,
								'reference_challan':"",
								'reference_challan': "",
								})


def get_data(name,company):
	data = []
	# print(" dates", s_d, m_d, filters.get('company'))
	query = """
				Select pris.*, pr.name, pr.supplier ,pr.company  from `tabPurchase Receipt Item` pris
				Join `tabPurchase Receipt` pr on pr.name = pris.parent
				where pr.name='{0}'
				and pr.is_subcontracted = "Yes" and pr.docstatus = 0
				and pris.challan_number_issues_by_job_worker is not null
				and pr.company = '{1}' """.format(name,company)


	pr = frappe.db.sql(query,as_dict=1)

	print(" PR ", pr)
	for p in pr:
		# print("this is pr p", p.received_qty)
		if p.challan_number_issues_by_job_worker:
			# print(" this is salsinvoice child", p.challan_number_issues_by_job_worker)
			soi_item = frappe.db.get_value("Sales Invoice Item", p.challan_number_issues_by_job_worker, ['item_code', 'batch_no', 'sales_order'], as_dict= 1)
			# From Sales invoice to Sales Order and Sales Order to Work Order
			# print("soi_item.get(batch_no) ",soi_item.get("batch_no"))

			sales_invoice = frappe.db.get_value("Sales Invoice Item", p.challan_number_issues_by_job_worker, ["parent"])
			
			st_entry = frappe.db.sql("""
										Select se.name from `tabStock Entry Detail` sed
										Join `tabStock Entry` se ON se.name = sed.parent
										where sed.batch_no = "{0}"
										and se.stock_entry_type = "Manufacture"
									""".format(soi_item.get("batch_no")), as_dict=1)


			print("st entry8888888888888888888888888888", st_entry)

			# LEvel ONE
			if st_entry:
				print(" This is level 11111111111111111111111111 ")
				se_bom = frappe.get_doc("Stock Entry", st_entry[0].get("name"))
				# print(" this is stock entry bom", se_bom)

				se_01 = frappe.get_doc("Stock Entry", { "work_order": se_bom.get("work_order"), "stock_entry_type" : "Material Transfer for Manufacture" })
				print(" this is manafactuffe ", se_01, se_01.get("fg_completed_qty"))

				if se_01:
					se_01_child = frappe.get_all("Stock Entry Detail", {"parent":se_01.get("name")})

					for s in se_01_child:
						
						se = frappe.get_doc("Stock Entry Detail", s)
						print(" this is se o1 child", se.batch_no,se.item_code)

						if se.name:
							st_entry1 = frappe.db.sql("""
										Select se.name from `tabStock Entry Detail` sed
										Join `tabStock Entry` se ON se.name = sed.parent
										where sed.batch_no = "{0}"
										and se.stock_entry_type = "Manufacture"
									""".format(se.get("batch_no")), as_dict=1)
							print("*********************444444444444444444444444444",st_entry1)
							# Leve Two
							if st_entry1:
								print(" This is level 22222222222222222222222222 ")
								se_bom1 = frappe.get_doc("Stock Entry", st_entry1[0].get("name"))
								print(" this is se_bom1 oooooooooooo", se_bom1)

								se_011 = frappe.get_doc("Stock Entry", { "work_order": se_bom1.get("work_order"), "stock_entry_type" : "Material Transfer for Manufacture"})
								print(" this is manafactuffe 2", se_011)

								if se_011:
									se_01_child1 = frappe.get_all("Stock Entry Detail", {"parent":se_011.get("name")})

									for s1 in se_01_child1:
										
										se1 = frappe.get_doc("Stock Entry Detail", s1)
										print(" this is se o2 child", se1.batch_no,s1)

										if se1.name:
											st_entry2 = frappe.db.sql("""
														Select se.name from `tabStock Entry Detail` sed
														Join `tabStock Entry` se ON se.name = sed.parent
														where sed.batch_no = "{0}"
														and se.stock_entry_type = "Manufacture"

													""".format(se1.get("batch_no")), as_dict=1)

											# Level Three
											if st_entry2:
												print(" This is level 333333333333333333333333333333333")
											
												se_bom2 = frappe.get_doc("Stock Entry", st_entry2[0].get("name"))
												# print(" this is stock entry bom", se_bom)

												se_012 = frappe.get_doc("Stock Entry", { "work_order": se_bom2.get("work_order"), "stock_entry_type" : "Material Transfer for Manufacture" })
												print(" this is manafactuffe 3", se_012)

												if se_012:
													se_01_child2 = frappe.get_all("Stock Entry Detail", {"parent":se_012.get("name")})

													for s2 in se_01_child2:
														print(" thjos os child se ", s2)
														se2 = frappe.get_doc("Stock Entry Detail", s2)
														print(" this is se o3 child", se2.batch_no)

														if se2.name:
															st_entry3 = frappe.db.sql("""
																		Select se.name from `tabStock Entry Detail` sed
																		Join `tabStock Entry` se ON se.name = sed.parent
																		where sed.batch_no = "{0}"
																		and se.stock_entry_type = "Manufacture"
																	""".format(se2.get("batch_no")), as_dict=1)

															# Level Four 
															
															if st_entry3:
																print(" This is level 444444444444444444444444444")
																
																se_bom3 = frappe.get_doc("Stock Entry", st_entry3[0].get("name"))
																# print(" this is stock entry bom", se_bom)

																se_013 = frappe.get_doc("Stock Entry", { "work_order": se_bom3.get("work_order"), "stock_entry_type" : "Material Transfer for Manufacture" })
																print(" this is manafactuffe 4", se_013)

																if se_013:
																	se_01_child3 = frappe.get_all("Stock Entry Detail", {"parent":se_013.get("name")})

																	for s3 in se_01_child3:
																		print(" thjos os child se ", )
																		se3 = frappe.get_doc("Stock Entry Detail", s3)
																		print(" this is se o4 child", se3.batch_no)

																		if se3.name:
																			st_entry4 = frappe.db.sql("""
																						Select se.name from `tabStock Entry Detail` sed
																						Join `tabStock Entry` se ON se.name = sed.parent
																						where sed.batch_no = "{0}"
																						and se.stock_entry_type = "Manufacture"
																					""".format(se3.get("batch_no")), as_dict=1)

																			# Level Four 
																			
																			if st_entry4:
																				print(" This is level 55555555555555555555")
																				
																
																				se_bom4 = frappe.get_doc("Stock Entry", st_entry4[0].get("name"))
																				# print(" this is stock entry bom", se_bom)

																				se_014 = frappe.get_doc("Stock Entry", { "work_order": se_bom3.get("work_order"), "stock_entry_type" : "Material Transfer for Manufacture" })
																				print(" this is manafactuffe 5", se_014)

																				if se_014:
																					se_01_child4 = frappe.get_all("Stock Entry Detail", {"parent":se_014.get("name")})

																					for s4 in se_01_child4:
																						print(" thjos os child se ", )
																						se4 = frappe.get_doc("Stock Entry Detail", s4)
																						print(" this is se o5 child", se4.batch_no)
																						if se4:
																							ref_challan = ""
																							stock_e=[]
																							if se4.get("batch_no"):
																								stock_e = frappe.db.sql("""
																													Select se.reference_challan, se.posting_date from `tabStock Entry` se 
																													join `tabStock Entry Detail` sed on sed.parent = se.name 
																													where se.stock_entry_type = "Material Receipt"
																													and sed.batch_no = '{0}' and se.company="Kroslink Polymers Pvt Ltd"
																													""".format(se4.get("batch_no")), as_dict=1)
																								print("******************************************************",p.item_code,stock_e)
																							if len(stock_e)>0:
																								ref_challan = (stock_e[0].get('reference_challan'))
																																										
																							data3 = {}

																							supp_details = frappe.db.sql(""" select adds.gstin as gstin_of_job_worker,
																														adds.state as state, supp.gst_category as job_workers_type
																														from `tabSupplier` supp
																														INNER JOIN `tabDynamic Link` dl
																														on dl.link_name = supp.name
																														INNER JOIN `tabAddress` adds
																														on dl.parent = adds.name
																														where supp.name = %(supp)s """,
																														{'supp': p.get("supplier")}, as_dict=1)
																							if supp_details:								
																								dic2 = supp_details[0]
																								for key, value in dic2.items():
																									data3[key] = value
																							data3["production_item"]=p.item_code
																							data3["item_code"]=se4.get("item_code")	
																							data3["batch"]=se4.get("batch_no")
																							data3["rate"]=se4.get("basic_rate")
																							print("*********************************",se4.get("basic_rate"))
																							data3['original_challan_number_issued_by_principal'] = ref_challan
																							data3['original_challan_date_issued_by_principal'] = frappe.get_value("Stock Entry", ref_challan, 'posting_date')
																							data3['challan_number_issued_by_job_worker'] = sales_invoice
																							data3['challan_date_issued_by_job_worker'] = frappe.get_value("Sales Invoice", sales_invoice, 'posting_date')
																							data3['description_of_goods'] = se4.description
																							data3['unique_quantity_code'] = se4.stock_uom
																							a = (p.qty/ se_bom.get("fg_completed_qty") ) * se.qty
																							b = (a/ se_bom1.get("fg_completed_qty") ) * se1.qty
																							c = (b/ se_bom2.get("fg_completed_qty") ) * se2.qty
																							d = (c/ se_bom3.get("fg_completed_qty") ) * se3.qty
																							data3['quantity'] = (d/ se_bom4.get("fg_completed_qty") ) * se4.qty
																							data3['losses_uqc'] = se4.stock_uom
																							data3['losses_quantity'] = 0
																							data3['nature_of_job_work_done'] = p.nature_of_job_work_done
																							data.append(data3)			

																			else:
																				print(" no elseeeeeeeeee no batchhhh 444 44444",  se3.description)
																				ref_challan = ""
																				stock_e=[]
																				if se3.get("batch_no"):
																					stock_e = frappe.db.sql("""
																										Select se.reference_challan, se.posting_date from `tabStock Entry` se 
																										join `tabStock Entry Detail` sed on sed.parent = se.name 
																										where se.stock_entry_type = "Material Receipt"
																										and sed.batch_no = '{0}' and  se.company="Kroslink Polymers Pvt Ltd"
																										""".format(se3.get("batch_no")), as_dict=1)
																					print("******************************************************",stock_e)
																				if len(stock_e)> 0:
																					ref_challan = (stock_e[0].get('reference_challan'))
																																							
																				data3 = {}

																				supp_details = frappe.db.sql(""" select adds.gstin as gstin_of_job_worker,
																											adds.state as state, supp.gst_category as job_workers_type
																											from `tabSupplier` supp
																											INNER JOIN `tabDynamic Link` dl
																											on dl.link_name = supp.name
																											INNER JOIN `tabAddress` adds
																											on dl.parent = adds.name
																											where supp.name = %(supp)s """,
																											{'supp': p.get("supplier")}, as_dict=1)
																				if supp_details:								
																					dic2 = supp_details[0]
																					for key, value in dic2.items():
																						data3[key] = value
																				data3["production_item"]=p.item_code
																				data3["item_code"]=se3.get("item_code")
																				data3["rate"]=se3.get("basic_rate")
																				data3["batch"]=se3.get("batch_no")
																				data3['original_challan_number_issued_by_principal'] = ref_challan
																				data3['original_challan_date_issued_by_principal'] = frappe.get_value("Stock Entry", ref_challan, 'posting_date')
																				data3['challan_number_issued_by_job_worker'] = sales_invoice
																				data3['challan_date_issued_by_job_worker'] = frappe.get_value("Sales Invoice", sales_invoice, 'posting_date')
																				data3['description_of_goods'] = se3.description
																				data3['unique_quantity_code'] = se3.stock_uom
																				a = (p.qty/ se_bom.get("fg_completed_qty") ) * se.qty
																				b = (a/ se_bom1.get("fg_completed_qty") ) * se1.qty
																				c = (b/ se_bom2.get("fg_completed_qty") ) * se2.qty
																				data3['quantity'] = (c/ se_bom3.get("fg_completed_qty") ) * se3.qty
																				data3['losses_uqc'] = se3.stock_uom
																				data3['losses_quantity'] = 0
																				data3['nature_of_job_work_done'] = p.nature_of_job_work_done
																				data.append(data3)
																		

																	
															else:
																print(" no elseeeeeeeeee no batchhhh 33333   33333",  se2.description,company)
																stock_e=[]
																ref_challan = ""
																if se2.get("batch_no"):
																	stock_e = frappe.db.sql("""
																						Select se.reference_challan, se.posting_date from `tabStock Entry` se 
																						join `tabStock Entry Detail` sed on sed.parent = se.name 
																						where se.stock_entry_type = "Material Receipt"
																						and sed.batch_no = '{0}' and se.company="Kroslink Polymers Pvt Ltd"
																						""".format(se2.get("batch_no")), as_dict=1)
																	print("******************************************************",stock_e)
																if len(stock_e)>0:
																	ref_challan = (stock_e[0].get('reference_challan'))
																																			
																data3 = {}

																supp_details = frappe.db.sql(""" select adds.gstin as gstin_of_job_worker,
																							adds.state as state, supp.gst_category as job_workers_type
																							from `tabSupplier` supp
																							INNER JOIN `tabDynamic Link` dl
																							on dl.link_name = supp.name
																							INNER JOIN `tabAddress` adds
																							on dl.parent = adds.name
																							where supp.name = %(supp)s """,
																							{'supp': p.get("supplier")}, as_dict=1)
																if supp_details:								
																	dic2 = supp_details[0]
																	for key, value in dic2.items():
																		data3[key] = value
																data3["production_item"]=p.item_code
																data3["item_code"]=se2.get("item_code")
																data3["rate"]=se2.get("basic_rate")
																data3["batch"]=se2.get("batch_no")	
																data3['original_challan_number_issued_by_principal'] = ref_challan
																data3['original_challan_date_issued_by_principal'] = frappe.get_value("Stock Entry", ref_challan, 'posting_date')
																data3['challan_number_issued_by_job_worker'] = sales_invoice
																data3['challan_date_issued_by_job_worker'] = frappe.get_value("Sales Invoice", sales_invoice, 'posting_date')
																data3['description_of_goods'] = se2.description
																data3['unique_quantity_code'] = se2.stock_uom
																a = (p.qty/ se_bom.get("fg_completed_qty") ) * se.qty
																b = (a/ se_bom1.get("fg_completed_qty") ) * se1.qty
																data3['quantity'] = (b/ se_bom2.get("fg_completed_qty") ) * se2.qty
																data3['losses_uqc'] = se2.stock_uom
																data3['losses_quantity'] = 0
																data3['nature_of_job_work_done'] = p.nature_of_job_work_done
																data.append(data3)
																

											else:
												print(" this is no000000000000000000000000000 22222222  22222222",  se1.description)	
												ref_challan = ""
												stock_e=[]
												if se1.get("batch_no"):
													stock_e = frappe.db.sql("""
																		Select se.reference_challan,sed.batch_no, se.posting_date from `tabStock Entry` se 
																		join `tabStock Entry Detail` sed on sed.parent = se.name 
																		where se.stock_entry_type = "Material Receipt"
																		and sed.batch_no = '{0}' and se.company="Kroslink Polymers Pvt Ltd"
																		""".format(se1.get("batch_no")), as_dict=1)
													print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&7",stock_e)
												if len(stock_e)>0:
													ref_challan = (stock_e[0].get('reference_challan'))
																															
												data3 = {}

												supp_details = frappe.db.sql(""" select adds.gstin as gstin_of_job_worker,
																			adds.state as state, supp.gst_category as job_workers_type
																			from `tabSupplier` supp
																			INNER JOIN `tabDynamic Link` dl
																			on dl.link_name = supp.name
																			INNER JOIN `tabAddress` adds
																			on dl.parent = adds.name
																			where supp.name = %(supp)s """,
																			{'supp': p.get("supplier")}, as_dict=1)
												if supp_details:								
													dic2 = supp_details[0]
													for key, value in dic2.items():
														data3[key] = value
												data3["production_item"]=p.item_code
												data3["rate"]=se1.get("basic_rate")
												data3["item_code"]=se1.get("item_code")
												data3["batch"]=se1.get("batch_no")
												data3['original_challan_number_issued_by_principal'] = ref_challan
												data3['original_challan_date_issued_by_principal'] = frappe.get_value("Stock Entry", ref_challan, 'posting_date')
												data3['description_of_goods'] = se1.description
												data3['unique_quantity_code'] = se1.stock_uom
												data3['challan_number_issued_by_job_worker'] = sales_invoice
												data3['challan_date_issued_by_job_worker'] = frappe.get_value("Sales Invoice", sales_invoice, 'posting_date')
												# data3['quantity'] = se1.qty
												a = (p.qty/ se_bom.get("fg_completed_qty") ) * se.qty
												data3['quantity'] = (a/ se_bom1.get("fg_completed_qty") ) * se1.qty
												data3['losses_uqc'] = se1.stock_uom
												data3['losses_quantity'] = 0
												data3['nature_of_job_work_done'] = p.nature_of_job_work_done	
												data.append(data3)				

										
							# level 0
							else :
								stock_e=[]
								ref_challan = ""
								if se.get("batch_no"):
									stock_e = frappe.db.sql("""
														Select se.reference_challan, se.posting_date from `tabStock Entry` se 
														join `tabStock Entry Detail` sed on sed.parent = se.name 
														where se.stock_entry_type = "Material Receipt"
														and sed.batch_no = '{0}' and se.company="Kroslink Polymers Pvt Ltd"
														""".format(se.get("batch_no")), as_dict=1)
									print("******************************************************",stock_e)
								if len(stock_e)>0:
									ref_challan = (stock_e[0].get('reference_challan'))
																											
								data3 = {}

								supp_details = frappe.db.sql(""" select adds.gstin as gstin_of_job_worker,
															adds.state as state, supp.gst_category as job_workers_type
															from `tabSupplier` supp
															INNER JOIN `tabDynamic Link` dl
															on dl.link_name = supp.name
															INNER JOIN `tabAddress` adds
															on dl.parent = adds.name
															where supp.name = %(supp)s """,
															{'supp': p.get("supplier")}, as_dict=1)
								if supp_details:								
									dic2 = supp_details[0]
									for key, value in dic2.items():
										data3[key] = value
								data3["production_item"]=p.item_code
								data3["item_code"]=se.get("item_code")	
								data3["batch"]=se.get("batch_no")
								data3["rate"]=se.get("basic_rate")
								print(" this is no000000000000000000000000000 11 ",  se.description)	
								data3['original_challan_number_issued_by_principal'] = ref_challan
								data3['original_challan_date_issued_by_principal'] = frappe.get_value("Stock Entry", ref_challan, 'posting_date')
								data3['challan_number_issued_by_job_worker'] = sales_invoice
								data3['challan_date_issued_by_job_worker'] = frappe.get_value("Sales Invoice", sales_invoice, 'posting_date')
								data3['description_of_goods'] = se.description
								data3['unique_quantity_code'] = se.stock_uom
								data3['quantity'] = (p.qty/ se_bom.get("fg_completed_qty") ) * se.qty
								data3['losses_uqc'] = se.stock_uom
								data3['losses_quantity'] = 0
								data3['nature_of_job_work_done'] = p.nature_of_job_work_done
								data.append(data3)

	mr=[]
	if name:
		po=frappe.get_doc("Purchase Receipt",name)
		for k in po.items:
			if k.purchase_order and k.idx==1:
				pe=frappe.db.get_all("Stock Entry",{"purchase_order":k.purchase_order},["name"])
				for l in pe:
					mr.append(l.name)
	total=[]
	if len(mr) > 1:
		total=tuple(mr)
	if len(mr)==1:
		total=mr[0]
	query2=""				
	if len(mr)>1:			
	
		query2 = """
					Select * from `tabStock Entry Detail` sed
					Left Join `tabStock Entry` se on se.name = sed.parent
					where se.stock_entry_type = "Material Receipt" 
					and se.docstatus = 1
					and se.return_from_supplier_for_itc_05 = 1
					and se.reference_challan is not null
					and se.name in {0}
					and se.company = '{1}' """.format(total, company)
	if len(mr)==1:
		query2 = """
					Select * from `tabStock Entry Detail` sed
					Left Join `tabStock Entry` se on se.name = sed.parent
					where se.stock_entry_type = "Material Receipt" 
					and se.docstatus = 1
					and se.return_from_supplier_for_itc_05 = 1
					and se.reference_challan is not null
					and se.name ='{0}'
					and se.company = '{1}' """.format(total, company)
	if query2:
		pr1 = frappe.db.sql(query2,as_dict=1)	
		print("&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&",len(pr1))
		for p in pr1:
			if p.reference_challan and p.return_from_supplier_for_itc_05 == 1:
				data3 = {}
				sales_invoice = ""
				si_date = ""
				nature = ""
				if p.reference_name:
					pr_item = frappe.get_doc("Purchase Receipt Item", p.reference_name)
					# print(" tjhis is PURCHASE RECEIPT ITEM", type(pr_item), pr_item.challan_number_issues_by_job_worker)
					nature = pr_item.nature_of_job_work_done
					sales_invoice, si_date = frappe.db.get_value("Sales Invoice Item", pr_item.challan_number_issues_by_job_worker, ["parent", "modified"])
					# print( " pidd Natuer ", nature)

				
				data3['challan_number_issued_by_job_worker'] = p.reference_challan
				data3['challan_date_issued_by_job_worker'] = frappe.get_value("Stock Entry", p.reference_challan, 'posting_date') 
				supp_details = frappe.db.sql(""" select adds.gstin as gstin_of_job_worker,
												adds.state as state, supp.gst_category as job_workers_type
												from `tabSupplier` supp
												INNER JOIN `tabDynamic Link` dl
												on dl.link_name = supp.name
												INNER JOIN `tabAddress` adds
												on dl.parent = adds.name
												where supp.name = %(supp)s """,
												{'supp': p.get("return_supplier_")}, as_dict=1)
				if supp_details:								
					dic2 = supp_details[0]
					for key, value in dic2.items():
						data3[key] = value

				rm_item_obj = frappe.get_doc("Item", p.item_code)
				data3["production_item"]=p.item_code
				data3["item_code"]=p.item_code
				data3["batch"]=p.batch_no
				data3['description_of_goods'] = rm_item_obj.description
				data3['unique_quantity_code'] = p.stock_uom
				data3['quantity'] = p.qty
				data3['losses_uqc'] = p.stock_uom
				data3['losses_quantity'] = 0
				data3['nature_of_job_work_done'] = nature
				data3['original_challan_number_issued_by_principal'] = p.name
				data3['original_challan_date_issued_by_principal'] = p.posting_date

				data.append(data3)
		print("**************************************45",data)
	return data
