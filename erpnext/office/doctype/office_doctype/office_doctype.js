// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('OFFICE Doctype', {
	refresh: function(frm) {
		console.log("======= inside Refresh =======")

		// New sheet button 
		frm.add_custom_button(__("New Sheet"), function () {
			console.log("======= inside button New Sheet =======")
			// Add wizard to select linked doctype

			let d = new frappe.ui.Dialog({
				
				title: 'Select Template',
				fields: [
					{ 
						label: 'Doctype',
						fieldname: 'doctype',
						fieldtype: 'Link',
						options: "DocType"
					},
					{
						label: 'First Name',
						fieldname: 'first_name',
						fieldtype: 'Data',
						read_only: 1,
						default : frm.doc.first_name
					},
				],
				primary_action_label: 'Create Sheet',
				primary_action(values) {
					console.log(values);
					d.hide();
				}
			})
			d.show();
		});
	}
});
