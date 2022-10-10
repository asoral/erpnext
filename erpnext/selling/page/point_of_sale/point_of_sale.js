frappe.provide('erpnext.PointOfSale');

frappe.pages['point-of-sale'].on_page_load = function(wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Point of Sale'),
		single_column: true
	});

	frappe.require('assets/js/point-of-sale.min.js', function() {
		wrapper.pos = new erpnext.PointOfSale.Controller(wrapper);
		window.cur_pos = wrapper.pos;
	});
};

frappe.pages['point-of-sale'].refresh = function(wrapper) {
	// const frm = me.events.get_frm();
	// console.log("941561561616",frm)
	if (document.scannerDetectionData) {
		onScan.detachFrom(document);
		wrapper.pos.wrapper.html("");
		wrapper.pos.check_opening_entry();
		console.log("12345789",wrapper)
	}
	// var b = this.pos_profile;
	// console.log('lllllllllllllllllll',b)
	// frappe.call({
	// 	method: "erpnext.selling.page.point_of_sale.pos.pole_clear",
	// 	args:{
	// 		"pos_profile":b
	// 	}
	// });
};
