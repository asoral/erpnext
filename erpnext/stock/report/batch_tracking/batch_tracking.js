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
			// on_change: function () {
			// 	var company = frappe.query_report.get_filter_value('company');
			// 	if(company){
			// 		frappe.call({
			// 			'method': 'erpnext.stock.report.batch_tracking.batch_tracking.get_com_batch',
			// 			'async': false,
			// 			'args': {
			// 				'company' : company
			// 			},
			// 			'callback': function(res){
			// 				console.log(' this is res', res.message)
			// 				frappe.query_report.set_filter_value('batch',res.message)
			// 				// frappe.query_reports.refresh()
			// 			}
			// 		});
			// 		// frappe.query_report.set_filter_value('address_group',"");
			// 		// frappe.query_report.refresh()
			// 	}
			// 	frappe.query_report.refresh()
			// }
		},
		{
			fieldname: "batch",
			label: __("Batch"),
			fieldtype: "Link",
			options: "Batch",
			reqd: 1,
			// "get_query": function () {
			// 	var company = frappe.query_report.get_filter_value('company');
			// 	console.log(" this is com", company)
			// 	frappe.call({
			// 		'method': 'erpnext.stock.report.batch_tracking.batch_tracking.get_com_batch',
			// 		'async': false,
			// 		'args': {
			// 			'company' : company
			// 		},
			// 		'callback': function(res){
			// 			console.log(' this is res', res.message)
			// 			return res.message
			// 		}
			// 	});
			// },
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
