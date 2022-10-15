// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.provide("erpnext.accounts.dimensions");

frappe.ui.form.on('Loyalty Program', {
	setup: function(frm) {
		var help_content =
			`<table class="table table-bordered" style="background-color: #f9f9f9;">
				<tr><td>
					<h4>
						<i class="fa fa-hand-right"></i>
						${__('Notes')}
					</h4>
					<ul>
						<li>
							${__("Loyalty Points will be calculated from the spent done (via the Sales Invoice), based on collection factor mentioned.")}
						</li>
						<li>
							${__("There can be multiple tiered collection factor based on the total spent. But the conversion factor for redemption will always be same for all the tier.")}
						</li>
						<li>
							${__("In the case of multi-tier program, Customers will be auto assigned to the concerned tier as per their spent")}
						</li>
						<li>
							${__("If unlimited expiry for the Loyalty Points, keep the Expiry Duration empty or 0.")}
						</li>
						<li>
							${__("If Auto Opt In is checked, then the customers will be automatically linked with the concerned Loyalty Program (on save)")}
						</li>
						<li>
							${__("One customer can be part of only single Loyalty Program.")}
						</li>
					</ul>
				</td></tr>
			</table>`;
		set_field_options("loyalty_program_help", help_content);
	},

	onload: function(frm,cdt,cdn) {
		frm.set_query("expense_account", function(doc) {
			return {
				filters: {
					"root_type": "Expense",
					'is_group': 0,
					'company': doc.company
				}
			};
		});

		frm.set_value("company", frappe.defaults.get_user_default("Company"));
		erpnext.accounts.dimensions.setup_dimension_filters(frm, frm.doctype);

		frm.fields_dict["row_wise_loyalty_point"].grid.get_field("document_type").get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			return {    
				filters:{
					name:["in",["Item","Item Group"]]
				}
			}
		}



		if(cur_frm.doc.doctype_name="POS Invoice"){		
		var fields1=[]
		var labels=[]
		frappe.call({
			method:"grandhyper.grandhyper.doctype.pos_invoice_wise_loyalty_points.pos_invoice_wise_loyalty_points.get_list",
			args:{
				"docname":"POS Invoice"
			},
			callback:function(r){
				if(r.message){
					fields1.push(r.message)
					labels=Object.keys(fields1[0])
					frm.fields_dict.pos_invoice_wise_loyalty_point.grid.update_docfield_property(
						'pos_invoice',
						'options',
						[""].concat(labels)
						);
				}
			}		
		})
		frappe.ui.form.on("POS Invoice Wise Loyalty Points",{
			pos_invoice:function(frm,cdt,cdn){
				const child=locals[cdt][cdn];
		const fields2=[]
		frappe.call({
			method:"grandhyper.grandhyper.doctype.pos_invoice_wise_loyalty_points.pos_invoice_wise_loyalty_points.get_list",
			args:{
				"docname":"POS Invoice"
			},
			callback:function(r){
				if(r.message){
					fields2.push(r.message)
					for (const [key, value] of Object.entries(fields2[0])) {
						if(child.pos_invoice == key){
							frappe.model.set_value(cdt,cdn,"field_name",value[0])
							frappe.model.set_value(cdt,cdn,"field_type",value[1])
						}
					  }
					  
				}
			}
			
		})
			}
		}
		
)}

	},

	refresh: function(frm) {
		if (frm.doc.loyalty_program_type === "Single Tier Program" && frm.doc.collection_rules.length > 1) {
			frappe.throw(__("Please select the Multiple Tier Program type for more than one collection rules."));
		}
	},

	company: function(frm) {
		erpnext.accounts.dimensions.update_dimension(frm, frm.doctype);
	}
});
