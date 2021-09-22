// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cost Calculator', {
	setup: function(frm) {
		frm.call({
			method:"get_bom",
			doc:frm.doc,
			callback: function(r) {
				frm.set_query("template_bom", function() {
					return {
						filters: [
							['name', 'in' , r.message]
						]
					}
				});
			}
			
		});

	},
	template_bom:function(frm){
		frm.clear_table("raw_material_items");
		frm.call({
			method:"get_all_value",
			doc:frm.doc,
			callback: function(r) {

			}
			
		});
	},
	qty:function(frm){
		frm.call({
			method:"get_qty",
			doc:frm.doc,
			callback: function(r) {
				
			}
			
		});
	},
	parameters:function(frm,cdt,cdn){
		// const row = locals[cdt][cdn];
		let fields = []
		frappe.db.get_doc("Item",frm.doc.item_code).then(e  => {
		if(e.has_variants==1){
		for(var i=0;i< e.attributes.length;i++){
			var fieldtype, desc;
			var row = e.attributes[i];
			if (row.numeric_values){
				fieldtype = "Float";
				desc = "Min Value: "+ row.from_range +" , Max Value: "+ row.to_range +", in Increments of: "+ row.increment
			}
			else {
				fieldtype = "Data";
				desc = ""
			}
			fields = fields.concat({
				"label": row.attribute,
				"fieldname": row.attribute,
				"fieldtype": fieldtype,
				"reqd": 0,
				"description": desc
			})
			
		}
		
		var d = new frappe.ui.Dialog({
			title: __('Parameters'),
			fields: fields
		});
		
		d.set_primary_action(__('Submit'), function() {
			var args = d.get_values();
			// const row = locals[cdt][cdn];
			console.log(args)
			var a=""
			for(var i in args){
				console.log(args[i])
				// console.log(args[i].value)
				a +=i+":"+args[i]+"\n"
			frm.doc.item_attribute = a;
			frm.refresh_field("item_attribute");
			
			}
			d.hide();
		});

		d.show();

		$.each(d.fields_dict, function(i, field) {

			if(field.df.fieldtype !== "Data") {
				return;
			}

			$(field.input_area).addClass("ui-front");

			var input = field.$input.get(0);
			input.awesomplete = new Awesomplete(input, {
				minChars: 0,
				maxItems: 99,
				autoFirst: true,
				list: [],
			});
			input.field = field;

			field.$input
				.on('input', function(e) {
					const row = locals[cdt][cdn];
					var term = e.target.value;
					frappe.call({
						method: "erpnext.stock.doctype.item.item.get_item_attribute",
						args: {
							parent: i,
							attribute_value: term
						},
						callback: function(r) {
							if (r.message) {
								e.target.awesomplete.list = r.message.map(function(d) { return d.attribute_value; });
							}
						}
					});
				})
				.on('focus', function(e) {
					$(e.target).val('').trigger('input');
				})
				.on("awesomplete-open", () => {
					let modal = field.$input.parents('.modal-dialog')[0];
					if (modal) {
						$(modal).removeClass("modal-dialog-scrollable");
					}
				})
				.on("awesomplete-close", () => {
					let modal = field.$input.parents('.modal-dialog')[0];
					if (modal) {
						$(modal).addClass("modal-dialog-scrollable");
					}
				});
		});
	}
	})
	},
	
	
});
frappe.ui.form.on('Bom Raw Material Item', {
	qty:function(frm,cdt,cdn){
		const row = locals[cdt][cdn];
		row.amount=row.qty*row.rate
		frappe.db.get_doc("Item",row.item_code).then(e  => {
		row.weight=row.qty*e.weight_per_unit
		})
	},
	rate:function(frm,cdt,cdn){
		const row = locals[cdt][cdn];
		row.amount=row.qty*row.rate
	},
	parameters:function(frm,cdt,cdn){
		const row = locals[cdt][cdn];
		let fields = []
		frappe.db.get_doc("Item",row.item_code).then(e  => {
		if(e.has_variants==1){
		for(var i=0;i< e.attributes.length;i++){
			var fieldtype, desc;
			var row = e.attributes[i];
			if (row.numeric_values){
				fieldtype = "Float";
				desc = "Min Value: "+ row.from_range +" , Max Value: "+ row.to_range +", in Increments of: "+ row.increment
			}
			else {
				fieldtype = "Data";
				desc = ""
			}
			fields = fields.concat({
				"label": row.attribute,
				"fieldname": row.attribute,
				"fieldtype": fieldtype,
				"reqd": 0,
				"description": desc
			})
			
		}
		
		var d = new frappe.ui.Dialog({
			title: __('Parameters'),
			fields: fields
		});
		
		d.set_primary_action(__('Submit'), function() {
			var args = d.get_values();
			const row = locals[cdt][cdn];
			console.log(args)
			var a=""
			for(var i in args){
				console.log(args[i])
				// console.log(args[i].value)
				a+=i+":"+args[i]+"\n"
			row.item_attributes = a;
			frm.refresh_field("raw_material_items");
			
			}
			d.hide();
		});

		d.show();

		$.each(d.fields_dict, function(i, field) {

			if(field.df.fieldtype !== "Data") {
				return;
			}

			$(field.input_area).addClass("ui-front");

			var input = field.$input.get(0);
			input.awesomplete = new Awesomplete(input, {
				minChars: 0,
				maxItems: 99,
				autoFirst: true,
				list: [],
			});
			input.field = field;

			field.$input
				.on('input', function(e) {
					const row = locals[cdt][cdn];
					var term = e.target.value;
					frappe.call({
						method: "erpnext.stock.doctype.item.item.get_item_attribute",
						args: {
							parent: i,
							attribute_value: term
						},
						callback: function(r) {
							if (r.message) {
								e.target.awesomplete.list = r.message.map(function(d) { return d.attribute_value; });
							}
						}
					});
				})
				.on('focus', function(e) {
					$(e.target).val('').trigger('input');
				})
				.on("awesomplete-open", () => {
					let modal = field.$input.parents('.modal-dialog')[0];
					if (modal) {
						$(modal).removeClass("modal-dialog-scrollable");
					}
				})
				.on("awesomplete-close", () => {
					let modal = field.$input.parents('.modal-dialog')[0];
					if (modal) {
						$(modal).addClass("modal-dialog-scrollable");
					}
				});
		});
	}
	})
	},

	
});
frappe.ui.form.on('Scrap Material Item', {
	qty:function(frm,cdt,cdn){
		const row = locals[cdt][cdn];
		row.amount=row.qty*row.rate
		frappe.db.get_doc("Item",row.item_code).then(e  => {
		row.weight=row.qty*e.weight_per_unit
		})
	},
	rate:function(frm,cdt,cdn){
		const row = locals[cdt][cdn];
		row.amount=row.qty*row.rate
	},
	parameters:function(frm,cdt,cdn){
		const row = locals[cdt][cdn];
		let fields = []
		frappe.db.get_doc("Item",row.item_code).then(e  => {
		if(e.has_variants==1){
		for(var i=0;i< e.attributes.length;i++){
			var fieldtype, desc;
			var row = e.attributes[i];
			if (row.numeric_values){
				fieldtype = "Float";
				desc = "Min Value: "+ row.from_range +" , Max Value: "+ row.to_range +", in Increments of: "+ row.increment
			}
			else {
				fieldtype = "Data";
				desc = ""
			}
			fields = fields.concat({
				"label": row.attribute,
				"fieldname": row.attribute,
				"fieldtype": fieldtype,
				"reqd": 0,
				"description": desc
			})
			
		}
		
		var d = new frappe.ui.Dialog({
			title: __('Parameters'),
			fields: fields
		});
		
		d.set_primary_action(__('Submit'), function() {
			var args = d.get_values();
			const row = locals[cdt][cdn];
			console.log(args)
			var a=""
			for(var i in args){
				console.log(args[i])
				// console.log(args[i].value)
				a+=i+":"+args[i]+"\n"
			row.item_attributes = a;
			frm.refresh_field("scrap_items");
			
			}
			d.hide();
		});

		d.show();

		$.each(d.fields_dict, function(i, field) {

			if(field.df.fieldtype !== "Data") {
				return;
			}

			$(field.input_area).addClass("ui-front");

			var input = field.$input.get(0);
			input.awesomplete = new Awesomplete(input, {
				minChars: 0,
				maxItems: 99,
				autoFirst: true,
				list: [],
			});
			input.field = field;

			field.$input
				.on('input', function(e) {
					const row = locals[cdt][cdn];
					var term = e.target.value;
					frappe.call({
						method: "erpnext.stock.doctype.item.item.get_item_attribute",
						args: {
							parent: i,
							attribute_value: term
						},
						callback: function(r) {
							if (r.message) {
								e.target.awesomplete.list = r.message.map(function(d) { return d.attribute_value; });
							}
						}
					});
				})
				.on('focus', function(e) {
					$(e.target).val('').trigger('input');
				})
				.on("awesomplete-open", () => {
					let modal = field.$input.parents('.modal-dialog')[0];
					if (modal) {
						$(modal).removeClass("modal-dialog-scrollable");
					}
				})
				.on("awesomplete-close", () => {
					let modal = field.$input.parents('.modal-dialog')[0];
					if (modal) {
						$(modal).addClass("modal-dialog-scrollable");
					}
				});
		});
	}
	})
	},
});
frappe.ui.form.on('Add Ons', {
	qty:function(frm,cdt,cdn){
		const row = locals[cdt][cdn];
		row.amount=row.qty*row.rate*row.factor
		// frappe.db.get_doc("Item",row.item_code).then(e  => {
		// row.weight=row.qty*e.weight_per_unit
		// })
	},
	rate:function(frm,cdt,cdn){
		const row = locals[cdt][cdn];
		row.amount=row.qty*row.rate*row.factor
	},
	factor:function(frm,cdt,cdn){
		const row = locals[cdt][cdn];
		row.amount=row.qty*row.rate*row.factor
	},

})