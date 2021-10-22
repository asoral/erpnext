// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Container', {
	date_in_transit: function(frm) {
		if(frm.doc.date_in_transit && !frm.doc.warehouse_received_date){
			frm.doc.status="In Transit"
			refresh_field("status")
		}
		
	},
	warehouse_received_date:function(frm){
		if(frm.doc.warehouse_received_date){
			frm.doc.status="Moved To Warehouse"
			refresh_field("status")
		}
	},
	refresh:function(frm,cdt,cdn){
		frm.call({
			method:"set_updating_qty",
			doc:frm.doc,
			callback: function(r) {
				if(r.message){
					
				
					refresh_field("ventures_list")
				
				}
				
			}
			
		});
		if (frm.doc.docstatus===0 && frm.doc.import_type=="Outgoing") {
			frm.add_custom_button(__('Sales Order'),
				function() {
					erpnext.utils.map_current_doc({
						method: "erpnext.selling.doctype.sales_order.sales_order.get_container_item",
						source_doctype: "Sales Order Item",
						target: me.frm,
						args:{
							"container":frm.doc.name,
						},
						setters: [
							{
								label: "Sales Order",
								fieldname: "parent",
								fieldtype: "Link",
								options: "Sales Order",
								default: me.frm.doc.parent || undefined
							},
							{
								label: "Item",
								fieldname: "item_code",
								fieldtype: "Link",
								options: "Item",
								default: me.frm.doc.item_code || undefined
							},
							{
								label: "Qty Ordered",
								fieldname: "projected_qty",
								fieldtype: "Float",
								default: me.frm.doc.projected_qty || undefined
							},
							{
								label: "Venture Qty",
								fieldname: "qty",
								fieldtype: "Float",
								default: me.frm.doc.qty || undefined
							}
						],
						get_query_filters: {
							company: me.frm.doc.company,
							port: me.frm.doc.destination,
							docstatus: 1,
							

						}
					})
				
					
				}, __("Get Items From"));
		
		}
		if (frm.doc.docstatus===0 && frm.doc.import_type=="Incoming") {
			frm.add_custom_button(__('Purchase Order'),
				function() {
					erpnext.utils.map_current_doc({
						method: "erpnext.buying.doctype.purchase_order.purchase_order.get_container_item",
						source_doctype: "Purchase Order Item",
						target: me.frm,
						args:{
							"container":frm.doc.name,
						},
						setters: [
							{
								label: "Purchase Order",
								fieldname: "parent",
								fieldtype: "Link",
								options: "Purchase Order",
								default: me.frm.doc.parent || undefined
							},
							{
								label: "Item",
								fieldname: "item_code",
								fieldtype: "Link",
								options: "Item",
								default: me.frm.doc.item_code || undefined
							},
							{
								label: "Qty Ordered",
								fieldname: "actual_qty",
								fieldtype: "Float",
								default: me.frm.doc.projected_qty || undefined
							},
							{
								label: "Venture Qty",
								fieldname: "qty",
								fieldtype: "Float",
								default: me.frm.doc.qty || undefined
							}
						],
						get_query_filters: {
							company: me.frm.doc.company,
							port: me.frm.doc.destination,
							docstatus: 1,
						}
					})
				
					
				}, __("Get Items From"));
		
		}
		if (frm.doc.docstatus===1 && frm.doc.import_type=="Outgoing") {
			frm.add_custom_button(__('Delivery Note'),
			function() {
				frm.call({
					method:"delivery_note",
					doc:frm.doc,
					freeze: true,
					freeze_message: __("Creating Delivery Note"),
					callback: function(r) {
						if(r.message){
							
							frappe.msgprint("Delivery Note Created")
							
						}
						
					}
					
				});
				
		})
	}
	if (frm.doc.docstatus===1 && frm.doc.import_type=="Incoming") {
		frappe.model.get_value('Purchase Receipt', {"container":frm.doc.name},"name",
		function(e) {
		if(!e.name){
		frm.add_custom_button(__('Purchase Receipt'),
		function() {
			frm.call({
				method:"purchase_receipt",
				doc:frm.doc,
				freeze: true,
				freeze_message: __("Creating Purchase Receipt"),
				callback: function(r) {
					if(r.message){
						
						frappe.msgprint("Purchase Receipt Created")
						
					}
					
				}
				
			});
		
	})
	}
		})
	}
	if (frm.doc.docstatus===1 && frm.doc.import_type=="Incoming") {
		frappe.model.get_value('Purchase Receipt', {"container":frm.doc.name},"name",
		function(e) {
		if(e.name){
		frm.add_custom_button(__('Landed Cost Voucher'),
		function() {
			frm.call({
				method:"make_landed_cost_voucher",
				doc:frm.doc,
				freeze: true,
				freeze_message: __("Landed Cost Voucher"),
				callback: function(r) {
					if(r.message){
						
						frappe.msgprint("Landed Cost Voucher Created")
						
					}
					
				}
				
			});
		})
		}
		})
	}
	},
	setup:function(frm){
		cur_frm.set_query("custom_house_broker", function (doc) {
			return {
				filters: {
					'broker': 1,
					
				}
			}
		});
		cur_frm.set_query("container_against", function (doc) {
			return {
				filters: {
					"name": ["in", ["Sales Order", "Purchase Order"]],
					
				}
			}
		});

		frm.fields_dict['ventures_list'].grid.get_field('venture_to').get_query = function(doc) {
			return {
				filters: {
					"name": ["in", ["Customer", "Supplier"]],
				}
			}
		}
		frm.fields_dict['ventures_list'].grid.get_field('order_to').get_query = function(doc) {
			return {
				filters: {
					"name": ["in", ["Customer", "Supplier"]],
				}
			}
		}
	}
});

