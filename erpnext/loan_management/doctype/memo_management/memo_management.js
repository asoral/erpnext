// Copyright (c) 2022, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

var arr=[];
var counter = 0;
frappe.ui.form.on('MEMO Management', {
	// first_reveiwerapprover: function(frm){
	// 	let a=frm.doc.first_reveiwerapprover
	// 	if(frappe.user_roles.includes("RM")){
	// 		frm.set_value('workflow_state', a)
	// 	}

		
	// },
	// refresh: function(frm){
	// 	if (!frm.is_new()) {
    //         frm.disable_save();
    //     }
	// }
	// ,
	before_save:function(frm){
		let a= frm.doc.second_reveiwerapprover;
		let b = frm.doc.third_reveiwerapprover;
		let c = frm.doc.first_reveiwerapprover;
		console.log(a);
		
		
		if(frm.doc.workflow_state=="" || frm.doc.workflow_state==null ){
			frm.set_value('workflow_state', c)

		}
		else if(frm.doc.first_reveiwerapprover==frm.doc.workflow_state ){
			frm.set_value('workflow_state', a)

		}
		else if(frm.doc.second_reveiwerapprover==frm.doc.workflow_state){
			frm.set_value('workflow_state', b)
		}
		
	}
	// before_save: function(frm) {
	// 		let a=frm.doc.first_reveiwerapprover
	// 		let b=frm.doc.second_reveiwerapprover
	// 		let c=frm.doc.third_reveiwerapprover
	// 		let d=frm.doc.fourth_reveiwerapprover
	// 		let e=frm.doc.fifth_reveiwerapprover
	// 		const all = [a,b,c,d,e].join(',');
	// 		let arr1 = all.split(',');
	// 		arr.push(arr1);
	// 		console.log(arr);
	// 	},
	// refresh: function(frm){
	// 	if (frappe.user_roles.includes('RM')) {
	// 		frm.disable_save();
	// 	} else {
	// 		frm.enable_save();
	// 	}

	// },
	
	// before_save : function(frm) {
	// 	if(frm.doc.first_reveiwerapprover == 'BM')
	// 		frappe.set_value('workflow_state', "BM")
	// },


	// first_reveiwerapprover: function(frm) {
	// 	let a=frm.doc.first_reveiwerapprover
	// 	arr.push(a);
	// 	console.log(arr);
	// },
	// second_reveiwerapprover: function(frm) {
	// 	arr.append(frm.second_reveiwerapprover);
	// 	console.log(arr);
	// },
	// third_reveiwerapprover: function(frm) {
	// 	arr.append(frm.third_reveiwerapprover);
	// 	console.log(arr);
	// },
	// fourth_reveiwerapprover: function(frm) {
	// 	arr.append(frm.fourth_reveiwerapprover);
	// 	console.log(arr);
	// },
	// fifth_reveiwerapprover: function(frm) {
	// 	arr.append(frm.fifth_reveiwerapprover);
	// 	console.log(arr);
	// },
	
});

frappe.ui.form.on('Reveiw List', {
	table_9_add: function (frm, cdt, cdn) {
	    let full_name= frappe.session.user_fullname;
		let role = frappe.user_roles;
		console.log(role);
	    console.log(full_name);
		//var d = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "username", full_name);
		frappe.model.set_value(cdt, cdn, "position", role[0]);
		//d.total_fmv=d.fmv_of_land+d.fmv_of_building
		frm.refresh_field("username");
		frm.refresh_field("position");
	}
});
