// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
frappe.ui.form.on('LOS', {
	//calculate child table row amount
	setup: function (frm) {
		frm.total = function (frm) {
			let total = 0;
			frm.doc.cicl.forEach(d => {
				total = total + d.amount;
			})
			let new_total = total
			frm.set_value("total_amount", new_total)
		}

	},

	"land_and_buildings": function (frm) {

		frm.set_value("total_assets", frm.doc.land_and_buildings + frm.doc.movable_assets + frm.doc.share_and_debenture + frm.doc.others);
	},
	"movable_assets": function (frm) {
		frm.set_value("total_assets", frm.doc.land_and_buildings + frm.doc.movable_assets + frm.doc.share_and_debenture + frm.doc.others);
	},
	"share_and_debenture": function (frm) {
		frm.set_value("total_assets", frm.doc.land_and_buildings + frm.doc.movable_assets + frm.doc.share_and_debenture + frm.doc.others);
	},
	"others": function (frm) {
		frm.set_value("total_assets", frm.doc.land_and_buildings + frm.doc.movable_assets + frm.doc.share_and_debenture + frm.doc.others);
	},
	"other_loan": function (frm) {
		frm.set_value("total_liabilities", frm.doc.other_loan + frm.doc.other_liability);
	},
	"other_liability": function (frm) {
		frm.set_value("total_liabilities", frm.doc.other_loan + frm.doc.other_liability);
	},
	"total_liabilities": function (frm) {
		frm.set_value("net_worth", frm.doc.total_assets - frm.doc.total_liabilities);
	},

	"salary_income": function (frm) {
		frm.set_value("total_income", frm.doc.salary_income + frm.doc.business_income + frm.doc.rental_income + frm.doc.profession_income + frm.doc.agro_income);
	},
	"salary_income": function (frm) {
		frm.set_value("total_income", frm.doc.salary_income + frm.doc.business_income + frm.doc.rental_income + frm.doc.profession_income + frm.doc.agro_income);
	},
	"business_income": function (frm) {
		frm.set_value("total_income", frm.doc.salary_income + frm.doc.business_income + frm.doc.rental_income + frm.doc.profession_income + frm.doc.agro_income);
	},
	"rental_income": function (frm) {
		frm.set_value("total_income", frm.doc.salary_income + frm.doc.business_income + frm.doc.rental_income + frm.doc.profession_income + frm.doc.agro_income);
	},
	"profession_income": function (frm) {
		frm.set_value("total_income", frm.doc.salary_income + frm.doc.business_income + frm.doc.rental_income + frm.doc.profession_income + frm.doc.agro_income);
	},
	"agro_income": function (frm) {
		frm.set_value("total_income", frm.doc.salary_income + frm.doc.business_income + frm.doc.rental_income + frm.doc.profession_income + frm.doc.agro_income);
	},

	"household_expenses": function (frm) {
		frm.set_value("total_expenses", frm.doc.household_expenses + frm.doc.rental_expenses + frm.doc.transportation_expenses + frm.doc.other_bank_emi + frm.doc.taxmiscelleneous_expenses);
	},
	"rental_expenses": function (frm) {
		frm.set_value("total_expenses", frm.doc.household_expenses + frm.doc.rental_expenses + frm.doc.transportation_expenses + frm.doc.other_bank_emi + frm.doc.taxmiscelleneous_expenses);
	},
	"transportation_expenses": function (frm) {
		frm.set_value("total_expenses", frm.doc.household_expenses + frm.doc.rental_expenses + frm.doc.transportation_expenses + frm.doc.other_bank_emi + frm.doc.taxmiscelleneous_expenses);
	},
	"other_bank_emi": function (frm) {
		frm.set_value("total_expenses", frm.doc.household_expenses + frm.doc.rental_expenses + frm.doc.transportation_expenses + frm.doc.other_bank_emi + frm.doc.taxmiscelleneous_expenses);
	},
	"taxmiscelleneous_expenses": function (frm) {
		frm.set_value("total_expenses", frm.doc.household_expenses + frm.doc.rental_expenses + frm.doc.transportation_expenses + frm.doc.other_bank_emi + frm.doc.taxmiscelleneous_expenses);
	},

	"total_expenses": function (frm) {
		frm.set_value("net_disposable_income", frm.doc.total_income - frm.doc.total_expenses);
	},
	"total_income": function (frm) {
		frm.set_value("net_disposable_income", frm.doc.total_income - frm.doc.total_expenses);
	},

	refresh: function (cur_frm) {
		let workflow = cur_frm.doc.workflow_state;
		cur_frm.set_df_property("lead_information_section", "hidden", 1);
		cur_frm.set_df_property("approval_chain_section", "hidden", 1);
		cur_frm.set_df_property("personal_detail_section", "hidden", 1);
		cur_frm.set_df_property("net_worth_details", "hidden", 1);
		cur_frm.set_df_property("income_expenses", "hidden", 1);
		cur_frm.set_df_property("limit_summary_facility_utilz", "hidden", 1);
		cur_frm.set_df_property("security_details_section", "hidden", 1);
		cur_frm.set_df_property("cicl_section", "hidden", 1);
		cur_frm.set_df_property("waiver_section", "hidden", 1);
		cur_frm.set_df_property("valuation_detail_section", "hidden", 1);
		cur_frm.set_df_property("valuation_details_section", "hidden", 1);
		cur_frm.set_df_property("disbursement_section", "hidden", 1);

		if (frappe.user_roles.includes("RM") && (workflow == "Draft"  || workflow == "CICL"|| workflow == "Review From RM")) {
			cur_frm.set_df_property("lead_information_section", "hidden", 0);
			cur_frm.set_df_property("personal_detail_section", "hidden", 0);
			cur_frm.set_df_property("approval_chain_section", "hidden", 0);
		}

		else if (frappe.user_roles.includes("CICL")) {
			cur_frm.set_df_property("lead_information_section", "hidden", 0);
			cur_frm.set_df_property("personal_detail_section", "hidden", 0);
			cur_frm.set_df_property("cicl_section", "hidden", 0);
		}

		else if (frappe.user_roles.includes("RM") && workflow == "Pending RM Approval") {
			cur_frm.set_df_property("lead_information_section", "hidden", 0);
			cur_frm.set_df_property("personal_detail_section", "hidden", 0);
			cur_frm.set_df_property("net_worth_details", "hidden", 0);
			cur_frm.set_df_property("income_expenses", "hidden", 0);
			cur_frm.set_df_property("limit_summary_facility_utilz", "hidden", 0);
			cur_frm.set_df_property("security_details_section", "hidden", 0);
			cur_frm.set_df_property("cicl_section", "hidden", 0);
			cur_frm.set_df_property("waiver_section", "hidden", 0);
			cur_frm.set_df_property("valuation_detail_section", "hidden", 0);
			cur_frm.set_df_property("valuation_details_section", "hidden", 0);
			cur_frm.set_df_property("disbursement_section", "hidden", 0);
		}
		else {
			cur_frm.set_df_property("approval_chain_section", "hidden", 0);
			cur_frm.set_df_property("lead_information_section", "hidden", 0);
			cur_frm.set_df_property("personal_detail_section", "hidden", 0);
			cur_frm.set_df_property("net_worth_details", "hidden", 0);
			cur_frm.set_df_property("income_expenses", "hidden", 0);
			cur_frm.set_df_property("limit_summary_facility_utilz", "hidden", 0);
			cur_frm.set_df_property("security_details_section", "hidden", 0);
			cur_frm.set_df_property("cicl_section", "hidden", 0);
			cur_frm.set_df_property("waiver_section", "hidden", 0);
			cur_frm.set_df_property("valuation_detail_section", "hidden", 0);
			cur_frm.set_df_property("valuation_details_section", "hidden", 0);
			cur_frm.set_df_property("disbursement_section", "hidden", 0);
		}

	},
});


//calculate child table row amount
frappe.ui.form.on("CICL Table", {
	"amount": function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		frm.total(frm);
	},
	cicl_remove: function (frm, cdt, cdn) {
		frm.total(frm)
	},

});

frappe.ui.form.on("Security Details", {
	fmv_of_land: function (frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "total_fmv", d.fmv_of_land + d.fmv_of_building);
		//d.total_fmv=d.fmv_of_land+d.fmv_of_building
		frm.refresh_field("total_fmv")
	},
	fmv_of_building: function (frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "total_fmv", d.fmv_of_land + d.fmv_of_building);
		//d.total_fmv=d.fmv_of_land+d.fmv_of_building
		frm.refresh_field("total_fmv")
	},
	total_fmv: function (frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "distressed_valuedv", ((d.total_fmv * d.collateral_distressed) / 100));
		//d.total_fmv=d.fmv_of_land+d.fmv_of_building
		frm.refresh_field("distressed_valuedv")
	},
	collateral_distressed: function (frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "distressed_valuedv", ((d.total_fmv * d.collateral_distressed) / 100));
		//d.total_fmv=d.fmv_of_land+d.fmv_of_building
		frm.refresh_field("distressed_valuedv")
	},
	district: function (frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		frappe.call({
			method: "erpnext.district_list.get_municipality",
			args: {
				district: d.district
			},
			callback: function (resp) {
				if (resp.message) {
					frm.fields_dict.security_details.grid.update_docfield_property("vdcmunicipality", "options", [""].concat(resp.message));
					frm.refresh_field("vdcmunicipality")
				}
			}
		})
	},


});

frappe.ui.form.on("Application Guarantor Details", {
	district: function (frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		frappe.call({
			method: "erpnext.district_list.get_municipality",
			args: {
				district: d.district
			},
			callback: function (resp) {
				if (resp.message) {
					frm.fields_dict.applicationguarantor_details.grid.update_docfield_property("vdc_municipality", "options", [""].concat(resp.message));
					frm.refresh_field("vdc_municipality")
				}
			}
		})
	},


});
frappe.ui.form.on("Security Details", {
	district: function (frm, cdt, cdn) {
		var d = locals[cdt][cdn];
		frappe.call({
			method: "erpnext.district_list.get_municipality",
			args: {
				district: d.district
			},
			callback: function (resp) {
				if (resp.message) {
					frm.fields_dict.security_details.grid.update_docfield_property("vdcmunicipality", "options", [""].concat(resp.message));
					frm.refresh_field("vdcmunicipality")
				}
			}
		})
	},
});


