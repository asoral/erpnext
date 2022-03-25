// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Batch Tracking"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			// default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "batch",
			label: __("Batch"),
			fieldtype: "Link",
			options: "Batch",
			reqd: 1,
			get_query: function (){
				return {
					"query": 'erpnext.stock.report.batch_tracking.batch_tracking.get_com_batch',
					"filters": {
						"company": frappe.query_report.get_filter_value('company')
					}

				}
			}

		},
		{
			fieldname: "level",
			label: __("Level"),
			fieldtype: "Int",
			default: 1,
			reqd: 1
		},
		{
			fieldname: "workorder",
			label: __("Workorder"),
			fieldtype: "Link",
			options: "Work Order",
		},
	]
};
