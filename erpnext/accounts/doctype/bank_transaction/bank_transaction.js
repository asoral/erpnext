// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on("Bank Transaction", {
	onload(frm) {
		frm.set_query("payment_document", "payment_entries", function () {
			return {
				filters: {
					name: [
						"in",
						[
							"Payment Entry",
							"Journal Entry",
							"Sales Invoice",
							"Purchase Invoice",
							"Expense Claim",
						],
					],
				},
			};
		});
	},
	bank_account: function (frm) {
		set_bank_statement_filter(frm);
	},

	setup: function (frm) {
		frm.set_query("party_type", function () {
			return {
				filters: {
					name: ["in", Object.keys(frappe.boot.party_account_types)],
				},
			};
		});
	},

	before_submitt:function(frm){
		var document_types = ['payment_entry','journal_entry']
		frm.clear_table("payment_entries");
		frappe.call({
				method:
					"erpnext.accounts.doctype.bank_transaction.bank_transaction.get_linked_payments",
				args: {
					bank_transaction_name: frm.doc.name,
					document_types: document_types,
				},
				callback: function (result) {
					console.log("------result",result.message)
					var data = result.message;
					var data_len = 0;
					for(var row in data){
						data_len += 1;
						var child = frm.add_child('payment_entries');
						child.payment_document = data[row][1];
						child.payment_entry = data[row][2];
						child.allocated_amount = data[row][3];
					}

					frm.refresh_field("payment_entries");
					if(data_len > 1){
						frm.clear_table("payment_entries");
						frm.refresh_field("payment_entries")

					}

				},
			});
	}
});

frappe.ui.form.on("Bank Transaction Payments", {
	payment_entries_remove: function (frm, cdt, cdn) {
		update_clearance_date(frm, cdt, cdn);
	},
});

const update_clearance_date = (frm, cdt, cdn) => {
	if (frm.doc.docstatus === 1) {
		frappe
			.xcall(
				"erpnext.accounts.doctype.bank_transaction.bank_transaction.unclear_reference_payment",
				{ doctype: cdt, docname: cdn }
			)
			.then((e) => {
				if (e == "success") {
					frappe.show_alert({
						message: __("Document {0} successfully uncleared", [e]),
						indicator: "green",
					});
				}
			});
	}
};

function set_bank_statement_filter(frm) {
	frm.set_query("bank_statement", function () {
		return {
			filters: {
				bank_account: frm.doc.bank_account,
			},
		};
	});
}
