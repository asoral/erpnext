// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('State', {
	onload: function(frm) {

		},
		refresh: function(frm){
			frappe.call({
				method:"set_state",
				doc:frm.doc,
				callback: function(r) {
					return{
						filters:[
							[
								'state','in',r.message
							]
						]
					}
				}
		})
		}
		
});
