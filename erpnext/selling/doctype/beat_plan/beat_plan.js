// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Beat Plan', {
	setup: function(frm) {
		frm.clear_table("beat_plan_items")
		frm.set_query('sales_person', () => {
			return {
				filters: {
					parent_sales_person: frm.doc.sales_manager
				}
			}
		})
		
		frm.set_query('beat_id',()=>{
			return{
				filters:{
					docstatus :1,
				}
			}
		})
	},
	refresh : function(frm){
		if(frm.doc.status != 'Completed'){
		frm.add_custom_button('Complete', () => {
			frm.set_value('status','Completed');
	})}
	},
	sales_person: function(frm){
		frappe.call({
			    method: "fill_child_t",
				doc:frm.doc,
				callback: function(r) {
			       frm.refresh_field("beat_plan_items")
			    }
				
			});
	}
	
	})	
