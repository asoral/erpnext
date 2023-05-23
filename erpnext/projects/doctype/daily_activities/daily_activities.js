

frappe.ui.form.on("Daily Activities", {
    refresh: function(frm) {
        frm.add_custom_button(__("Add Child Table"), function() {
            // create a new section
            var section = frm.add_child("form_layout", frappe.ui.form.Layout);
            section.add_class("new-section");
            section.add_label("Child Table");
            section.add_field({
                "fieldname": "child_table",
                "label": "Child Table",
                "fieldtype": "Table",
                "parent": section.name
            }).df.options = "Daily Activities List";
            frm.refresh_field("form_layout");
        });
    }
});