// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Container Settings', {
	onload: function(frm) {
		frm.call({
			method:"account_query",
			doc:frm.doc,
			callback: function(r) {
				if(r.message){
					
					cur_frm.set_query("oceanair_freight", function (doc) {
						return {
							filters: {
								"name": ["in", r.message],
							}
						}
					});
					cur_frm.set_query("cargo_insurance", function (doc) {
						return {
							filters: {
								"name": ["in", r.message],
							}
						}
					});
					cur_frm.set_query("customs_broker_fee", function (doc) {
						return {
							filters: {
								"name": ["in", r.message],
							}
						}
					});
					cur_frm.set_query("incidentalmisc", function (doc) {
						return {
							filters: {
								"name": ["in", r.message],
							}
						}
					});
					cur_frm.set_query("drayage", function (doc) {
						return {
							filters: {
								"name": ["in", r.message],
							}
						}
					});
					cur_frm.set_query("warehousing", function (doc) {
						return {
							filters: {
								"name": ["in", r.message],
							}
						}
					});
					cur_frm.set_query("bank_charge", function (doc) {
						return {
							filters: {
								"name": ["in", r.message],
							}
						}
					});
					cur_frm.set_query("finance_charge", function (doc) {
						return {
							filters: {
								"name": ["in", r.message],
							}
						}
					});
				
				}
				
			}
			
		});
	}
});
