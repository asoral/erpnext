// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('District', {
	refresh: function(frm) {

	},
	state: function(frm){
		let district = ['Pune','Satara']
		frm.set_query('district',()=>{
			return{
				filters:{
					state:'Maharashtra'
				}
			}
		})
	},
});
