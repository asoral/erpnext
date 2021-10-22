// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Container Type', {
	internal_length: function(frm) {
		var a = frm.doc.internal_length
		var b=	frm.doc.internal_width
		var c=	frm.doc.internal_height
		frm.doc.max_cbm= a*b*c
		refresh_field("max_cbm")
	},
	internal_width: function(frm) {
		var a = frm.doc.internal_length
		var b=	frm.doc.internal_width
		var c=	frm.doc.internal_height
		frm.doc.max_cbm= a*b*c
		refresh_field("max_cbm")
	},
	internal_height: function(frm) {
		var a = frm.doc.internal_length
		var b=	frm.doc.internal_width
		var c=	frm.doc.internal_height
		frm.doc.max_cbm= a*b*c
		refresh_field("max_cbm")
	}
	
});
