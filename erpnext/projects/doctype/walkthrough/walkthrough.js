// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Walkthrough', {
	refresh: function(frm) {
				cur_frm.fields_dict['item_details'].grid.get_field('dimension_uom').get_query = function(doc, cdt, cdn) {
					return {
						filters: {
							"dimension":1
						}
								   
						
					}
				}
				frm.refresh_field("item_details")
				cur_frm.fields_dict['item_details'].grid.get_field('weight_uom').get_query = function(doc, cdt, cdn) {
					return {
						filters: {
							"weight":1
						}
								   
						
					}
				}
				frm.refresh_field("item_details")
				
			}	
});

frappe.ui.form.on('Walkthrough Items', {
	create_item: function(frm,cdt,cdn) {
		let wchild=locals[cdt][cdn]
		frappe.new_doc("Item",{"item_code":wchild.item_name,"item_name":wchild.item_name,"item_group":wchild.item_group,"qty":wchild.qty,"length":wchild.length,"width":wchild.width,"height":wchild.height,"item_image":wchild.item_image,"dimension_uom":wchild.dimension_uom})
		.then(function(){
			cur_frm.add_child("customer_items", 
		{"customer_name":frm.doc.customer,"customer_group":frm.doc.customer_group,"ref_code":wchild.item_name})
		cur_frm.refresh_field("customer_items")
		} ,
	)},
});


