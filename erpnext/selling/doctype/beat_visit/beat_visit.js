// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Beat Visit', {
	setup: function(frm) {
		frm.set_query('beat_plan',()=>{
			return{
				filters:{
					'beat_id':frm.doc.beat,
					'docstatus':1
				}
			}
		}),
		frm.set_query('beat',()=>{
			return{
				filters:{
					'docstatus':1
				}
			}
		}),
		frm.set_query('sales_person',()=>{
			return{
				filters:{
					'parent_sales_person':frm.doc.sales_manager
				}
			}
		}),
		frm.set_query('visit_territory',()=>{
			return{
				filters:{
					'parent_territory':frm.doc.parent_territory
				}
			}
		}),
		frm.set_query('customer',()=>{
			return{
				filters:{
					'territory':frm.doc.visit_territory,
					'is_a_secondary_cust':1
				}
			}
		}),
		frm.set_query('item_group',()=>{
			return{
				filters:{
					'is_group':0
				}
			}
		}),
		frm.set_query("item_code", "visit_order", function(doc, cdt, cdn) {
			return {
				filters: {
					'is_sales_item': 1
				}
			};
		});
		
	},
	customer:function(frm){
		frappe.call({
            method: "cust_stats", //dotted path to server method
			doc:frm.doc,
			callback: function(r) {
               frm.refresh_field("last_visit_date_")
			   frm.refresh_field("last_order_date_")
			   frm.refresh_field('last_item_ordered')
			   frm.refresh_field('target_quantity_')
			   frm.refresh_field('target_amount_')
			   frm.refresh_field('monthly_potential')
            }
			
        });
	
		
	},
	date: function(frm){
		frm.refresh_field("visit_territory")
		frappe.call({
            method: "get_tt", //dotted path to server method
			doc:frm.doc,
			callback: function(r) {
               frm.refresh_field("visit_territory")
            }
			
        });
	
	},
	
	item_group: function(frm){
		if(frm.doc.item_group){	
		frappe.call({
			method: "fill_vo",
			doc:frm.doc,
			callback: function(r){
				frm.refresh_field("visit_order")
			}
		})
		}
	},
	before_save: function(frm){
		if(frm.doc.price_list){
		frappe.call({
			method: "fill_vg",
			doc:frm.doc,
			callback: function(r){
				frm.refresh_field("visit_gift")
			}
		})
	
	}
	},
	payment_mode : function(frm){
		if(frm.doc.payment_mode){
			frm.toggle_display(['ref_no', 'ref_date'], frm.doc.payment_mode === 'Cheque');
			frm.toggle_reqd('ref_no', frm.doc.payment_mode === 'Cheque');
			frm.toggle_reqd('ref_no', frm.doc.payment_mode === 'Bank Draft');
			frm.toggle_reqd('ref_date', frm.doc.payment_mode === 'Cheque');
			frm.toggle_reqd('ref_date', frm.doc.payment_mode === 'Bank Draft');

		}
	},
	pymt: function(frm){
		frm.refresh_field('pymt')
		if(frm.doc.pymt){
			frm.toggle_display(['payment_mode'],frm.doc.pymt>0);
			// frm.toggle_reqd('payment_mode',frm.doc.pymt>0);
			frm.set_df_property('payment_mode', 'reqd', 1)
		}
		else{frm.set_df_property('payment_mode', 'hidden', 1)
			frm.set_df_property('payment_mode', 'reqd', 0)}
	}
	
});

frappe.ui.form.on('Visit Order', {
	qty: function(frm,cdt,cdn){
		var child = locals[cdt][cdn];
		if(child.qty){
			frappe.model.set_value(cdt,cdn,"amount",child.rate*child.qty)
		}
		frm.refresh_field('amount')
	}
});

frappe.ui.form.on('Visit Gift', {
	qty: function(frm,cdt,cdn){
		var child = locals[cdt][cdn];
		if(child.rate){
			frappe.model.set_value(cdt,cdn,"amount",child.rate*child.qty)
		}
		frm.refresh_field('amount')
	}
});
