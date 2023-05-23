// Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Sub Project Testing', {
	project: function (frm) {
		
		frappe.call({
			method: "erpnext.projects.doctype.sub_project_testing.sub_project_testing.sub_project",
			args: {
				project: frm.doc.project
			},
			callback: function (resp) {
				if (resp.message) {
					console.log("Inside if condition")
					console.log(resp.message)
					var options = [];
					for (var i = 0; i < resp.message.length; i++) {
						options.push({
							'label': resp.message[i].sub_project,
							
							'value': resp.message[i].sub_project
							
						});
						
						
					}
					frm.set_df_property('sub_project', 'options', options);
					frm.refresh_field('sub_project');
				}
			}
		})
	},
});

