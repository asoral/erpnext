/* eslint-disable no-unused-vars */
erpnext.PointOfSale.Payment = class {
	constructor({ events, wrapper }) {
		this.wrapper = wrapper;
		console.log("wrapper**************",wrapper)
		this.events = events;
		console.log("events***************************",events)
		

		this.init_component();
	}

	init_component() {
		this.prepare_dom();
		this.initialize_numpad();
		this.bind_events();
		this.attach_shortcuts();

	}

	prepare_dom() {
		this.wrapper.append(
			`<section class="payment-container">
				<div class="payment-modes"></div>
				<div class="fields-numpad-container">
					<div class="fields-section">
						
						
						<div class="invoice-fields"></div>
						
					</div>
				</div>
				<div class="totals-section">
					<div class="totals"></div>
				</div>
				<div class="submit-order-btn">${__("Complete Order")}</div>
			</section>`
		);
		this.$component = this.wrapper.find('.payment-container');
		this.$payment_modes = this.$component.find('.payment-modes');
		this.$totals_section = this.$component.find('.totals-section');
		this.$totals = this.$component.find('.totals');
		this.$numpad = this.$component.find('.number-pad');
		this.$invoice_fields_section = this.$component.find('.fields-section');
		console.log("og_numpad",this.$numpad)
	}

	make_invoice_fields_control() {
		frappe.db.get_doc("POS Settings", undefined).then((doc) => {
			const fields = doc.invoice_fields;
			if (!fields.length) return;

			this.$invoice_fields = this.$invoice_fields_section.find('.invoice-fields');
			this.$invoice_fields.html('');
			const frm = this.events.get_frm();

			fields.forEach(df => {
				this.$invoice_fields.append(
					`<div class="invoice_detail_field ${df.fieldname}-field" data-fieldname="${df.fieldname}"></div>`
				);
				let df_events = {
					onchange: function() {
						frm.set_value(this.df.fieldname, this.get_value());
					}
				};
				if (df.fieldtype == "Button") {
					df_events = {
						click: function() {
							if (frm.script_manager.has_handlers(df.fieldname, frm.doc.doctype)) {
								frm.script_manager.trigger(df.fieldname, frm.doc.doctype, frm.doc.docname);
							}
						}
					};
				}

				this[`${df.fieldname}_field`] = frappe.ui.form.make_control({
					df: {
						...df,
						...df_events
					},
					parent: this.$invoice_fields.find(`.${df.fieldname}-field`),
					render_input: true,
				});
				this[`${df.fieldname}_field`].set_value(frm.doc[df.fieldname]);
			});
		});
	}

	initialize_numpad() {
		const me = this;
		this.number_pad = new erpnext.PointOfSale.NumberPad({
			wrapper: this.$numpad,
			events: {
				numpad_event: function($btn) {
					me.on_numpad_clicked($btn);
				}
			},
			cols: 3,
			keys: [
				[ 1, 2, 3 ],
				[ 4, 5, 6 ],
				[ 7, 8, 9 ],
				[ '.', 0, 'Delete' ]
			],
		});

		this.numpad_value = '';
	}

	on_numpad_clicked($btn) {
		const button_value = $btn.attr('data-button-value');

		highlight_numpad_btn($btn);
		this.numpad_value = button_value === 'delete' ? this.numpad_value.slice(0, -1) : this.numpad_value + button_value;
		this.selected_mode.$input.get(0).focus();
		this.selected_mode.set_value(this.numpad_value);

		function highlight_numpad_btn($btn) {
			$btn.addClass('shadow-base-inner bg-selected');
			setTimeout(() => {
				$btn.removeClass('shadow-base-inner bg-selected');
			}, 100);
		}
	}

	bind_events() {
		const me = this;

		this.$payment_modes.on('click', '.mode-of-payment', function(e) {
			const mode_clicked = $(this);
			// if clicked element doesn't have .mode-of-payment class then return
			if (!$(e.target).is(mode_clicked)) return;

			const scrollLeft = mode_clicked.offset().left - me.$payment_modes.offset().left + me.$payment_modes.scrollLeft();
			me.$payment_modes.animate({ scrollLeft });

			const mode = mode_clicked.attr('data-mode');

			// hide all control fields and shortcuts
			$(`.mode-of-payment-control`).css('display', 'none');
			$(`.cash-shortcuts`).css('display', 'none');
			me.$payment_modes.find(`.pay-amount`).css('display', 'inline');
			me.$payment_modes.find(`.loyalty-amount-name`).css('display', 'none');

			// remove highlight from all mode-of-payments
			$('.mode-of-payment').removeClass('border-primary');

			if (mode_clicked.hasClass('border-primary')) {
				// clicked one is selected then unselect it
				mode_clicked.removeClass('border-primary');
				me.selected_mode = '';
			} else {
				// clicked one is not selected then select it
				mode_clicked.addClass('border-primary');
				mode_clicked.find('.mode-of-payment-control').css('display', 'flex');
				mode_clicked.find('.cash-shortcuts').css('display', 'grid');
				me.$payment_modes.find(`.${mode}-amount`).css('display', 'none');
				me.$payment_modes.find(`.${mode}-name`).css('display', 'inline');

				me.selected_mode = me[`${mode}_control`];
				me.selected_mode && me.selected_mode.$input.get(0).focus();
				me.auto_set_remaining_amount();
			}
		});

		frappe.ui.form.on('POS Invoice', 'contact_mobile', (frm) => {
			const contact = frm.doc.contact_mobile;
			const request_button = $(this.request_for_payment_field.$input[0]);
			if (contact) {
				request_button.removeClass('btn-default').addClass('btn-primary');
			} else {
				request_button.removeClass('btn-primary').addClass('btn-default');
      }
    });

		frappe.ui.form.on('POS Invoice', 'coupon_code', (frm) => {
			if (frm.doc.coupon_code && !frm.applying_pos_coupon_code) {
				if (!frm.doc.ignore_pricing_rule) {
					frm.applying_pos_coupon_code = true;
					frappe.run_serially([
						() => frm.doc.ignore_pricing_rule=1,
						() => frm.trigger('ignore_pricing_rule'),
						() => frm.doc.ignore_pricing_rule=0,
						() => frm.trigger('apply_pricing_rule'),
						() => frm.save(),
						() => this.update_totals_section(frm.doc),
						() => (frm.applying_pos_coupon_code = false)
					]);
				} else if (frm.doc.ignore_pricing_rule) {
					frappe.show_alert({
						message: __("Ignore Pricing Rule is enabled. Cannot apply coupon code."),
						indicator: "orange"
					});
				}
			}
		});

		this.setup_listener_for_payments();

		this.$payment_modes.on('click', '.shortcut', function() {
			const value = $(this).attr('data-value');
			me.selected_mode.set_value(value);
		});

		// this.$component.on('click', '.submit-order-btn', () => {
		// 	const doc = this.events.get_frm().doc;
		// 	const paid_amount = doc.paid_amount;
		// 	const items = doc.items;

		// 	if (paid_amount == 0 || !items.length) {
		// 		const message = items.length ? __("You cannot submit the order without payment.") : __("You cannot submit empty order.");
		// 		frappe.show_alert({ message, indicator: "orange" });
		// 		frappe.utils.play_sound("error");
		// 		return;
		// 	}

		// 	console.log(" this is invoice submit", this.events)
		// 	this.events.submit_invoice();
		// 	// frappe.run_serially([
		// 	// 	() => this.events.submit_invoice(),
		// 	// 	// () => this.events.new_order()
		// 	// ]);
			
		// });

		
			
		this.$component.on('click', ".submit-order-btn", () => {
			window.dicty = {}
			
			const pmts = [];
			const me = this ;
			const tot = 0.0;
			
			

			

			

			

			const doc = this.events.get_frm().doc;
			console.log("doc*********************************8",doc)
			const paid_amount = doc.paid_amount;
			const items = doc.items;
			const payments = doc.payments;
			const gt = doc.grand_total;
			const pos = doc.pos_profile
			

			const table_fields = [
			
				
				{
					fieldname: "base_amount", fieldtype: "Float",
					in_list_view: 1, label: "Amount",reqd: 0,
					 
					
				},

				{
					fieldname: "mode_of_payment", fieldtype: "Data",
					in_list_view: 1, label: "Mode Of Payment",reqd: 0,
					 
					
				},
				{
					
					fieldname: "currency", fieldtype: "Link",
					in_list_view: 0, label: "Currency",reqd: 0,
					hidden:0
						
				},
				{
					
					fieldname: "exchange_rate", fieldtype: "Float",
					in_list_view: 0, label: "Exchange Rate",reqd: 0,
					
					
						
				},
				{
					fieldname: "amount", fieldtype: "Currency",
					in_list_view: 1, label: "Base Amount",reqd: 0,
					options:"Currency"
					 
					
				},

			]
			

			





			


			const d = new frappe.ui.Dialog({
				title: 'Enter details',
				fields: [
					{
						fieldtype: 'Select', label: __('Mode of Payment'), 
						options: [], fieldname: 'mop', reqd: 1,
						onchange: () => fetch_curr_and_xchg_rate()
					},

					{
						fieldtype: 'Section Break'
					},

					{
						fieldtype: 'HTML', label: __('Grand Total'), 
						 fieldname: 'gte', reqd: 0
				
						
					},

					{
						fieldtype: 'Section Break'
					},

					{
						fieldtype: 'Float', label: __('Base Amount'), 
						 fieldname: 'bamount', reqd: 1,
						onchange: () => get_total()

						
					},

					{
						fieldtype: 'Column Break'
					},

					{
						fieldtype: 'Link', label: __('Currency'), 
						 fieldname: 'currency', reqd: 1, options:"Currency",
						 read_only:1
						
					},

					{
						fieldtype: 'Column Break'
					},
					{
						fieldtype: 'Float', label: __('Exchange Rate'), 
						 fieldname: 'xchg_rate', reqd: 1,
						 read_only:1
						
					},
					{
						fieldtype: 'Column Break'
					},
					{
						fieldtype: 'Currency', label: __('Amount(Base Currency)'), 
						 fieldname: 'amt', reqd: 1,
						 read_only:1
						
					},
					{
						fieldtype: 'Section Break'
					},

					{
						fieldtype: 'HTML', label: __('Grand Total'), 
						 fieldname: 'totals', reqd: 0
				
						
					},

					{
						fieldtype: 'Section Break'
					},


					{
					fieldname: "payment_details",
					fieldtype: "Table",
					label: "Payment Details",
					cannot_add_rows: true,
					in_place_edit: true,
					reqd: 0,
					data: [],
					fields: table_fields,
					hidden:1

				},
					{
						fieldtype: 'Section Break'
					},

					{
						fieldtype: 'HTML', label: __('Numpad'), 
						 fieldname: 'numpad', reqd: 0,
						//  click: () => {
						// 	 console.log("helllo")
						//  }
				
						
					},
					{
						fieldtype: 'Section Break'
					},
					{
						fieldtype: 'Button', label: __('Add Amount'), 
						 fieldname: 'btn', reqd: 0,
						 click:()=>{
							 
							//  tot += parseFloat(d.fields_dict.pamt.get_value() + d.fields_dict.amt.get_value())
							 console.log("ooooooooooooooooooooooooooooo",tot)
							 let base_amount = d.fields_dict.bamount.get_value()
							 let currency = d.fields_dict.currency.get_value()
							 let exchange_rate = d.fields_dict.xchg_rate.get_value()
							 let amount = d.fields_dict.amt.get_value()
							 let tobe_paid = d.fields_dict.amtp.get_value()
							 let change = d.fields_dict.chg.get_value()
							 let mode_of_payment = d.fields_dict.mop.get_value()
							 console.log("9242*******************",d.fields_dict.payment_details.get_value())

							 let ct = d.fields_dict.payment_details.get_value()
							 console.log("ct^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^66",ct)

							 const doc = this.events.get_frm().doc;
							 const payments = doc.payments

							 

							 

							 




							
							 
							
							 
							 
							if(ct.length != 0 ){
								console.log("NOtEmpty*********************")
								ct.forEach(i=>{
									if(i["mode_of_payment"] == mode_of_payment){
										i["base_amount"] += base_amount
										i["amount"] += amount
										
									}
									else{
										console.log("mop not present")
										
										
									}
								})
							}
							
							 

							

							//  d.fields_dict.payment_details.df.data.some(z => {
							// 	// console.log("z)))))))))))))))))))00",z)
							// 	// tot += z.amount
							// 	console.log("z)))))))))))))))))))00",tot)
							// })
							// total_amt += amount + d.fields_dict.pamt.get_value()
							if(!dicty["tamt"]){

								dicty["tamt"] = amount
								console.log("if&&&&&&&&&&&&&&&&&&&&&&&&&&&")
							}
							else if(dicty["tamt"]){
								dicty["tamt"] += amount
								console.log("else&&&&&&&&&&&&&&&&&&&&&&&&&&&")
							}

							if(!dicty["tobe_paid"]){
								dicty["tobe_paid"] = tobe_paid
							}
							else if(dicty["tobe_paid"]){
								dicty["tobe_paid"] += tobe_paid
								
							}

							if(!dicty["change"]){
								dicty["change"] = change
							}
							else if(dicty["change"]){
								dicty["change"] += change
								
							}
							

							 d.fields_dict.payment_details.grid.refresh();
							 d.fields_dict.pamt.set_value(dicty["tamt"])
							//  d.fields_dict.amtp.set_value(dicty["tobe_paid"])
							//  d.fields_dict.chg.set_value(dicty["change"])
							let amtphtml = 0.0
							let changehtml = 0.0

							if(d.fields_dict.gtotal.get_value()-dicty["tamt"] > 0){
								console.log("amtp****************************888",d.fields_dict.gtotal.get_value()-dicty["tamt"] > 0)
								d.fields_dict.amtp.set_value(d.fields_dict.gtotal.get_value()-dicty["tamt"])
								d.set_df_property('chg', 'hidden', 1)
								d.set_df_property('amtp', 'hidden', 0)
								amtphtml += d.fields_dict.gtotal.get_value()-dicty["tamt"]

							}
							else if(d.fields_dict.gtotal.get_value()-dicty["tamt"] < 0){
								console.log("chg****************************888",d.fields_dict.gtotal.get_value()-dicty["tamt"] < 0)
								d.fields_dict.chg.set_value(-(d.fields_dict.gtotal.get_value()-dicty["tamt"]))
								d.set_df_property('amtp', 'hidden', 1)
								d.set_df_property('chg', 'hidden', 0)
								changehtml += (-(d.fields_dict.gtotal.get_value()-dicty["tamt"]))

							}

							

							
							


							const totals = `
							<style>
							.styled-table {
								border-collapse: collapse;
								margin: 25px 0;
								font-size: 1.2em;
								font-family: sans-serif;
								min-width: 510px;
								box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
							}

							.styled-table thead tr {
								background-color: #009879;
								color: #ffffff;
								text-align: left;
							}

							.styled-table th,
							.styled-table td {
								padding: 12px 15px;
							}
							</style>


							<table class="styled-table">
							<thead>
								<tr>
									<th>Grand Total</th>
									<th>Paid Amount</th>
									<th>To Be Paid</th>
									<th>Change</th>
								</tr>
							</thead>
							<tbody>
								<tr>
									<td>${format_currency(gt, "INR")}</td>
									<td>${format_currency(dicty["tamt"], "INR")}</td>
									<td>${format_currency(amtphtml, "INR")}</td>
									<td>${format_currency(changehtml, "INR" )}</td>
								</tr>
								
							</tbody>
						</table>
							`


							$(d.fields_dict['totals'].wrapper).html(totals)

							
							

							
							 
							 
							 
							 

						 }
				
						
					},
					{
						fieldtype: 'Column Break'
					},

					{
						fieldtype: 'Button', label: __('Clear'), 
						 fieldname: 'btn2', reqd: 0,
						 click:()=>{

							console.log("this_events(((((((((((((((((((",this.events)

							dicty["tamt"] = 0.0
							dicty["tobe_paid"] = 0.0
							dicty["change"] = 0.0
							d.fields_dict.pamt.set_value("")
							d.fields_dict.amtp.set_value("")
							d.fields_dict.chg.set_value("")
							d.fields_dict.payment_details.df.data.length = 0
							d.fields_dict.payment_details.refresh();
							d.fields_dict.pamt.refresh()
							d.fields_dict.amtp.refresh()

							 
							payments.forEach(m => {
							let base_amount = 0.0
							let amount = 0.0
							let mode_of_payment = m.mode_of_payment
							d.fields_dict.payment_details.df.data.push({base_amount,mode_of_payment,amount})
							d.fields_dict.payment_details.refresh();
							
						})

						const totals = `
							<style>
							.styled-table {
								border-collapse: collapse;
								margin: 25px 0;
								font-size: 1.2em;
								font-family: sans-serif;
								min-width: 510px;
								box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
							}

							.styled-table thead tr {
								background-color: #009879;
								color: #ffffff;
								text-align: left;
							}

							.styled-table th,
							.styled-table td {
								padding: 12px 15px;
							}
							</style>


							<table class="styled-table">
							<thead>
								<tr>
									<th>Grand Total</th>
									<th>Paid Amount</th>
									<th>To Be Paid</th>
									<th>Change</th>
								</tr>
							</thead>
							<tbody>
								<tr>
									<td>${format_currency(gt, "INR")}</td>
									<td>${format_currency(0.0, "INR")}</td>
									<td>${format_currency(gt, "INR")}</td>
									<td>${format_currency(0.0, "INR" )}</td>
								</tr>
								
							</tbody>
						</table>
							`


							$(d.fields_dict['totals'].wrapper).html(totals)
							 

							 
							
						 }
				
						
					},
					
					{
						fieldtype: 'Section Break'
					},
					{
						fieldtype: 'Currency', label: __('Grand Total'), 
						 fieldname: 'gtotal', reqd: 0,
						 hidden:1
						
					},
					{
						fieldtype: 'Column Break'
					},
					{
						fieldtype: 'Currency', label: __('Paid Amount'), 
						 fieldname: 'pamt', reqd: 0,
						 hidden:1,
						 
						
					},
					{
						fieldtype: 'Column Break'
					},
					{
						fieldtype: 'Currency', label: __('Amount To Be Paid'), 
						 fieldname: 'amtp', reqd: 0,
						 hidden:1
						
					},
					{
						fieldtype: 'Column Break'
					},
					{
						fieldtype: 'Currency', label: __('Change'), 
						 fieldname: 'chg', reqd: 0,
						 hidden:1
						
					},



					
					

					
				],
				primary_action_label: 'Submit',
				primary_action(values) {
					let me = this;

					this.$components_wrapper = this.wrapper.find('.point-of-sale-app');
					console.log("values**************************",me.events)
					let final_dict = {"grand_total":parseFloat(values.gtotal),"paid_amount":values.pamt,"change_amount":values.chg,"currency":"INR","rounded_total":parseFloat(values.gtotal)

					}
					// me.update_totals_section(final_dict)
					doc["base_paid_amount"] = values.pamt
					doc["change_amount"] = values.chg
					console.log("doc&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&7",doc.name)
					
					if(values.amtp == 0.0 || values.chg > 0.0){
						frappe.call({
							method:"erpnext.selling.page.point_of_sale.pos_payment.update_pos_invoice",
							args:{
								"values":values.payment_details,
								"inv":doc.name,
								"paid_amount":values.pamt,
								"change_amount":values.chg
								
							},
							callback:function(r){
								if (r.message == "reload"){
									frappe.call({
										method: "erpnext.selling.page.point_of_sale.pos.pole_clear",
										args:{
										"pos_profile":pos
									}
									});
									window.location.reload()
								}
								// frappe.ui.form.qz_connect()
								// .then(function () {
								// 	var config = qz.configs.create("POS-80")
								// 	// window.location.reload()
								// 	return qz.print(config, [r.message]);
								// })
								// .then(frappe.ui.form.qz_success)
								// .catch(err => {
								// 	frappe.ui.form.qz_fail(err);
								// });

								
	
							}
						})
						
						





						d.hide();

					}
					else if(values.amtp > 0.0){
						const message = __("You cannot submit the order without payment.")
						frappe.show_alert({ message, indicator: "orange" });
						frappe.utils.play_sound("error");
						return;

					}
					
					
					


					
					
				}
			});
			
			
			d.show();
			d.$wrapper.find('.modal-dialog').css("width", "1000px");
			console.log("fields_dict",d.fields_dict.numpad)

			

			

			let numpad_loc = d.fields_dict.numpad.$wrapper.find('.payment-container');
			let npddg = numpad_loc.find('.number-pad');

			console.log("find",npddg)



			

			


		
			

			//  = (val) => {
			// 	d.fields_dict.bamount.set_value(val)
		
			// }get_total_amount


			


			const get_total = () => {
				console.log("before",d.fields_dict.amt.get_value())
				let total = d.fields_dict.bamount.get_value() * d.fields_dict.xchg_rate.get_value()
				d.fields_dict.amt.set_value(total);
				
			}
			const get_diff = () => {
				console.log("before",d.fields_dict.pamt.get_value())
				let total = d.fields_dict.gtotal.get_value() - d.fields_dict.amt.get_value()
				let ftotal = 0.0
				if(d.fields_dict.pamt.get_value()){
					ftotal += total - d.fields_dict.pamt.get_value()
					d.fields_dict.amtp.set_value(ftotal);
				}
				
				// let ftotal = total - d.fields_dict.pamt.get_value()
				let gtotal = d.fields_dict.gtotal.get_value()
				if(ftotal < 0){
					console.log("total********************",total)
					d.fields_dict.chg.set_value((-ftotal));
					d.fields_dict.amtp.set_value(0.0);
					d.set_df_property('amtp', 'hidden', 1);
					d.set_df_property('chg', 'hidden', 0);
					
				}
				else if(ftotal >0){
					d.fields_dict.chg.set_value(0.0);
					d.set_df_property('chg', 'hidden', 1);
					d.set_df_property('amtp', 'hidden', 0);
					d.fields_dict.amtp.set_value(ftotal);

				}
				
			}

			const fetch_curr_and_xchg_rate = () => {
				const me = this;
				const doc = this.events.get_frm().doc;
				const comp = doc.company;
				
				d.fields_dict.gtotal.set_value(gt)
				d.fields_dict.bamount.set_value(0.0)
				d.fields_dict.currency.set_value("")
				d.fields_dict.xchg_rate.set_value(0.0)
				d.fields_dict.amt.set_value(0.0)
				
				
				
				
				
	
				const flist = []
				const fdict = {}
				const p = {"mode_of_payment" : d.fields_dict.mop.get_value() }
	
					console.log("before getdoc",p.mode_of_payment,comp)
					if(!p.mode_of_payment) return ;


					frappe.db.get_doc("Mode of Payment", p.mode_of_payment).then(( currency ) => {
						
						
						console.log("after getdoc",currency)
						frappe.db.get_doc("Company",comp).then(({default_currency}) => {
							console.log(default_currency)
							frappe.call({
								method:"erpnext.setup.utils.get_exchange_rate",
								args:{
									"from_currency":currency.currency,
									"to_currency":default_currency
	
								},
								callback:function(r){
									if(r.message){

										const formatted_currency_equi = format_currency(parseFloat(gt/r.message), currency.currency)
										d.fields_dict.xchg_rate.set_value(r.message);
										d.fields_dict.currency.set_value(currency.currency)
										// $(d.fields_dict['numpad'].wrapper).html(npd);
										const strhtml = `<h3>Grand Total in ${currency.currency} : ${formatted_currency_equi} </h3>`

										
										$(d.fields_dict['gte'].wrapper).html(strhtml)

										
										
										
	
									}
									// else{
									// 	console.log("hiii")
										
									// 	dialog.fields_dict.mul_curr_denominations.grid.refresh();
									// }
								}
								
							})
	
						});
						
						
	
					});
					
				
			
			const npd = `<!DOCTYPE html>
			<html>
			<head>
			<style>
			.button {
			  border: none;
			  color: black;
			  padding: 15px 32px;
			  text-align: center;
			  text-decoration: none;
			  display: inline-block;
			  font-size: 16px;
			  margin: 4px 2px;
			  cursor: pointer;
			}
			
			.button1  /* Green */
			.button2  /* Blue */
			.button3 
			.button4
			.button5
			.button6
			.button7
			.button8
			.button9
			.button10
			.button11
			.button12
			
			
			</style>
			</head>
			<body>
			
			
			<p id="demo"></p>
			
			<script>
			
			
			function myFunction(v) {
				window.lk = 0.0
				

				// frappe.call({
				// 	method:"erpnext.selling.page.point_of_sale.pos_payment.get_total_amount",
				// 	args:{
				// 		"equi":v
				// 	},
				// 	callback:function(r){
				// 		lk += v

				
		
		
						
		
		
				// 	},
				// })
			  document.getElementById("demo").innerHTML += v ;
			//   get_total_amount(document.getElementById("demo").innerHTML)
			  window.lk = document.getElementById("demo").innerHTML
			  console.log(lk)
			
						
			  
			 
			}
			function myFunction2(){
				document.getElementById("demo").innerHTML=""
			}
			</script>
			
			
			
			<button class="button button1" onclick="myFunction(1)" >1</button>
			<button class="button button2" onclick="myFunction(2)">2</button>
			<button class="button button3" onclick="myFunction(3)">3</button>
			
			<br> <button class="button button4" onclick="myFunction(4)">4</button>
				<button class="button button5" onclick="myFunction(5)">5</button>
				<button class="button button6" onclick="myFunction(6)">6</button> 
			</br>
			
			
			  <button class="button button7" onclick="myFunction(7)">7</button>
			  <button class="button button8" onclick="myFunction(8)">8</button>
			  <button class="button button9" onclick="myFunction(9)">9</button>
			
			
			<br>
			  <button class="button button10" onclick="myFunction('.')">.</button>
			  <button class="button button11" onclick="myFunction(0)">0</button>
			  <button class="button button12" onclick="myFunction2()">Del</button>
			</br>
			
			
			
			
			</body>
			</html>`
	
			}



			payments.forEach(m => {
				frappe.db.get_doc("POS Invoice",m.parent).then(p => {
					frappe.db.get_doc("POS Profile",p.pos_profile).then(g => {
						g.payments.forEach(pymts => {
						d.fields_dict.mop.df.options.push(pymts.mode_of_payment)
						console.log("9242*********************")
						d.fields_dict.mop.refresh();
						let base_amount = 0.0
						let amount = 0.0
						let mode_of_payment = pymts.mode_of_payment
						d.fields_dict.payment_details.df.data.push({base_amount,mode_of_payment,amount})
						d.fields_dict.payment_details.refresh();

						})
						

					})


				})

				

				
				
				
				
			})

			
			

			
			
		});

		

		frappe.ui.form.on('POS Invoice', 'paid_amount', (frm) => {
			this.update_totals_section(frm.doc);
			console.log("frm.doc&&&&&&&&&&&&&&&&&&&&&&&&&&&&&7",frm.doc)

			// need to re calculate cash shortcuts after discount is applied
			const is_cash_shortcuts_invisible = !this.$payment_modes.find('.cash-shortcuts').is(':visible');
			this.attach_cash_shortcuts(frm.doc);
			!is_cash_shortcuts_invisible && this.$payment_modes.find('.cash-shortcuts').css('display', 'grid');
			this.render_payment_mode_dom();
		});

		frappe.ui.form.on('POS Invoice', 'loyalty_amount', (frm) => {
			const formatted_currency = format_currency(frm.doc.loyalty_amount, frm.doc.currency);
			this.$payment_modes.find(`.loyalty-amount-amount`).html(formatted_currency);
		});

		frappe.ui.form.on("Sales Invoice Payment", "amount", (frm, cdt, cdn) => {
			// for setting correct amount after loyalty points are redeemed
			const default_mop = locals[cdt][cdn];
			const mode = default_mop.mode_of_payment.replace(/ +/g, "_").toLowerCase();
			if (this[`${mode}_control`] && this[`${mode}_control`].get_value() != default_mop.amount) {
				this[`${mode}_control`].set_value(default_mop.amount);
			}
		});
	}

	

	setup_listener_for_payments() {
		frappe.realtime.on("process_phone_payment", (data) => {
			const doc = this.events.get_frm().doc;
			const { response, amount, success, failure_message } = data;
			let message, title;

			if (success) {
				title = __("Payment Received");
				const grand_total = cint(frappe.sys_defaults.disable_rounded_total) ? doc.grand_total : doc.rounded_total;
				if (amount >= grand_total) {
					frappe.dom.unfreeze();
					message = __("Payment of {0} received successfully.", [format_currency(amount, doc.currency, 0)]);
					this.events.submit_invoice();
					cur_frm.reload_doc();

				} else {
					message = __("Payment of {0} received successfully. Waiting for other requests to complete...", [format_currency(amount, doc.currency, 0)]);
				}
			} else if (failure_message) {
				message = failure_message;
				title = __("Payment Failed");
			}

			frappe.msgprint({ "message": message, "title": title });
		});
	}

	auto_set_remaining_amount() {
		const doc = this.events.get_frm().doc;
		const grand_total = cint(frappe.sys_defaults.disable_rounded_total) ? doc.grand_total : doc.rounded_total;
		const remaining_amount = grand_total - doc.paid_amount;
		const current_value = this.selected_mode ? this.selected_mode.get_value() : undefined;
		if (!current_value && remaining_amount > 0 && this.selected_mode) {
			this.selected_mode.set_value(remaining_amount);
		}
	}

	attach_shortcuts() {
		const ctrl_label = frappe.utils.is_mac() ? '⌘' : 'Ctrl';
		this.$component.find('.submit-order-btn').attr("title", `${ctrl_label}+Enter`);
		frappe.ui.keys.on("ctrl+enter", () => {
			const payment_is_visible = this.$component.is(":visible");
			const active_mode = this.$payment_modes.find(".border-primary");
			if (payment_is_visible && active_mode.length) {
				this.$component.find('.submit-order-btn').click();
			}
		});

		frappe.ui.keys.add_shortcut({
			shortcut: "tab",
			action: () => {
				const payment_is_visible = this.$component.is(":visible");
				let active_mode = this.$payment_modes.find(".border-primary");
				active_mode = active_mode.length ? active_mode.attr("data-mode") : undefined;

				if (!active_mode) return;

				const mode_of_payments = Array.from(this.$payment_modes.find(".mode-of-payment")).map(m => $(m).attr("data-mode"));
				const mode_index = mode_of_payments.indexOf(active_mode);
				const next_mode_index = (mode_index + 1) % mode_of_payments.length;
				const next_mode_to_be_clicked = this.$payment_modes.find(`.mode-of-payment[data-mode="${mode_of_payments[next_mode_index]}"]`);

				if (payment_is_visible && mode_index != next_mode_index) {
					next_mode_to_be_clicked.click();
				}
			},
			condition: () => this.$component.is(':visible') && this.$payment_modes.find(".border-primary").length,
			description: __("Switch Between Payment Modes"),
			ignore_inputs: true,
			page: cur_page.page.page
		});
	}

	toggle_numpad() {
		// pass
	}

	render_payment_section() {
		
		this.render_payment_mode_dom();
		this.make_invoice_fields_control();
		this.update_totals_section();
		this.focus_on_default_mop();
	}

	edit_cart() {
		this.events.toggle_other_sections(false);
		this.toggle_component(false);
	}

	checkout() {
		this.events.toggle_other_sections(true);
		this.toggle_component(true);

		this.render_payment_section();
	}

	toggle_remarks_control() {
		if (this.$remarks.find('.frappe-control').length) {
			this.$remarks.html('+ Add Remark');
		} else {
			this.$remarks.html('');
			this[`remark_control`] = frappe.ui.form.make_control({
				df: {
					label: __('Remark'),
					fieldtype: 'Data',
					onchange: function() {}
				},
				parent: this.$totals_section.find(`.remarks`),
				render_input: true,
			});
			this[`remark_control`].set_value('');
		}
	}

	fetch_curr_and_xchg_rate(mode_of_payment,amount){
		let to_curr = ""
		let equi = 0.0
		// setTimeout(this.render_payment_mode_dom, 2000)
		return frappe.call({
			method:"erpnext.selling.page.point_of_sale.pos_payment.get_dets",
			args:{
				"mop":mode_of_payment,
				"amount":amount

			},
			callback:function(r){
				console.log("789456123",r.message)
				to_curr = r.message[1]
				equi = r.message[0]
				console.log("to_curr9242",to_curr)
				console.log("equi9242",equi)

				return equi
				//return Promise.resolve(equi);


				


			},
			

		})
		
	 };

	 fetch_gt(mode_of_payment,amount){
		let to_curr = ""
		let equi = 0.0
		// setTimeout(this.render_payment_mode_dom, 2000)
		return frappe.call({
			method:"erpnext.selling.page.point_of_sale.pos_payment.get_gt",
			args:{
				"mop":mode_of_payment,
				"amount":amount

			},
			callback:function(r){
				console.log("789456123",r.message)
				to_curr = r.message[1]
				equi = r.message[0]
				console.log("to_curr9242",to_curr)
				console.log("equi9242",equi)

				return equi
				//return Promise.resolve(equi);


				


			},
			

		})
		
	 };

	
	// get_grand_total_in_multiple_currencies(){
	// 	const doc = this.events.get_frm().doc;
	// 	const grand_total = doc.grand_total;
	// 	const pos_profile = doc.pos_profile
	// 	const mop = [];
	// 	let component = this.wrapper.find('.payment-container');
	// 	let ai = component.find('.fields-section')
	// 	frappe.db.get_doc("POS Profile",pos_profile).then(mods=> {
			
	// 		for(var key in mods.payments){
	// 			console.log("key**************88",mods.payments[key]["mode_of_payment"].replace(/ +/g, "_").toLowerCase())
	// 			mop.push(mods.payments[key]["mode_of_payment"])
	// 		}
	// 		ai.append(`<button type="button"><div class="multi-curr-btn">${__("Payment Methods")}</div></button>`)
	// 		mop.forEach(w => {
	// 			console.log("Currency Dict^^^^^^^^^^^^^^^^^^^^^^^^^^^",w)
	// 			this.fetch_gt(w,grand_total).then(e => {
	// 			console.log("MYList for grand total is: ", e.message)
	// 			let activemode = e.message[w.replace(/ +/g, "_").toLowerCase()]
	// 			console.log("MYList for grand total is: ", activemode)
	// 			window.to_curr = activemode[0]
	// 			window.equi = activemode[1]

	// 			const formatted_currency_equi = format_currency(equi, to_curr);
	// 			ai.append(`

							
	// 						<div class="cash-to_curr"> Grand Total in  ${to_curr} :${formatted_currency_equi} </div>`

	// 					)


					
					

	// 			})
	// 		})

			
			
			
	// 	})



	// }

	render_payment_mode_dom() {
		



	// 	const doc = this.events.get_frm().doc;
	// 	const pos_profile = doc.pos_profile
	// 	const grand_total = doc.grand_total
	// 	console.log("89415615194984",doc)
		
	// 	const currency = doc.currency;
		
		



	// 	// this.fetch_curr_and_xchg_rate(p.mode_of_payment,current_value).then(e => {
	// 	// 	console.log("MYList is: ", e.message)
	// 	// 	window.activemode = e.message[active_mode]
	// 	// 		window.to_curr = activemode[0]
	// 	// 		window.equi = activemode[1]
	// 	// })
	// 	// console.log("mop*****************&&&&&&&&&&&&&&&&",mop)
		
	// 	const payments = doc.payments;
	// 	console.log("Currency Dict",currency)
		


		
	// 	const default_company = frappe.defaults.get_default('company');
	// 	const com_curr = frappe.get_doc(":Company", default_company).default_currency;
	// 	var xchg = 0.0

	// 	this.$payment_modes.html(`${
			
	// 		console.log("payments",payments),
	// 		payments.map((p, i) => {
	// 			console.log("p&&&&&&&&*************",i)
	// 			const mode = p.mode_of_payment.replace(/ +/g, "_").toLowerCase();
	// 			const amount = p.amount > 0 ? format_currency(p.amount, currency) : '';
	// 			console.log("Amount is",currency)
	// 			let mop_curr = ""
			
	// 			console.log("mode",mop_curr)
	// 			const payment_type = p.type;
	// 			const margin = i % 2 === 0 ? 'pr-2' : 'pl-2';
				


				
				
	// 			this.fetch_curr_and_xchg_rate(p.mode_of_payment,p.amount).then(e => {
	// 				console.log("MYList is: ", e.message)

	// 				window.to_curr = e.message[1]
	// 				window.equi = e.message[0]

	// 			})

				

	// 			var x= (`
	// 			<div class="payment-mode-wrapper">
	// 				<div class="mode-of-payment" data-mode="${mode}" data-payment-type="${payment_type}">
	// 					${p.mode_of_payment}
	// 					<div class="${mode}-amount pay-amount">${amount}</div>
	// 					<div class="${mode} mode-of-payment-control"></div>
						
						
	// 				</div>
					
					
	// 			</div>
	// 		`);
				
				
	// 			return  x
	// 		}).join('')
	// 	}`);

	// 	payments.forEach(p => {
	// 		// console.log("index of payments*******************",i)
	// 		const mode = p.mode_of_payment.replace(/ +/g, "_").toLowerCase();
	// 		const me = this;
	// 		const doc = this.events.get_frm().doc;
	// 		this[`${mode}_control`] = frappe.ui.form.make_control({
	// 			df: {
	// 				label: p.mode_of_payment,
	// 				fieldtype: 'Currency',
	// 				placeholder: __('Enter {0} amount.', [p.mode_of_payment]),
	// 				onchange: function() {


	// 					let active_mode2 = me.$payment_modes.find(".border-primary");
	// 					let active_mode = active_mode2.length ? active_mode2.attr("data-mode") : undefined;
	// 					console.log("9242********************",active_mode)



	// 					if (!active_mode) return;

	// 					// const mode_of_payments = Array.from(this.$payment_modes.find(".mode-of-payment")).map(m => $(m).attr("data-mode"));
	// 					// const mode_index = mode_of_payments.indexOf(active_mode);

	// 					// console.log("9242********************",mode_index)
						
	// 					const current_value = frappe.model.get_value(p.doctype, p.name, 'amount');
	// 					me.fetch_curr_and_xchg_rate(p.mode_of_payment,current_value).then(e => {
	// 						console.log("MYList is: ", e.message)
	// 						window.activemode = e.message[active_mode]
	// 							window.to_curr = activemode[0]
	// 							window.equi = activemode[1]
	// 					})
	// 					console.log("ct",frappe.model.get_value(p.doctype, p.name, 'mode_of_payment'))
	// 					if (current_value != this.value) {
	// 						console.log("yes")
	// 						frappe.model
	// 							.set_value(p.doctype, p.name, 'amount', flt(this.value))
	// 							.then(() => me.update_totals_section())
	// 							me.fetch_curr_and_xchg_rate(p.mode_of_payment,this.value).then(e => {
	// 								console.log("MYList is: ", e.message)
	// 								window.activemode = Object.keys(e.message)[0]
									
	// 								console.log("am*******************",activemode)
	// 								window.to_curr = e.message[activemode][0]
	// 								window.equi = e.message[activemode][1]
	// 								const formatted_currency_equi = format_currency(equi, to_curr);
									
	// 							console.log("yyyyyyyyyyyyyyyyyyyyyyyeeeeeeeeeeessssssssssss",activemode)
	// 							console.log(">>>>>>>>>>>>>>>>>>>>>>: ",me.wrapper.find('.payment-container') , to_curr)
	// 							me.$payment_modes.find(`cash-equi`).html(formatted_currency_equi);
	// 							// let component = me.wrapper.find('.payment-container');
	// 							// let ai = component.find('.fields-section')

								
	// 							if(to_curr != com_curr && equi > 0.0){
									
	// 								frappe.model
	// 								.set_value(p.doctype, p.name, 'amount', flt(equi))
	// 								.then(() => me.update_totals_section())

									

								
								
						
						
										
						
						
	// 								}
								
	// 							// else if (to_curr == com_curr){
									
	// 							// 	doc["updated_amount"] =  equi
	// 							// 	console.log("equi*********************",doc,equi)
									
	// 							// }
								

								
							
	// 							})
 

	// 					}
	// 				}
	// 			},
	// 			parent: this.$payment_modes.find(`.${mode}.mode-of-payment-control`),
	// 			render_input: true,
	// 		});
	// 		this[`${mode}_control`].toggle_label(false);
	// 		this[`${mode}_control`].set_value(p.amount);
	// 	});

	// 	this.render_loyalty_points_payment_mode();

	// 	this.attach_cash_shortcuts(doc);
	}

	focus_on_default_mop() {
		const doc = this.events.get_frm().doc;
		const payments = doc.payments;
		payments.forEach(p => {
			const mode = p.mode_of_payment.replace(/ +/g, "_").toLowerCase();
			if (p.default) {
				setTimeout(() => {
					this.$payment_modes.find(`.${mode}.mode-of-payment-control`).parent().click();
				}, 500);
			}
		});
	}

	attach_cash_shortcuts(doc) {
		const grand_total = cint(frappe.sys_defaults.disable_rounded_total) ? doc.grand_total : doc.rounded_total;
		const currency = doc.currency;

		const shortcuts = this.get_cash_shortcuts(flt(grand_total));

		this.$payment_modes.find('.cash-shortcuts').remove();
		let shortcuts_html = shortcuts.map(s => {
			return `<div class="shortcut" data-value="${s}">${format_currency(s, currency, 0)}</div>`;
		}).join('');

		this.$payment_modes.find('[data-payment-type="Cash"]').find('.mode-of-payment-control')
			.after(`<div class="cash-shortcuts">${shortcuts_html}</div>`);
	}

	get_cash_shortcuts(grand_total) {
		let steps = [1, 5, 10];
		const digits = String(Math.round(grand_total)).length;

		steps = steps.map(x => x * (10 ** (digits - 2)));

		const get_nearest = (amount, x) => {
			let nearest_x = Math.ceil((amount / x)) * x;
			return nearest_x === amount ? nearest_x + x : nearest_x;
		};

		return steps.reduce((finalArr, x) => {
			let nearest_x = get_nearest(grand_total, x);
			nearest_x = finalArr.indexOf(nearest_x) != -1 ? nearest_x + x : nearest_x;
			return [...finalArr, nearest_x];
		}, []);
	}

	render_loyalty_points_payment_mode() {
		const me = this;
		const doc = this.events.get_frm().doc;
		const { loyalty_program, loyalty_points, conversion_factor } = this.events.get_customer_details();

		this.$payment_modes.find(`.mode-of-payment[data-mode="loyalty-amount"]`).parent().remove();

		if (!loyalty_program) return;

		let description, read_only, max_redeemable_amount;
		if (!loyalty_points) {
			description = __("You don't have enough points to redeem.");
			read_only = true;
		} else {
			max_redeemable_amount = flt(flt(loyalty_points) * flt(conversion_factor), precision("loyalty_amount", doc));
			description = __("You can redeem upto {0}.", [format_currency(max_redeemable_amount)]);
			read_only = false;
		}

		const margin = this.$payment_modes.children().length % 2 === 0 ? 'pr-2' : 'pl-2';
		const amount = doc.loyalty_amount > 0 ? format_currency(doc.loyalty_amount, doc.currency) : '';
		this.$payment_modes.append(
			`<div class="payment-mode-wrapper">
				<div class="mode-of-payment loyalty-card" data-mode="loyalty-amount" data-payment-type="loyalty-amount">
					Redeem Loyalty Points
					<div class="loyalty-amount-amount pay-amount">${amount}</div>
					<div class="loyalty-amount-name">${loyalty_program}</div>
					<div class="loyalty-amount mode-of-payment-control"></div>
				</div>
			</div>`
		);

		this['loyalty-amount_control'] = frappe.ui.form.make_control({
			df: {
				label: __("Redeem Loyalty Points"),
				fieldtype: 'Currency',
				placeholder: __("Enter amount to be redeemed."),
				options: 'company:currency',
				read_only,
				onchange: async function() {
					if (!loyalty_points) return;

					if (this.value > max_redeemable_amount) {
						frappe.show_alert({
							message: __("You cannot redeem more than {0}.", [format_currency(max_redeemable_amount)]),
							indicator: "red"
						});
						frappe.utils.play_sound("submit");
						me['loyalty-amount_control'].set_value(0);
						return;
					}
					const redeem_loyalty_points = this.value > 0 ? 1 : 0;
					await frappe.model.set_value(doc.doctype, doc.name, 'redeem_loyalty_points', redeem_loyalty_points);
					frappe.model.set_value(doc.doctype, doc.name, 'loyalty_points', parseInt(this.value / conversion_factor));
				},
				description
			},
			parent: this.$payment_modes.find(`.loyalty-amount.mode-of-payment-control`),
			render_input: true,
		});
		this['loyalty-amount_control'].toggle_label(false);

		// this.render_add_payment_method_dom();
	}

	render_add_payment_method_dom() {
		const docstatus = this.events.get_frm().doc.docstatus;
		if (docstatus === 0)
			this.$payment_modes.append(
				`<div class="w-full pr-2">
					<div class="add-mode-of-payment w-half text-grey mb-4 no-select pointer">+ Add Payment Method</div>
				</div>`
			);
	}

	update_totals_section(doc) {
		if (!doc) doc = this.events.get_frm().doc;
		const paid_amount = parseFloat(doc.paid_amount);
		const grand_total = cint(frappe.sys_defaults.disable_rounded_total) ? doc.grand_total : doc.rounded_total;
		const remaining = grand_total-parseFloat(doc.paid_amount);
		const change = doc.change_amount || remaining <= 0 ? -1 * remaining : undefined;
		const currency = doc.currency;
		const label = change ? __('Change') : __('To Be Paid');

		// this.$totals.html(
		// 	`<div class="col">
		// 		<div class="total-label">${__('Grand Total')}</div>
		// 		<div class="value">${format_currency(grand_total, currency)}</div>
		// 	</div>
		// 	<div class="seperator-y"></div>
		// 	<div class="col">
		// 		<div class="total-label">${__('Paid Amount')}</div>
		// 		<div class="value">${format_currency(paid_amount, currency)}</div>
		// 	</div>
		// 	<div class="seperator-y"></div>
		// 	<div class="col">
		// 		<div class="total-label">${label}</div>
		// 		<div class="value">${format_currency(change || remaining, currency)}</div>
		// 	</div>`
		// );
	}

	toggle_component(show) {
		console.log("show**********************************************")
		show ? this.$component.css('display', 'flex') : this.$component.css('display', 'none');
	}
};
