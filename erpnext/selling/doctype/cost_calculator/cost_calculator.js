// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Cost Calculator', {
	setup: function(frm) {
		frm.call({
			method:"get_bom",
			freeze: true,
			freeze_message: __("Fetching Bom Items..."),
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
		frm.set_query("quotation_to", function() {
			return{
				"filters": {
					"name": ["in", ["Customer", "Lead"]],
				}
			}
		});
		frm.set_query("item_code", "add_ons", function(doc, cdt, cdn) {
			var row = locals[cdt][cdn];
			return {
				filters: {
					"is_stock_item": 0,
					"has_variants":0
				}
			}
		});
		frm.set_query("bom_no", "raw_material_items", function(doc, cdt, cdn) {
			var row = locals[cdt][cdn];
			return {
				filters: {
					"item": row.item_code
					
				}
			}
		});
		frm.set_query("bom_no", "add_ons", function(doc, cdt, cdn) {
			var row = locals[cdt][cdn];
			return {
				filters: {
					"item": row.item_code
					
				}
			}
		});

	},
	refresh:function(frm){
		if(frm.doc.docstatus==1){
			cur_frm.add_custom_button(__('Quotation'), function() {
				frm.call({
					method:"make_quotation",
					doc:frm.doc,
					callback: function(r) {
						msgprint("Quotation Created!!!")
					}
					
				});
			}, __('Create'))
			}
		if(frm.doc.docstatus==1){
			cur_frm.add_custom_button(__('BOM'), function() {
				frm.call({
					method:"make_bom",
					doc:frm.doc,
					callback: function(r) {
						msgprint("Bom Created!!!")
					}
					
				});
			}, __('Create'))
			}
		// doctype = doc.quotation_to == 'Customer' ? 'Customer':'Lead';
		// frappe.dynamic_link = {doc: this.frm.doc, fieldname: 'party_name', doctype: doctype}

		frm.set_query("price_list", function() {
			return {
				filters: {
					"buying":1
				}
			}
		});
		
	},
	set_dynamic_field_label: function(){
		if (this.frm.doc.quotation_to == "Customer")
		{
			this.frm.set_df_property("party_name", "label", "Customer");
			this.frm.fields_dict.party_name.get_query = null;
		}

		if (this.frm.doc.quotation_to == "Lead")
		{
			this.frm.set_df_property("party_name", "label", "Lead");

			this.frm.fields_dict.party_name.get_query = function() {
				return{	query: "erpnext.controllers.queries.lead_query" }
			}
		}
	},

	currency:function(frm){
		if(frm.doc.currency!="INR"){
			frm.doc.conversion_rate=0
			frm.doc.plc_conversion_rate=0
			frm.call({
				method:"set_price_list_currency",
				freeze: true,
				freeze_message: __("Fetching Currency Rates..."),
				doc:frm.doc,
				callback: function(r) {
					
				}
				
			});
		}
	},
	price_list:function(frm){
		
		frm.doc.conversion_rate=0
		frm.doc.plc_conversion_rate=0
		frm.call({
			method:"set_price_list_currency",
			freeze: true,
			freeze_message: __("Fetching Currency Rates..."),
			doc:frm.doc,
			callback: function(r) {
				
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
				
				a+="'"+i+"'"+":"+"'"+args[i]+"'"+","+"\n"
				frm.doc.item_attribute = a;
			}
			frm.refresh_field("item_attribute");
			frappe.call({
				method: "set_value",
				doc:frm.doc,
				callback: function(r) {
					if (r.message) {
						frm.refresh_field("raw_material_items");
						frm.refresh_field("scrap_items");
						frappe.call({
							method: "calculate_formula",
							doc:frm.doc,
							callback: function(r) {
								if (r.message) {
									frm.call({
										method:"calculate_value_raw",
										doc:frm.doc,
										callback: function(r) {
											
										}
										
									});
									frm.refresh_field("raw_material_items");
								}
							}
						});
					}
				}
			});
			frappe.call({
				method: "calculate_formula_scrap_item",
				doc:frm.doc,
				callback: function(r) {
					if (r.message) {
					frm.call({
						method:"calculate_value_scrap",
						doc:frm.doc,
						callback: function(r) {
							
						}
						
					});
					frm.refresh_field("scrap_items");
					}
				}
			});
			
			
			
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
	item_code:function(frm,cdt,cdn){
		const row = locals[cdt][cdn];
		frappe.db.get_doc("Item",row.item_code).then(e  => {
			row.formula=e.cost_calculator_formula
			refresh_field("items")
		})

	},
	qty:function(frm,cdt,cdn){
		const row = locals[cdt][cdn];
		row.amount=row.qty*row.rate
		row.weight=row.qty*row.wp_unit*(1+row.scrap/100)
		frm.refresh_field("raw_material_items");
		frm.call({
			method:"calculate_value_raw",
			doc:frm.doc,
			callback: function(r) {
				
			}
			
		});
	},
	rate:function(frm,cdt,cdn){
		const row = locals[cdt][cdn];
		row.amount=row.qty*row.rate
		frm.refresh_field("raw_material_items");
		frm.call({
			method:"calculate_value_raw",
			doc:frm.doc,
			callback: function(r) {
				
			}
			
		});
		
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
				// if(row.item_attributes){
				// 	
				// 	a+=String(row.item_attributes)
				// 	const f="{"+String(row.item_attributes)+"}"
				// 	console.log(f)
				// 	// var c=JSON.parse(f)
				// 	for(var j in f){
				// 		if(i!=j){
				// 			a+="'"+i+"'"+":"+"'"+args[i]+"'"+","+"\n"
				// 		}
				// 	}
					
				// }
				// else{
					a+="'"+i+"'"+":"+"'"+args[i]+"'"+","+"\n"
					
				
				row.item_attributes = a;
			}
			
			frappe.call({
				method: "calculate_formula",
				doc:frm.doc,
				callback: function(r) {
					if (r.message) {
						frm.call({
							method:"calculate_value_raw",
							doc:frm.doc,
							callback: function(r) {
								
							}
							
						});
						frm.refresh_field("raw_material_items");
					}
				}
			});
			
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
		row.weight=row.qty*row.wp_unit
		frm.refresh_field("scrap_items");
		frm.call({
			method:"calculate_value_scrap",
			doc:frm.doc,
			callback: function(r) {
				
			}
			
		});
		
	},
	rate:function(frm,cdt,cdn){
		const row = locals[cdt][cdn];
		row.amount=row.qty*row.rate
		frm.refresh_field("scrap_items");
		frm.call({
			method:"calculate_value_scrap",
			doc:frm.doc,
			callback: function(r) {
				
			}
			
		});
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
				a+="'"+i+"'"+":"+"'"+args[i]+"'"+","+"\n"
			row.item_attributes = a;
			frappe.call({
				method: "calculate_formula_scrap_item",
				doc:frm.doc,
				callback: function(r) {
					if (r.message) {
					frm.call({
						method:"calculate_value_scrap",
						doc:frm.doc,
						callback: function(r) {
							
						}
						
					});
					frm.refresh_field("scrap_items");
					}
				}
			});
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
		frm.call({
			method:"calculate_value_addons",
			doc:frm.doc,
			callback: function(r) {
				
			}
			
		});
	},
	rate:function(frm,cdt,cdn){
		const row = locals[cdt][cdn];
		row.amount=row.qty*row.rate*row.factor
		frm.call({
			method:"calculate_value_addons",
			doc:frm.doc,
			callback: function(r) {
				
			}
			
		});
	},
	factor:function(frm,cdt,cdn){
		const row = locals[cdt][cdn];
		row.amount=row.qty*row.rate*row.factor
		frm.call({
			method:"calculate_value_addons",
			doc:frm.doc,
			callback: function(r) {
				
			}
			
		});
	},

})