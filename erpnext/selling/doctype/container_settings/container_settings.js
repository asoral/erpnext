// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Container Settings', {
	onload: function(frm) {
		cur_frm.set_query("oceanair_freight", function (doc) {
			var account_type = ["Tax", "Chargeable", "Income Account", "Expenses Included In Valuation"];
			return {
				query: "erpnext.controllers.queries.tax_account_query",
				filters: {
					"account_type": account_type,
					"company": doc.company
				}
			}
		});
		cur_frm.set_query("cargo_insurance", function (doc) {
			var account_type = ["Tax", "Chargeable", "Income Account", "Expenses Included In Valuation"];
			return {
				query: "erpnext.controllers.queries.tax_account_query",
				filters: {
					"account_type": account_type,
					"company": doc.company
				}
			}
		});
		cur_frm.set_query("customs_broker_fee", function (doc) {
			var account_type = ["Tax", "Chargeable", "Income Account", "Expenses Included In Valuation"];
			return {
				query: "erpnext.controllers.queries.tax_account_query",
				filters: {
					"account_type":[ "in",["Tax", "Chargeable", "Income Account", "Expenses Included In Valuation"]],
					"company": doc.company
				}
			}
		});
		cur_frm.set_query("incidentalmisc", function (doc) {
			var account_type = ["Tax", "Chargeable", "Income Account", "Expenses Included In Valuation"];
			return {
				query: "erpnext.controllers.queries.tax_account_query",
				filters: {
					"account_type": account_type,
					"company": doc.company
				}
			}
		});
		cur_frm.set_query("drayage", function (doc) {
			var account_type = ["Tax", "Chargeable", "Income Account", "Expenses Included In Valuation"];
			return {
				query: "erpnext.controllers.queries.tax_account_query",
				filters: {
					"account_type": account_type,
					"company": doc.company
				}
			}
		});
		cur_frm.set_query("warehousing", function (doc) {
			var account_type = ["Tax", "Chargeable", "Income Account", "Expenses Included In Valuation"];
			return {
				query: "erpnext.controllers.queries.tax_account_query",
				filters: {
					"account_type": account_type,
					"company": doc.company
				}
			}
		});
		cur_frm.set_query("bank_charge", function (doc) {
			var account_type = ["Tax", "Chargeable", "Income Account", "Expenses Included In Valuation"];
			return {
				query: "erpnext.controllers.queries.tax_account_query",
				filters: {
					"account_type": account_type,
					"company": doc.company
				}
			}
		});
		cur_frm.set_query("finance_charge", function (doc) {
			var account_type = ["Tax", "Chargeable", "Income Account", "Expenses Included In Valuation"];
			return {
				query: "erpnext.controllers.queries.tax_account_query",
				filters: {
					"account_type": account_type,
					"company": doc.company
				}
			}
		});
		

	}
});
