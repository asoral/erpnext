// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Overtime', {
	from_date: function(frm){
		console.log(">>>>>>>>>>>>>>>>>>>>>>>>>>>>")
		frappe.call({
			method: "set_date",
			doc: frm.doc,
			callback: function(resp){
				if(resp.message){
					frm.set_value("to_date",resp.message)
				}
			}
	})
	}
});

frappe.ui.form.on("Overtime Details", {
	login: function(frm,cdt,cdn){
		var d = locals[cdt][cdn];
		frappe.call({
				method: "erpnext.nepali_date.get_converted_date",
				args: {
					date: d.login
				},
				callback: function(resp){
					if(resp.message){
						d.loginnepal = resp.message
						frm.refresh_field("loginnepal")
					}
				}
		})
		calculate_over_time(frm,cdt,cdn)
	},
	logout: function(frm,cdt,cdn){
		var d = locals[cdt][cdn];
		frappe.call({
			method: "erpnext.nepali_date.get_converted_date",
			args: {
				date: d.logout
			},
			callback: function(resp){
				if(resp.message){
					d.logoutnepal = resp.message
					frm.refresh_field("logoutnepal")
				}
			}
	})
		calculate_over_time(frm,cdt,cdn)

	}
})
 function calculate_over_time(frm,cdt,cdn){
	 let row = locals[cdt][cdn]
	 if(row.login && row.logout) {
		frappe.call({
			method: "get_overtime",
			doc: frm.doc,
			args: {
				login: row.login,
				logout: row.logout,
			},
			callback: function(resp){
				if(resp.message){
					console.log("msg is: ",resp.message)
					row.total_overtime = resp.message
					frm.refresh_field("total_overtime")
					
				}
			}
		})

	 }
 }
