# # -*- coding: utf-8 -*-
# # Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# # For license information, please see license.txt

# from __future__ import unicode_literals
# # import frappe
# from frappe.model.document import Document

# class MaterialProduce(Document):
# 	pass

# -*- coding: utf-8 -*-
# Copyright (c) 2021, Dexciss Technology and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.model.meta import get_field_precision
import json
# from erpnext.manufacturing.doctype.bom.bom import add_additional_cost
from frappe.utils import cint, cstr, flt

class MaterialProduce(Document):
    @frappe.whitelist()
    def set_produce_material(self):
        if self.material_produce_details:
            total_qty = 0
            line_id = None
            for res in self.material_produce_details:
                total_qty += flt(res.qty_produced, res.precision('qty_produced'))
                line_id = res.line_ref
            l_doc = frappe.get_doc("Material Produce Item", line_id)
            # if l_doc.qty_produced:
            #     if total_qty > l_doc.qty_produced:
            #         pass
                    #frappe.throw(_("Can not allow total produced qty greater then {0}").format(l_doc.qty_produced))
            lst = []
            i = frappe.get_doc("Batch Settings")
            for res in self.material_produce_details:
                if res.qty_produced:
                    lst.append({
                        "item_code": res.item_code,
                        "item_name": res.item_name,
                        "t_warehouse": res.t_warehouse,
                        "qty_produced": flt(res.qty_produced, res.precision('qty_produced')),
                        "has_batch_no": res.has_batch_no,
                        "batch": res.batch_no if i.is_finish_batch_series == "Manual" else res.batch_series,
                        "rate": flt(res.rate, res.precision('rate')),
                        "weight": res.weight,
                        "line_ref": res.line_ref
                    })
            if line_id:
                l_doc = frappe.get_doc("Material Produce Item", line_id)
                l_doc.data = json.dumps(lst)
                l_doc.qty_produced = flt(total_qty, l_doc.precision('qty_produced'))
                l_doc.status = "Set"
                l_doc.save(ignore_permissions=True)
        return True

    def on_submit(self):
        self.our_validation()

    # def on_cancel(self):
    #     pass
        # self.calc_actual_fg_wt_on_wo()

    def calc_actual_fg_wt_on_wo(self):
        wo = frappe.get_doc("Work Order", self.work_order)
        wo.actual_fg_weight = flt(flt(wo.produced_qty) * flt(wo.weight_per_unit), wo.precision('actual_fg_weight'))
        wo.db_update()

    def our_validation(self):
        if self.partial_produce:
            wo = frappe.get_doc("Work Order", self.work_order)
            wo.actual_yeild = flt(self.actual_yeild_on_wo(), wo.precision('actual_yeild'))
            frappe.db.set_value("Work Order", self.work_order, "actual_yeild", wo.actual_yeild)
            self.make_se()
        else:
            atleast_one_mc = frappe.db.sql("""select * from `tabMaterial Consumption` where work_order = %s and docstatus = 1""", (self.work_order))
            if atleast_one_mc:
                # no_previous_complete_mc = frappe.db.count('Material Produce', {'work_order': self.work_order, 'docstatus': 1, 'partial_produce': 0})
                previous_complete_mp = frappe.db.sql("""select * from `tabMaterial Produce` where work_order = %s and docstatus = 1 and partial_produce = 0""", (self.work_order),as_dict = 1)
                if len(previous_complete_mp) == 0 or previous_complete_mp[0].get('name') == self.name:
                    mfg = frappe.get_doc("Manufacturing Settings")
                    wo = frappe.get_doc("Work Order", self.work_order)
                    if self.actual_yeild_on_wo() >= (wo.bom_yeild-mfg.allowed_production_deviation_percentage) and self.actual_yeild_on_wo() <= (wo.bom_yeild+mfg.allowed_production_deviation_percentage):
                        self.calc_actual_fg_wt_on_wo() 
                        wo.actual_yeild = flt(self.actual_yeild_on_wo(), wo.precision('actual_yeild'))
                        frappe.db.set_value("Work Order", self.work_order, "actual_yeild", wo.actual_yeild)
                        self.make_se()
                    else:
                        frappe.throw(_('Actual yeild is not within deviation limits'))
                else:
                    frappe.throw(_('Another complete Material Produce for {0} is already present'.format(self.work_order)))
                    #frappe.throw(_('Another complete Material Produce for {0} is already present'.format(len(previous_complete_mp))))
            else:
                frappe.throw(_('Atleast one submitted Material Consumption required'))

    def actual_yeild_on_wo(self):
        value = 0
        wo = frappe.get_doc("Work Order", self.work_order)
        # wo.actual_fg_weight = flt(flt(wo.produced_qty) * flt(wo.weight_per_unit), wo.precision('actual_fg_weight'))
        wo.actual_fg_weight = flt(flt(wo.consumed_total_weight) * flt(wo.weight_per_unit), wo.precision('actual_fg_weight'))
        frappe.db.set_value("Work Order", self.work_order, "actual_fg_weight", wo.actual_fg_weight)
        if wo.actual_rm_weight == 0 or wo.actual_rm_weight == None:
            wo.actual_yeild = 0
        else:
            # wo.actual_yeild = flt((flt(wo.actual_fg_weight)/flt(wo.actual_rm_weight))*100, wo.precision('actual_yeild'))
            value = flt((flt(wo.actual_fg_weight)/flt(wo.actual_rm_weight))*100)
        return value

    def cost_details_calculation(self):
        precision1 = get_field_precision(frappe.get_meta("Material Produce").get_field("cost_of_scrap"))
        if self.partial_produce:
            wo = frappe.get_doc("Work Order", self.work_order)
            total_transfer_qty = 0
            for res in self.material_produce_item:
                if res.type == "FG":
                    total_transfer_qty += flt(res.qty_produced)
            if wo.qty == 0:
                self.cost_of_rm_consumed = 0
                self.cost_of_operation_consumed = 0
            else:
                self.cost_of_rm_consumed = flt(((flt(wo.planned_rm_cost))/(flt(wo.qty)))*total_transfer_qty, self.precision("cost_of_rm_consumed"))
                self.cost_of_operation_consumed = flt((flt(wo.planned_operating_cost)/flt(wo.qty))*total_transfer_qty, self.precision('cost_of_operation_consumed'))
        else:
            tcrmc = tcoc = scrap_cost = 0
            wo = frappe.get_doc("Work Order", self.work_order)
            value = frappe.db.sql("""select cost_of_rm_consumed, cost_of_operation_consumed from `tabMaterial Produce`
                                  where partial_produce = 1 and docstatus = 1 and work_order = %s""",(self.work_order), as_dict = True)
            for val in value:
                tcrmc += val.cost_of_rm_consumed
                tcoc += val.cost_of_operation_consumed

            self.total_cost_of_rm_consumed_for_partial_close = flt(tcrmc, self.precision('total_cost_of_rm_consumed_for_partial_close'))
            self.total_cost_of_operation_consumed_for_partial_close = flt(tcoc, self.precision('total_cost_of_operation_consumed_for_partial_close'))
            self.wo_actual_rm_cost = flt(wo.actual_rm_cost, self.precision('wo_actual_rm_cost'))
            self.wo_actual_operating_cost = flt(wo.total_operating_cost, self.precision('wo_actual_operating_cost'))

            for res in self.material_produce_item:
                scrap_cost = 0
                if res.type == "Scrap" and res.data:
                    for line in json.loads(res.data):
                        if line.get('rate'):
                            scrap_cost += flt(line.get('rate'))
            self.cost_of_scrap = flt(scrap_cost, self.precision('cost_of_scrap'))

            self.amount = flt((self.wo_actual_rm_cost + self.wo_actual_operating_cost) - (self.total_cost_of_rm_consumed_for_partial_close + self.total_cost_of_operation_consumed_for_partial_close + self.cost_of_scrap), self.precision('amount'))
            
    def make_stock_entry(self):
        return self.make_se()

    def make_se(self):
        wo = frappe.get_doc("Work Order",self.work_order)
        stock_entry = frappe.new_doc("Stock Entry")
        stock_entry.work_order = self.work_order
        stock_entry.bom_no = wo.bom_no
        stock_entry.from_bom = 1
        stock_entry.use_multi_level_bom = wo.use_multi_level_bom
        stock_entry.material_produce = self.name
        stock_entry.company = self.company
        stock_entry.stock_entry_type = "Manufacture"
        total_transfer_qty = 0
        lst = []
        for res in self.material_produce_item:
            if res.status == 'Not Set':
                lst.append(0)
            else:
                lst.append(1)
        if 1 not in lst:
            frappe.throw(_("At least one Item required to be Produce"))

        wo = frappe.get_doc("Work Order",self.work_order)
        for res in self.material_produce_item:
            if res.type == "FG":
                total_transfer_qty += flt(res.qty_produced, res.precision('qty_produced'))

#         for res in wo.required_items:
#             qty = 0
#             if res.transferred_qty:
#                 expense_account, cost_center = frappe.db.get_values("Company", self.company, ["default_expense_account", "cost_center"])[0]
#                 item_expense_account, item_cost_center = frappe.db.get_value("Item Default",
#                                 {'parent': res.item_code,'company': self.company},["expense_account","buying_cost_center"])
#                 if not cost_center and not item_cost_center:
#                     frappe.throw(_("Please update default Cost Center for company {0}").format(self.company))
#                 if self.partial_produce:
#                     if res.additional_material:
#                         qty = res.transferred_qty
#                     else:
#                         bom = frappe.get_doc("BOM",wo.bom_no)
#                         if bom.exploded_items:
#                             query = frappe.db.sql("""select (bl.stock_qty / ifnull(b.quantity, 1)) as 'qty' 
#                                 from `tabBOM` as b 
#                                 inner join `tabBOM Explosion Item` as bl on bl.parent = b.name
#                                 where bl.item_code = %s and b.name = %s limit 1""",(res.item_code,bom.name))
#                             if query:
#                                 qty = float(query[0][0]) * total_transfer_qty
#                             else:
#                                 qty = res.transferred_qty
#                         elif bom.scrap_items:
#                             query = frappe.db.sql("""select (bl.stock_qty / ifnull(b.quantity, 1)) as 'qty' 
#                                 from `tabBOM` as b 
#                                 inner join `tabBOM Scrap Item` as bl on bl.parent = b.name
#                                 where bl.item_code = %s and b.name = %s limit 1""",(res.item_code,bom.name))
#                             if query:
#                                 qty = float(query[0][0]) * total_transfer_qty
#                             else:
#                                 qty = res.transferred_qty
#                         else:
#                             query = frappe.db.sql("""select (bl.qty / ifnull(b.quantity, 1)) as 'qty' 
#                                 from `tabBOM` as b 
#                                 inner join `tabBOM Item` as bl on bl.parent = b.name
#                                 where bl.item_code = %s and b.name = %s limit 1""",(res.item_code,bom.name))
#                             if query:
#                                 qty = float(query[0][0]) * total_transfer_qty
#                             else:
#                                 qty = res.transferred_qty
#                 else:
#                     qty = res.transferred_qty - res.consumed_qty
#                     stock_entry.completed_work_order = 1
#                 itm_doc = frappe.get_doc("Item",res.item_code)
#                 if qty > 0:
#                     se_item = stock_entry.append("items")
#                     se_item.item_code = res.item_code
#                     se_item.qty = qty
#                     se_item.s_warehouse = wo.wip_warehouse
#                     se_item.item_name = itm_doc.item_name
#                     se_item.description = itm_doc.description
#                     se_item.uom = itm_doc.stock_uom
#                     se_item.stock_uom = itm_doc.stock_uom
#                     se_item.expense_account = item_expense_account or expense_account
#                     se_item.cost_center = item_cost_center or cost_center
#                     # in stock uom
#                     se_item.conversion_factor = 1.00
        stock_entry.calculate_rate_and_amount(raise_error_if_no_rate=False)
        for res in self.material_produce_item:
            if res.data:
                for line in json.loads(res.data):
                    batch_no = None
                    if line.get('has_batch_no'):
                        batch_name = make_autoname(line.get('batch'))
                        batch_no = frappe.get_doc(dict(
                            doctype='Batch',
                            batch_id=batch_name,
                            item=line.get('item_code'),
                            supplier=getattr(self, 'supplier', None),
                            reference_doctype=self.doctype,
                            reference_name=self.name)).insert().name
                    expense_account, cost_center = frappe.db.get_values("Company", self.company, ["default_expense_account", "cost_center"])[0]
                    item_expense_account, item_cost_center = frappe.db.get_value("Item Default",
                                            {'parent': line.get('item_code'),'company': self.company},["expense_account","buying_cost_center"])
                    if not cost_center and not item_cost_center:
                        frappe.throw(_("Please update default Cost Center for company {0}").format(self.company))

                    itm_doc = frappe.get_doc("Item", line.get('item_code'))
                    if line.get('qty_produced') > 0:
                        se_item = stock_entry.append("items")
                        se_item.item_code = line.get('item_code')
                        se_item.qty = flt(line.get('qty_produced'), se_item.precision('qty'))
                        se_item.t_warehouse = line.get('t_warehouse')
                        se_item.item_name = itm_doc.item_name
                        se_item.description = itm_doc.description
                        se_item.uom = res.uom
                        se_item.mrp = res.mrp
                        se_item.stock_uom = res.uom
                        se_item.batch_no = batch_no
                        se_item.basic_rate=line.get("rate")
                        se_item.expense_account = item_expense_account or expense_account
                        se_item.cost_center = wo.rm_cost_center or item_cost_center or cost_center
                        se_item.is_finished_item = 1 if res.type == 'FG' else 0
                        se_item.is_scrap_item = 1 if res.type == 'Scrap' else 0
                        # in stock uom
                        se_item.conversion_factor = 1.00
            
        stock_entry.from_bom = 1
        stock_entry.fg_completed_qty = flt(total_transfer_qty, stock_entry.precision('fg_completed_qty'))
        add_additional_cost(stock_entry, wo)
        stock_entry.set_actual_qty()
        stock_entry.set_missing_values()
        stock_entry.insert(ignore_permissions=True)
        stock_entry.validate()
        stock_entry.validate_work_order()
        stock_entry.flags.ignore_validate_update_after_submit = True
        stock_entry.submit()
        return stock_entry.as_dict()


    @frappe.whitelist()
    def add_details_line(self, partial_produce, bom, type,line_id, work_order, item_code, warehouse,qty_produced=None,batch_size=None, data=None, amount=None):
        precision1 = get_field_precision(frappe.get_meta("Material Produce Detail").get_field("qty_produced"))
        precision2 = get_field_precision(frappe.get_meta("Material Produce").get_field("batch_size"))
        precision3 = get_field_precision(frappe.get_meta("Material Produce").get_field("amount"))
        precision4 = get_field_precision(frappe.get_meta("Material Produce Detail").get_field("rate"))

        if qty_produced:
            qty_produced = flt(qty_produced, precision1)
        else:
            qty_produced = 0
        if batch_size:
            batch_size = flt(batch_size, precision2)
        else:
            batch_size = 0
        if not data:
            item = frappe.get_doc("Item", item_code)
            lst = []
            batch_option = None
            enabled = frappe.db.get_single_value('Batch Settings', 'enabled')
            #i = frappe.get_doc("Material Produce Detail",{"item_code":item_code})
            # item_master_batch_series = frappe.db.get_value('Item', {"item_code": item_code}, ['batch_series'])
            # if item_master_batch_series:
            if item.batch_number_series and enabled == 0:
                batch_option = item.batch_number_series
            elif enabled:
                is_finish_batch_series = frappe.db.get_single_value('Batch Settings', 'is_finish_batch_series')
                batch_series = frappe.db.get_single_value('Batch Settings', 'batch_series')
                if is_finish_batch_series == 'Use Work Order as Series':
                    batch_option = str(work_order) + "-.##"
                if is_finish_batch_series == 'Create New':
                    batch_option = batch_series
                # if is_finish_batch_series == 'Manual':
                #     batch_option = i.batch_no  
                
            else:
                # if item.batch_number_series:
                #     batch_option = item.batch_number_series
                # else:
                batch_option = str(work_order) + "-.##"
            if not amount:
                amount = 0
            else:
                amount = flt(amount, precision3)
            if qty_produced >= 1:
                if type == "Scrap":
                    bo = frappe.get_doc("BOM", bom)
                    if bo.scrap_items:
                        for row in bo.scrap_items:
                            per_item_rate = flt(row.rate, row.precision('rate'))
                            break
                    else:
                        per_item_rate = 0
                else:
                    if partial_produce:
                        if self.cost_of_rm_consumed == 0:
                            wo = frappe.get_doc("Work Order", self.work_order)
                            total_transfer_qty = 0
                            for res in self.material_produce_item:
                                if res.type == "FG":
                                    total_transfer_qty += flt(res.qty_produced)
                            if wo.qty == 0:
                                self.cost_of_rm_consumed = 0
                                self.cost_of_operation_consumed = 0
                            else:
                                self.cost_of_rm_consumed = flt(((flt(wo.planned_rm_cost))/(flt(wo.qty)))*total_transfer_qty, self.precision("cost_of_rm_consumed"))
                                self.cost_of_operation_consumed = flt((flt(wo.planned_operating_cost)/flt(wo.qty))*total_transfer_qty, self.precision('cost_of_operation_consumed'))
                        per_item_rate = flt((flt(self.cost_of_rm_consumed)+flt(self.cost_of_operation_consumed))/flt(qty_produced), precision4)
                    else:
                        per_item_rate = flt(flt(amount) / flt(qty_produced), precision4)
            else:
                per_item_rate = 0

            wo = frappe.get_doc("Work Order", self.work_order)
            if item.has_batch_no:
                remaining_size = qty_produced
                if batch_size:
                    while True:
                        if (remaining_size >= batch_size):
                            lst.append({
                                "item_code": item.name,
                                "item_name": item.item_name,
                                "t_warehouse": warehouse,
                                "qty_produced": flt(batch_size, precision1),
                                "has_batch_no": item.has_batch_no,
                                "batch": batch_option if item.has_batch_no else None,
                                "rate": flt(per_item_rate, precision4),
                                "weight": item.weight_per_unit,
                                "line_ref": line_id,
                                # "work_order_total_cost":wo.work_order_total_cost,
                                # "scrap_total_cost":wo.scrap_total_cost

                            })
                        else:
                            lst.append({
                                "item_code": item.name,
                                "item_name": item.item_name,
                                "t_warehouse": warehouse,
                                "qty_produced": flt(remaining_size, precision1),
                                "has_batch_no": item.has_batch_no,
                                "batch": batch_option if item.has_batch_no else None,
                                "rate": flt(per_item_rate, precision4),
                                "weight": item.weight_per_unit,
                                "line_ref": line_id,
                                # "work_order_total_cost":wo.work_order_total_cost,
                                # "scrap_total_cost":wo.scrap_total_cost
                            })
                            break
                        remaining_size -= batch_size
                        if(remaining_size < 1):
                            break
                else:
                    lst.append({
                        "item_code": item.name,
                        "item_name": item.item_name,
                        "t_warehouse": warehouse,
                        "qty_produced": flt(qty_produced, precision1),
                        "has_batch_no": item.has_batch_no,
                        "batch": batch_option if item.has_batch_no else None,
                        "rate": flt(per_item_rate, precision4),
                        "weight": item.weight_per_unit,
                        "line_ref": line_id,
                        # "work_order_total_cost":wo.work_order_total_cost,
                        # "scrap_total_cost":wo.scrap_total_cost
                    })
            else:
                lst.append({
                    "item_code": item.name,
                    "item_name": item.item_name,
                    "t_warehouse": warehouse,
                    "qty_produced": flt(qty_produced, precision1),
                    "has_batch_no": item.has_batch_no,
                    "weight": item.weight_per_unit,
                    "rate": flt(per_item_rate, precision4),
                    "line_ref": line_id,
                    # "work_order_total_cost":wo.work_order_total_cost,
                    # "scrap_total_cost":wo.scrap_total_cost
                })
            self.cost_details_calculation()
            return lst
        else:
            self.cost_details_calculation()
            return json.loads(data)

def add_additional_cost(stock_entry, work_order):
    # Add non stock items cost in the additional cost
    stock_entry.additional_costs = []
    expenses_included_in_valuation = frappe.get_cached_value("Company", work_order.company,
        "expenses_included_in_valuation")

    add_non_stock_items_cost(stock_entry, work_order, expenses_included_in_valuation)
    add_operations_cost(stock_entry, work_order, expenses_included_in_valuation)


def add_non_stock_items_cost(stock_entry, work_order, expense_account):
    bom = frappe.get_doc('BOM', work_order.bom_no)
    table = 'exploded_items' if work_order.get('use_multi_level_bom') else 'items'

    items = {}
    for d in bom.get(table):
        items.setdefault(d.item_code, d.amount)

    non_stock_items = frappe.get_all('Item',
        fields="name", filters={'name': ('in', list(items.keys())), 'ifnull(is_stock_item, 0)': 0}, as_list=1)

    non_stock_items_cost = 0.0
    for name in non_stock_items:
        non_stock_items_cost += flt(items.get(name[0])) * flt((stock_entry.fg_completed_qty), stock_entry.precision('fg_completed_qty')) / flt((bom.quantity), bom.precision('quantity'))

    if non_stock_items_cost:
        stock_entry.append('additional_costs', {
            'expense_account': expense_account,
            'description': _("Non stock items"),
            'amount': non_stock_items_cost
        })

def add_operations_cost(stock_entry, work_order=None, expense_account=None):
    from erpnext.stock.doctype.stock_entry.stock_entry import get_operating_cost_per_unit
    operating_cost_per_unit = get_operating_cost_per_unit(work_order, stock_entry.bom_no)

    if stock_entry.material_produce:
        mp_doc = frappe.get_doc("Material Produce", stock_entry.material_produce)
        if not mp_doc.partial_produce:
            if stock_entry.fg_completed_qty == 0:
                operating_cost_per_unit = 0
            else:
                operating_cost_per_unit = flt((flt((mp_doc.wo_actual_operating_cost), mp_doc.precision('wo_actual_operating_cost')) - flt((mp_doc.total_cost_of_operation_consumed_for_partial_close), mp_doc.precision('total_cost_of_operation_consumed_for_partial_close'))) / flt((stock_entry.fg_completed_qty), stock_entry.precision('fg_completed_qty')))
    if operating_cost_per_unit:
        stock_entry.append('additional_costs', {
            "expense_account": expense_account,
            "description": _("Operating Cost as per Work Order / BOM"),
            "amount": operating_cost_per_unit * flt((stock_entry.fg_completed_qty), stock_entry.precision('fg_completed_qty'))
        })

    if work_order and work_order.additional_operating_cost and work_order.qty:
        additional_operating_cost_per_unit = \
            flt((work_order.additional_operating_cost), work_order.precision('additional_operating_cost')) / flt((work_order.qty), work_order.precision('qty'))
        if additional_operating_cost_per_unit:
            stock_entry.append('additional_costs', {
                "expense_account": expense_account,
                "description": "Additional Operating Cost",
                "amount": additional_operating_cost_per_unit * flt((stock_entry.fg_completed_qty), stock_entry.precision('fg_completed_qty'))
            })
