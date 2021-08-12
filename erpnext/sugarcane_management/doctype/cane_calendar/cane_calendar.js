// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cane Calendar', {
	w_date : function(frm){
		frm.set_query('cwi',() => {
			return {
				filters:{
					weight_date: frm.doc.w_date
				}
			}
		})
	}
	
});
