// Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Beat', {
	refresh :function(frm,cdt,cdn){
		// frm.fields_dict['beatct'].grid.get_field('sales_person').get_query = function(doc, cdt, cdn) {
		// 	var child = locals[cdt][cdn];
		// 	//console.log(child);
		// 	return {    
		// 		filters:[
		// 			['parent_sales_person', '=', frm.doc.sales_manager]
		// 		]
		// 	}
		// },
		frm.fields_dict['beatct'].grid.get_field('monday').get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			//console.log(child);
			return {    
				filters:[
					['parent_territory', '=', frm.doc.territory]
				]
			}
		},
		frm.fields_dict['beatct'].grid.get_field('tuesday').get_query = function(doc, cdt, cdn) {
			var child = locals[cdt][cdn];
			console.log(child);
			return {    
				filters:[
					['parent_territory', '=', frm.doc.territory]
				]
			}
		},
		frm.fields_dict['beatct'].grid.get_field('wednesday').get_query = function(doc, cdt, cdn) {
			// var child = locals[cdt][cdn];
			//console.log(child);
			return {    
				filters:[
					['parent_territory', '=', frm.doc.territory]
				]
			}
		},
		frm.fields_dict['beatct'].grid.get_field('thursday').get_query = function(doc, cdt, cdn) {
			// var child = locals[cdt][cdn];
			//console.log(child);
			return {    
				filters:[
					['parent_territory', '=', frm.doc.territory]
				]
			}
		},
		frm.fields_dict['beatct'].grid.get_field('friday').get_query = function(doc, cdt, cdn) {
			// var child = locals[cdt][cdn];
			//console.log(child);
			return {    
				filters:[
					['parent_territory', '=', frm.doc.territory]
				]
			}
		},
		frm.fields_dict['beatct'].grid.get_field('saturday').get_query = function(doc, cdt, cdn) {
			// var child = locals[cdt][cdn];
			//console.log(child);
			return {    
				filters:[
					['parent_territory', '=', frm.doc.territory]
				]
			}
		}
	},
	sales_manager: function(frm){
		frm.clear_table("beatct")
		frappe.call({
            method: "get_salesperson", //dotted path to server method
			doc:frm.doc,
			callback: function(r) {
               frm.refresh_field("beatct")
            }
        });
		
		

	},
	validate : function(frm,cdt,cdn){
		
		let rows = frm.doc.beatct
		// console.log(rows)
		let l = frm.set_value('sales_person_count',rows.length)
		frm.refresh_field("beatct");
		// frm.set_value('t_visit',l*6)
		// frm.refresh_field("beatct");


		
	},
	week_start_date : function(frm){
		var end = frappe.datetime.add_days(frm.doc.week_start_date, 5)
		frm.set_value("week_end_date", end)
		var getdate = frm.doc.week_start_date
		var d = new Date(getdate);
		var weekday = new Array(7);
		weekday[0] = "Sunday";
		weekday[1] = "Monday";
		weekday[2] = "Tuesday";
		weekday[3] = "Wednesday";
		weekday[4] = "Thursday";
		weekday[5] = "Friday";
		weekday[6] = "Saturday";
		var n = weekday[d.getDay()];
		if (n!="Monday"){
			
			
			frappe.throw(__('Week Must Start From Monday'))
		

		}
		
		

	},
	setup : function(frm){
		frm.set_query('sales_manager',()=>{
			return{
				filters:{
					// territory :frm.doc.territory,
					is_group : 1
				}
			}
		})
	}
});
		
// frappe.ui.form.on("beatct", "monday", function(frm, cdt, cdn) {

// 	var mon = frm.doc.monday
// 	frm.set_value('t_visit',mon.length)
// 	frm.refresh_field("beatct");




// });
