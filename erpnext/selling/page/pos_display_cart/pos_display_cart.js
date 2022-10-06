frappe.provide('erpnext.POSDisplayCart');

frappe.pages['pos-display-cart'].on_page_load = function(wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: ('POS DIsplay Cart'),
		single_column: true
	});

	frappe.require('assets/js/pos-display-cart.min.js', function() {
		wrapper.pos = new erpnext.POSDisplayCart.Controller(wrapper);
		window.cur_pos = wrapper.pos;
	});
};

frappe.pages['pos-display-cart'].refresh = function(wrapper) {
	if (document.scannerDetectionData) {
		onScan.detachFrom(document);
		wrapper.pos.wrapper.html("");
		wrapper.pos.check_opening_entry();

	}
	// frappe.call({
	// 	method: "erpnext.selling.page.point_of_sale.pos.clear",
		
	// 	callback: function(r) {
			
	// 	}
	// });
};