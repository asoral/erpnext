frappe.pages['googlesheet'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Sheets',
		single_column: true
	});
}