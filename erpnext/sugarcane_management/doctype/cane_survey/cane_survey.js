// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cane Survey', {

	l_name : function (frm) {
		let fname = frm.doc.f_name;
		let mname = frm.doc.m_name;
		let lname = frm.doc.l_name;
		let full = fname.concat(" "+mname+" "+lname);
		frm.set_value('full_name',full)
		}
	




	
});
