
erpnext.PointOfSale.Controller = class {
	constructor(wrapper) {
		this.wrapper = $(wrapper).find('.layout-main-section');
		this.page = wrapper.page;

		this.check_opening_entry();
		
	}

	fetch_opening_entry() {
		return frappe.call("erpnext.selling.page.point_of_sale.point_of_sale.check_opening_entry", { "user": frappe.session.user });
	}

	check_opening_entry() {
		this.fetch_opening_entry().then((r) => {
			if (r.message.length) {
				// assuming only one opening voucher is available for the current user
				this.prepare_app_defaults(r.message[0]);
			} else {
				this.create_opening_voucher();
			}
		});
	}

	create_opening_voucher() {
		const mcdt = []
		
		const mops = []
		const me = this;
		const table_fields = [
			
			{
				fieldname: "mode_of_payment", fieldtype: "Link",
				in_list_view: 1, label: "Mode of Payment",
				options: "Mode of Payment", reqd: 1
			},
			{
				fieldname: "opening_amount", fieldtype: "Currency",
				in_list_view: 1, label: "Opening Amount",
				options: "company:company_currency",
				change: function () {
					dialog.fields_dict.balance_details.df.data.some(d => {
						if (d.idx == this.doc.idx) {
							this.doc["button"] = d.idx
							console.log("NNNNNNNNNNNNNNNNNNn",this.doc)
							d.opening_amount = this.value;
							dialog.fields_dict.balance_details.grid.refresh();
							return true;
						}
					});
				}
			},
			
		];
		const table_fields2 = [
			
			{
				fieldname: "name", fieldtype: "Data",
				in_list_view: 1, label: "Name",reqd: 1,
				
			},
			{
				fieldname: "factor", fieldtype: "Float",
				in_list_view: 0, label: "Float",reqd: 0,
				read_only:1,
			},
			{
				fieldname: "mode_of_payment", fieldtype: "Link",
				in_list_view: 0, label: "Mode Of Payment",reqd: 1,
				options:"Mode of Payment" , 
				
			},
			{
				
				fieldname: "currency", fieldtype: "Link",
				in_list_view: 1, label: "Currency",reqd: 0,
				hidden:1
					
			},
			{
				
				fieldname: "exchange_rate", fieldtype: "Float",
				in_list_view: 1, label: "Exchange Rate",reqd: 0,
				read_only:1,
				change:function (){
					dialog.fields_dict.mul_curr_denominations.df.data.some(d => {
						if (d.idx == this.doc.idx) {
						d.total_amount = d.factor*d.exchange_rate*d.count
						dialog.fields_dict.mul_curr_denominations.grid.refresh();
						return true;
						}
						
					});
				}
					
			},
			{
				
				fieldname: "count", fieldtype: "Int",
				in_list_view: 1, label: "Count",reqd: 1,
				change:function (){
					let x = 0.0
					dialog.fields_dict.mul_curr_denominations.df.data.some(d => {
						if (d.idx == this.doc.idx) {
							
							d.total_amount = d.factor*d.exchange_rate*d.count
							
						dialog.fields_dict.mul_curr_denominations.grid.refresh();
						
						return true;
						}
						
						

						
			
					});
					var st = {"total_amt":0.0}
						
					dialog.fields_dict.mul_curr_denominations.df.data.forEach(e => {
						st["total_amt"] += parseFloat(e.total_amount)
						console.log("9242",st)
						parseFloat(e.total_amount) ? x+= parseFloat(e.total_amount) : 0.0
						dialog.fields_dict.t_amount.set_value(x);
						dialog.fields_dict.t_amount.refresh();
						
					});
					console.log("x is: ", x)

				}
				
					
			},
			{
				
				fieldname: "total_amount", fieldtype: "Currency",
				in_list_view: 1, label: "Total Amount",reqd: 1
				
					
			},
			




			
		];
		
		const fetch_pos_payment_methods = () => {
			const pos_profile = dialog.fields_dict.pos_profile.get_value();
			if (!pos_profile) return;
			frappe.db.get_doc("POS Profile", pos_profile).then(({ payments }) => {
				dialog.fields_dict.balance_details.df.data = [];
				payments.forEach(pay => {
					const { mode_of_payment } = pay;
					dialog.fields_dict.balance_details.df.data.push({ mode_of_payment, opening_amount: '0' });
				});
				dialog.fields_dict.balance_details.grid.refresh();
			});
		}
		const fetch_pos_payment_method_for_denominations = () => {
			const mops = []
			const pos_profile = dialog.fields_dict.pos_profile.get_value();
			if (!pos_profile) return;
			frappe.db.get_doc("POS Profile", pos_profile).then(({ payments }) => {
				dialog.fields_dict.balance_details.df.data = [];
				payments.forEach(pay => {
					
					dialog.fields_dict.mop.df.options.push(pay.mode_of_payment)
					dialog.fields_dict.mop.refresh();
				});
				
				
			});
		}
		const fetch_curr_and_xchg_rate = () => {
			dialog.fields_dict.mul_curr_denominations.df.data.length = 0
			dialog.fields_dict.mul_curr_denominations.grid.refresh()

			const flist = []
			const fdict = {}
			const d = {"mode_of_payment" : dialog.fields_dict.mop.get_value() }

				console.log("before getdoc")
				if(!d.mode_of_payment) return ;
				frappe.db.get_doc("Mode of Payment", d.mode_of_payment).then(({ currency }) => {
					
					const comp = dialog.fields_dict.company.get_value();
					console.log("after getdoc")
					frappe.db.get_doc("Company",comp).then(({default_currency}) => {
						console.log(default_currency)
						frappe.call({
							method:"erpnext.setup.utils.get_exchange_rate",
							args:{
								"from_currency":currency,
								"to_currency":default_currency

							},
							callback:function(r){
								if(r.message){
									console.log(r.message,r)
									frappe.db.get_doc("Currency",currency).then(({denominations})=> {
										denominations.forEach(g => {

											console.log("*****************",g.name1,g.factor)
											const name = g.name1
											const factor  = g.factor
											const mode_of_payment = d.mode_of_payment
											const exchange_rate = r.message
											flist.push({name,factor,mode_of_payment,exchange_rate})
											
										})
										flist.forEach(m => {
											
											console.log("%%%%%%%%%%%",m)
											dialog.fields_dict.mul_curr_denominations.df.data.push(m)
											dialog.fields_dict.mul_curr_denominations.grid.refresh();
											})
									})
									console.log("flist",flist)

								}
								else{
									console.log("hiii")
									
									dialog.fields_dict.mul_curr_denominations.grid.refresh();
								}
							}
							
						})

					});
					
					

				});
				
			


		}
		
		const dialog = new frappe.ui.Dialog({
			
			title: __('Create POS Opening Entry'),
			static: true,
			fields: [
				
				{
					fieldtype: 'Link', label: __('Company'), default: frappe.defaults.get_default('company'),
					options: 'Company', fieldname: 'company', reqd: 1
				},
				{
					fieldtype: 'Link', label: __('POS Profile'),
					options: 'POS Profile', fieldname: 'pos_profile', reqd: 1,
					get_query: () => pos_profile_query,
					onchange: () => fetch_pos_payment_methods(),
					onchange: () => fetch_pos_payment_method_for_denominations()
				},
				{
					fieldname: "balance_details",
					fieldtype: "Table",
					label: "Opening Balance Details",
					cannot_add_rows: false,
					in_place_edit: true,
					reqd: 1,
					data: [],
					fields: table_fields

				},
				{
					fieldtype: 'Select', label: __('Mode of Payment'), 
					options: [], fieldname: 'mop', reqd: 1,
					onchange: () => fetch_curr_and_xchg_rate()
				},

				{
					fieldname: "mul_curr_denominations",
					fieldtype: "Table",
					label: "Multiple Currency Denominations",
					cannot_add_rows: true,
					in_place_edit: true,
					reqd: 0,
					data: [],
					fields: table_fields2
				},

				{
					fieldtype: 'Data', label: "dict",
					 fieldname: 'mcdt', reqd: 0,
					hidden : 1,
					
				},
				{
					fieldtype: 'Currency', label: "Total Amount",
					 fieldname: 't_amount', reqd: 1,read_only :1
					
					
				},

				
				{
					fieldtype: 'Button', label: __('Add Denominations'), 
					 fieldname: 'button', 
					 click:()=>{
						var mul_curr = {}
						var ftable = {}

						// dialog.fields_dict.mul_curr_denominations.df.data.some(d => {
						// 	d.added = 0
						// 	dialog.fields_dict.mul_curr_denominations.grid.refresh();

						// })

						
						

						const ct = dialog.fields_dict.mul_curr_denominations.df.data
						const ct2 = dialog.fields_dict.balance_details.df.data
						const mpmt = dialog.fields_dict.mop.get_value()
						const tamt = dialog.fields_dict.t_amount.get_value()

						console.log("ct**********",ct)
						if(!mul_curr[mpmt]){
							mul_curr[mpmt] = parseFloat(tamt)
							
						}
						else{
							mul_curr[mpmt] += parseFloat(tamt)
							
						}


						for(var key in ct) {
							if(ct[key].total_amount ){
								mcdt.push({"factor":ct[key].factor,"mode_of_payment":ct[key].mode_of_payment,"exchange_rate":ct[key].exchange_rate,"count":ct[key].count,"total_amount":ct[key].total_amount})
							}
							
								console.log("Yesssssssssssssssssssssss")
								
								
								
							
							
							
							
						 }
						 console.log("1st",mul_curr)

						 for(var key2 in ct2) {
							if(!mul_curr[ct2[key2].mode_of_payment]){
								mul_curr[ct2[key2].mode_of_payment] = parseFloat(ct2[key2].opening_amount)
							}
							else{
								mul_curr[ct2[key2].mode_of_payment] += parseFloat(ct2[key2].opening_amount)
							}
							
							
						 }
						 console.log("2nd",mul_curr)
						
						 console.log("mcdt",mcdt)
						 dialog.fields_dict.balance_details.df.data.length = 0
						dialog.fields_dict.balance_details.grid.refresh();
						dialog.fields_dict.mul_curr_denominations.df.data.length = 0
						dialog.fields_dict.mul_curr_denominations.grid.refresh();
		
		
						for(var key3 in mul_curr) {
							console.log("key213",key3)
							var mode_of_payment = key3;
							var opening_amount = parseFloat(mul_curr[key3])
							dialog.fields_dict.balance_details.df.data.push({ mode_of_payment , opening_amount});
							dialog.fields_dict.balance_details.grid.refresh();
		
						 }
						console.log("key is",mul_curr)

						dialog.fields_dict.mcdt.set_value(mcdt);

						
				
						
					 }
				}
				
				
			],
			
			
			primary_action: async function({ company, pos_profile, balance_details ,mcdt}) {
				console.log("mcdt is ::",company)
				console.log("mcdt is ::",pos_profile)
				console.log("mcdt is ::",mcdt)
				if (!balance_details.length) {
					frappe.show_alert({
						message: __("Please add Mode of payments and opening balance details."),
						indicator: 'red'
					})

					return frappe.utils.play_sound("error");
				}
				console.log(balance_details.filter(d => d.mode_of_payment))

				// filter balance details for empty rows
				balance_details = balance_details.filter(d => d.mode_of_payment);

				const method = "erpnext.selling.page.point_of_sale.point_of_sale.create_opening_voucher";
				const res = await frappe.call({ method, args: { pos_profile, company, balance_details ,mcdt }, freeze:true });
				!res.exc && me.prepare_app_defaults(res.message);
				dialog.hide();
			},
			primary_action_label: __('Submit'),
			
			
		});
		
		
		
		dialog.show();
		dialog.$wrapper.find('.modal-dialog').css("width", "100%");
		const pos_profile_query = {
			query: 'erpnext.accounts.doctype.pos_profile.pos_profile.pos_profile_query',
			filters: { company: dialog.fields_dict.company.get_value() }
		};
	}

	async prepare_app_defaults(data) {
		this.pos_opening = data.name;
		console.log("qazwsxedcrfv",data.name)
		console.log("qazwsxedcrfv",data)
		this.company = data.company;
		this.pos_profile = data.pos_profile;
		this.pos_opening_time = data.period_start_date;
		this.item_stock_map = {};
		this.settings = {};

		frappe.db.get_value('Stock Settings', undefined, 'allow_negative_stock').then(({ message }) => {
			this.allow_negative_stock = flt(message.allow_negative_stock) || false;
		});

		frappe.call({
			method: "erpnext.selling.page.point_of_sale.point_of_sale.get_pos_profile_data",
			args: { "pos_profile": this.pos_profile },
			callback: (res) => {
				const profile = res.message;
				Object.assign(this.settings, profile);
				this.settings.customer_groups = profile.customer_groups.map(group => group.name);
				this.make_app();
			}
		});
	}

	set_opening_entry_status() {
		this.page.set_title_sub(
			`<span class="indicator orange">
				<a class="text-muted" href="#Form/POS%20Opening%20Entry/${this.pos_opening}">
					Opened at ${moment(this.pos_opening_time).format("Do MMMM, h:mma")}
				</a>
			</span>`);
	}

	make_app() {
		this.prepare_dom();
		this.prepare_components();
		this.prepare_menu();
		this.make_new_invoice();
		this.button()
	}

	prepare_dom() {
		this.wrapper.append(
			`<div class="point-of-sale-app"></div>`
		);

		this.$components_wrapper = this.wrapper.find('.point-of-sale-app');
	}

	prepare_components() {
		this.init_item_selector();
		this.init_item_details();
		this.init_item_cart();
		this.init_payments();
		this.init_recent_order_list();
		this.init_order_summary();
		this.getScreenDetails();
	}

	prepare_menu() {

		var pos = this.pos_profile;
		this.page.add_inner_button(__("Clear"), function() {
			frappe.call({
				method: "erpnext.selling.page.point_of_sale.pos.pole_clear",
				args:{
				"pos_profile":pos
			}
			});
			console.log('clear the pole display')
		});

		this.page.clear_menu();

		this.page.add_menu_item(__("Open Form View"), this.open_form_view.bind(this), false, 'Ctrl+F');

		this.page.add_menu_item(__("Toggle Recent Orders"), this.toggle_recent_order.bind(this), false, 'Ctrl+O');

		this.page.add_menu_item(__("Save as Draft"), this.save_draft_invoice.bind(this), false, 'Ctrl+S');

		this.page.add_menu_item(__('Close the POS'), this.close_pos.bind(this), false, 'Shift+Ctrl+C');
	}

	get_mapped_printer() {
		// returns a list of "print format: printer" mapping filtered by the current print format
		let print_format_printer_map = this.get_print_format_printer_map();
		if (print_format_printer_map[this.frm.doctype]) {
			return print_format_printer_map[this.frm.doctype].filter(
				(printer_map) => printer_map.print_format == this.selected_format()
			);
		} else {
			return [];
		}
	}
	get_print_format_printer_map() {
		// returns the whole object "print_format_printer_map" stored in the localStorage.
		try {
			let print_format_printer_map = JSON.parse(
				localStorage.print_format_printer_map
			);
			return print_format_printer_map;
		} catch (e) {
			return {};
		}
	}

	button(){
		this.page.add_inner_button(('Open Cash Drawer'),()=>{
			
			// const me = this;
			console.log("%%%%%%%%%%%%%%%%%%%%%%%",this)
			this.print_format_printer_map = this.get_print_format_printer_map();
			this.data = this.print_format_printer_map[this.frm.doctype] || [];
		    // let printer_list = [];
			f
			frappe.ui.form.qz_get_printer_list().then((data) => {
				
				data.forEach(printer => {
					d.fields_dict.printer.df.options.push(printer)
					d.fields_dict.printer.refresh()
				})
	
			})
		const d = new frappe.ui.Dialog({
			title: __("Supervisor Authorization"),
			fields: [
				{
					label : "Supervisor ID",
					fieldname: "user",
					fieldtype: "Select",
					reqd: 1,
					options: []
				},
				{
					label: "Password",
					fieldname: "password",
					fieldtype: "Password",
					reqd: 1,
				},
				{
					label: 'Date & Time',
					fieldname: 'date_and_time',
					fieldtype: 'Datetime',
					reqd:1,
					read_only:1,
					default: frappe.datetime.now_datetime(),
					hidden:1
				},
				{
					label: 'POS User',
					fieldname: 'pos_user',
					fieldtype: 'Data',
					reqd:1,
					read_only:1,
					hidden:1
				},
				{
					label:'POS Profile',
					fieldname:'pos_profile',
					fieldtype:'Data',
					reqd:1,
					read_only:1,
					hidden:1
				},
				{
					label:'Reason',
					fieldname:'reason',
					fieldtype:'Small Text',
					reqd:1
				},
				{
					label:"Printer",
					fieldname:'printer',
					fieldtype:"Select",
					options:[]
				}
				
			],
			primary_action(v) {
				var data = d.get_values();
				frappe.call({
					method: "grandhyper.api.remove_authorize",
					
					args: {
						"user": data.user,
						"password": data.password,
						"pos_profile": cur_frm.doc.pos_profile,
						'date_and_time':data.date_and_time,
						'pos_user':data.pos_user,
						'pos_profile':data.pos_profile,
						'reason':data.reason
					},
					callback:function(r){
	
						if(r.message){


					// frappe.ui.form.qz_get_printer_list().then(
						frappe.ui.form.qz_connect()
							// frappe.utils.print(
							// 	'Supervisor Log',
							// 	r.message,
							// 	'Demo'
							// )
							.then(function () {

								var config = qz.configs.create(v.printer);
								var data =["Cash Drawer Open"]
								return qz.print(config,data);

							})
							.then(frappe.ui.form.qz_success)
							.catch(err => {
								frappe.ui.form.qz_fail(err);
							})
						}
						
						else{
							frappe.throw('Please enter valid "Supervisor ID" and "Password."');
							
						}

					
					}
				});

				d.hide();
			},
			primary_action_label: __('Authorize')
		});
		d.fields_dict.pos_user.set_value(user)
		d.fields_dict.pos_profile.set_value(this.pos_profile)

		frappe.db.get_doc('POS Profile', this.pos_profile).then((doc) => {
			doc.pos_profile_supervisor.forEach(m=>{
				d.fields_dict.user.df.options.push(m.user)
				d.fields_dict.user.refresh();
			})
		});		
		d.show();			
		}).addClass("btn-warning").css({'color':'#FFFFFF','font-weight': 'bold','background-color':'#0096FF'})
	}


	open_form_view() {
		frappe.model.sync(this.frm.doc);
		frappe.set_route("Form", this.frm.doc.doctype, this.frm.doc.name);
	}

	toggle_recent_order() {
		const show = this.recent_order_list.$component.is(':hidden');
		this.toggle_recent_order_list(show);
	}

	save_draft_invoice() {
		if (!this.$components_wrapper.is(":visible")) return;

		if (this.frm.doc.items.length == 0) {
			frappe.show_alert({
				message: __("You must add atleast one item to save it as draft."),
				indicator:'red'
			});
			frappe.utils.play_sound("error");
			return;
		}

		this.frm.save(undefined, undefined, undefined, () => {
			frappe.show_alert({
				message: __("There was an error saving the document."),
				indicator: 'red'
			});
			frappe.utils.play_sound("error");
		}).then(() => {
			frappe.run_serially([
				() => frappe.dom.freeze(),
				() => this.make_new_invoice(),
				() => frappe.dom.unfreeze(),
			]);
		});
	}

	close_pos() {
		if (!this.$components_wrapper.is(":visible")) return;

		let voucher = frappe.model.get_new_doc('POS Closing Entry');
		voucher.pos_profile = this.frm.doc.pos_profile;
		voucher.user = frappe.session.user;
		voucher.company = this.frm.doc.company;
		voucher.pos_opening_entry = this.pos_opening;
		voucher.period_end_date = frappe.datetime.now_datetime();
		voucher.posting_date = frappe.datetime.now_date();
		frappe.set_route('Form', 'POS Closing Entry', voucher.name);
		console.log('%%%%%%%%%%%%%%%%%%%%%%%5',voucher.user)
	}

	init_item_selector() {
		this.item_selector = new erpnext.PointOfSale.ItemSelector({
			wrapper: this.$components_wrapper,
			pos_profile: this.pos_profile,
			settings: this.settings,
			events: {
				item_selected: args => this.on_cart_update(args),

				get_frm: () => this.frm || {}
			
			},
			
		});
		
		
		
	}

	init_item_cart() {
		window.li = []
		this.cart = new erpnext.PointOfSale.ItemCart({
			wrapper: this.$components_wrapper,
			settings: this.settings,
			events: {
				get_frm: () => this.frm,

				cart_item_clicked: (item) => {
					const item_row = this.get_item_from_frm(item);
					this.item_details.toggle_item_details_section(item_row);
					console.log('ttttttttttttttttttttt',this.frm)
				},
				
				numpad_event: (value, action) => this.update_item_field(value, action),

				checkout: () => this.save_and_checkout(),

				edit_cart: () => this.payment.edit_cart(),

				customer_details_updated: (details) => {
					this.customer_details = details;
					// will add/remove LP payment method
					this.payment.render_loyalty_points_payment_mode();
				},

				new_order: () => {
					frappe.run_serially([
						() => frappe.dom.freeze(),
						() => this.make_new_invoice(),
						() => this.item_selector.toggle_component(true),
						() => frappe.dom.unfreeze(),
					]);
				}
				
			}
			
		})
		
		
	}

	init_item_details() {
		
		this.item_details = new erpnext.PointOfSale.ItemDetails({
			wrapper: this.$components_wrapper,
			settings: this.settings,
			events: {
				get_frm: () => this.frm,

				toggle_item_selector: (minimize) => {
					this.item_selector.resize_selector(minimize);
					this.cart.toggle_numpad(minimize);
				},

				form_updated: (item, field, value) => {
					const item_row = frappe.model.get_doc(item.doctype, item.name);
					if (item_row && item_row[field] != value) {
						const args = {
							field,
							value,
							item: this.item_details.current_item
						};
						
						
						
						return this.on_cart_update(args);

					}
					
					return Promise.resolve();
				},

				highlight_cart_item: (item) => {
					const cart_item = this.cart.get_cart_item(item);
					this.cart.toggle_item_highlight(cart_item);
				},

				item_field_focused: (fieldname) => {
					this.cart.toggle_numpad_field_edit(fieldname);
				},
				set_value_in_current_cart_item: (selector, value) => {
					this.cart.update_selector_value_in_cart_item(selector, value, this.item_details.current_item);
				},
				clone_new_batch_item_in_frm: (batch_serial_map, item) => {
					// called if serial nos are 'auto_selected' and if those serial nos belongs to multiple batches
					// for each unique batch new item row is added in the form & cart
					Object.keys(batch_serial_map).forEach(batch => {
						const item_to_clone = this.frm.doc.items.find(i => i.name == item.name);
						const new_row = this.frm.add_child("items", { ...item_to_clone });
						// update new serialno and batch
						new_row.batch_no = batch;
						new_row.serial_no = batch_serial_map[batch].join(`\n`);
						new_row.qty = batch_serial_map[batch].length;
						this.frm.doc.items.forEach(row => {
							if (item.item_code === row.item_code) {
								this.update_cart_html(row);
							}
						});
					})
				},
				remove_item_from_cart: () => this.remove_item_from_cart(),
				get_item_stock_map: () => this.item_stock_map,
				close_item_details: () => {
					this.item_details.toggle_item_details_section(null);
					this.cart.prev_action = null;
					this.cart.toggle_item_highlight();
				},
				get_available_stock: (item_code, warehouse) => this.get_available_stock(item_code, warehouse)
			}
			
		});
		
		
	}

	init_payments() {
		this.payment = new erpnext.PointOfSale.Payment({
			wrapper: this.$components_wrapper,
			events: {
				get_frm: () => this.frm || {},

				get_customer_details: () => this.customer_details || {},

				toggle_other_sections: (show) => {
					if (show) {
						this.item_details.$component.is(':visible') ? this.item_details.$component.css('display', 'none') : '';
						this.item_selector.toggle_component(false);
					} else {
						this.item_selector.toggle_component(true);
					}
				},

				submit_invoice: () => {
					this.frm.savesubmit()
						.then((r) => {
							
							this.toggle_components(false);
							// this.init_order_summary.new_order();
							this.order_summary.toggle_component(true);
							this.order_summary.load_summary_of(this.frm.doc, true);
							frappe.show_alert({
								indicator: 'green',
								message: __('POS invoice {0} created succesfully', [r.doc.name])
							});
							this.new_order();

						});
				},
				new_order: () => {
					frappe.run_serially([
						() => frappe.dom.freeze(),
						() => this.make_new_invoice(),
						() => this.item_selector.toggle_component(true),
						() => frappe.dom.unfreeze(),
					]);
				}
			}
		});
		
	}

	init_recent_order_list() {
		this.recent_order_list = new erpnext.PointOfSale.PastOrderList({
			wrapper: this.$components_wrapper,
			events: {
				open_invoice_data: (name) => {
					frappe.db.get_doc('POS Invoice', name).then((doc) => {
						this.order_summary.load_summary_of(doc);
					});
					console.log('EEEEEEEEEEEEEEEE',name)
				},
				reset_summary: () => this.order_summary.toggle_summary_placeholder(true)
			}
		})
		
		// return open_invoice_data.name
	}

	init_order_summary() {
		this.order_summary = new erpnext.PointOfSale.PastOrderSummary({
			wrapper: this.$components_wrapper,
			events: {
				get_frm: () => this.frm,

				process_return: (name) => {
					this.recent_order_list.toggle_component(false);
					frappe.db.get_doc('POS Invoice', name).then((doc) => {
						frappe.run_serially([
							() => this.make_return_invoice(doc),
							() => this.cart.load_invoice(),
							() => this.item_selector.toggle_component(true)
						]);
						
					});
				},
				edit_order: (name) => {
					this.recent_order_list.toggle_component(false);
					frappe.run_serially([
						() => this.frm.refresh(name),
						() => this.frm.call('reset_mode_of_payments'),
						() => this.cart.load_invoice(),
						() => this.item_selector.toggle_component(true)
					]);
				},
				delete_order: (name) => {
					frappe.model.delete_doc(this.frm.doc.doctype, name, () => {
						this.recent_order_list.refresh_list();
					});
				},
				new_order: () => {
					frappe.run_serially([
						() => frappe.dom.freeze(),
						() => this.make_new_invoice(),
						() => this.item_selector.toggle_component(true),
						() => frappe.dom.unfreeze(),
					]);
				}
			}
		})
		
	}

	toggle_recent_order_list(show) {
		this.toggle_components(!show);
		this.recent_order_list.toggle_component(show);
		this.order_summary.toggle_component(show);
	}

	toggle_components(show) {
		this.cart.toggle_component(show);
		this.item_selector.toggle_component(show);

		// do not show item details or payment if recent order is toggled off
		!show ? (this.item_details.toggle_component(false) || this.payment.toggle_component(false)) : '';
	}

	make_new_invoice() {
		return frappe.run_serially([
			() => frappe.dom.freeze(),
			() => this.make_sales_invoice_frm(),
			() => this.set_pos_profile_data(),
			() => this.set_pos_profile_status(),
			() => this.cart.load_invoice(),
			() => frappe.dom.unfreeze()
		]);
	}

	make_sales_invoice_frm() {
		const doctype = 'POS Invoice';
		return new Promise(resolve => {
			if (this.frm) {
				this.frm = this.get_new_frm(this.frm);
				this.frm.doc.items = [];
				this.frm.doc.is_pos = 1
				resolve();
			} else {
				frappe.model.with_doctype(doctype, () => {
					this.frm = this.get_new_frm();
					this.frm.doc.items = [];
					this.frm.doc.is_pos = 1
					resolve();
				});
			}
		});
	}

	get_new_frm(_frm) {
		const doctype = 'POS Invoice';
		const page = $('<div>');
		const frm = _frm || new frappe.ui.form.Form(doctype, page, false);
		const name = frappe.model.make_new_doc_and_get_name(doctype, true);
		frm.refresh(name);

		return frm;
	}

	async make_return_invoice(doc) {
		frappe.dom.freeze();
		this.frm = this.get_new_frm(this.frm);
		this.frm.doc.items = [];
		return frappe.call({
			method: "erpnext.accounts.doctype.pos_invoice.pos_invoice.make_sales_return",
			args: {
				'source_name': doc.name,
				'target_doc': this.frm.doc
			},
			callback: (r) => {
				frappe.model.sync(r.message);
				frappe.get_doc(r.message.doctype, r.message.name).__run_link_triggers = false;
				this.set_pos_profile_data().then(() => {
					frappe.dom.unfreeze();
				});
			}
		});
	}

	set_pos_profile_data() {
		if (this.company && !this.frm.doc.company) this.frm.doc.company = this.company;
		if (this.pos_profile && !this.frm.doc.pos_profile) this.frm.doc.pos_profile = this.pos_profile;
		if (!this.frm.doc.company) return;

		return this.frm.trigger("set_pos_data");
	}

	set_pos_profile_status() {
		this.page.set_indicator(this.pos_profile, "blue");
	}

	async on_cart_update(args) {
		const mylist =[]
		const qty_list = []
		frappe.dom.freeze();
		let item_row = undefined;
		try {
			let { field, value, item } = args;
			item_row = this.get_item_from_frm(item);
			const item_row_exists = !$.isEmptyObject(item_row);
			console.log(item)
			console.log('args',args)
			li.push({"item_name":item_row.item_name,
					"amount":item_row.amount,
					"qty":item_row.qty,
					"item_code":item_row.item_code,
					"rate":item_row.rate,
					'income_account':item_row.income_account,
					'uom':item_row.uom,
					'conversion_factor': item_row.conversion_factor
				})
			console.log('SSSSSSSSSSSSSSSSSSSss',li)
			mylist.push(item.item_code,item.rate)
			console.log(mylist)

			const from_selector = field === 'qty' && value === "+1";
			if (from_selector)
				value = flt(item_row.qty) + flt(value);
				console.log("value********************************************",value)
				
			if (item_row_exists) {
				if (field === 'qty')
					value = flt(value);

				if (['qty', 'conversion_factor'].includes(field) && value > 0 && !this.allow_negative_stock) {
					const qty_needed = field === 'qty' ? value * item_row.conversion_factor : item_row.qty * value;
					await this.check_stock_availability(item_row, qty_needed, this.frm.doc.set_warehouse);
				}

				if (this.is_current_item_being_edited(item_row) || from_selector) {
					await frappe.model.set_value(item_row.doctype, item_row.name, field, value);
					this.update_cart_html(item_row);
				}
				qty_list.push(item_row.item_name,item_row.amount,item_row.qty)
				

			} else {
				if (!this.frm.doc.customer)
					return this.raise_customer_selection_alert();

				const { item_code, batch_no, serial_no, rate } = item;

				if (!item_code)
					return;

				const new_item = { item_code, batch_no, rate, [field]: value };

				if (serial_no) {
					await this.check_serial_no_availablilty(item_code, this.frm.doc.set_warehouse, serial_no);
					new_item['serial_no'] = serial_no;
				}

				if (field === 'serial_no')
					new_item['qty'] = value.split(`\n`).length || 0;

				item_row = this.frm.add_child('items', new_item);

				if (field === 'qty' && value !== 0 && !this.allow_negative_stock)
					await this.check_stock_availability(item_row, value, this.frm.doc.set_warehouse);

				await this.trigger_new_item_events(item_row);

				this.update_cart_html(item_row);

				if (this.item_details.$component.is(':visible'))
					this.edit_item_details_of(item_row);

				if (this.check_serial_batch_selection_needed(item_row) && !this.item_details.$component.is(':visible'))
					this.edit_item_details_of(item_row);

		
			}
			// this.save_draft_invoice();
			this.add_item();
			console.log('###############')
			this.getItem(li);
			var func = this.
			myfunction(mylist);
			

		} catch (error) {
			console.log(error);
		} finally {
			frappe.dom.unfreeze();
			return item_row;
		}
	}

	raise_customer_selection_alert() {
		frappe.dom.unfreeze();
		frappe.show_alert({
			message: __('You must select a customer before adding an item.'),
			indicator: 'orange'
		});
		frappe.utils.play_sound("error");
	}

	get_item_from_frm({ name, item_code, batch_no, uom, rate }) {
		let item_row = null;
		if (name) {
			item_row = this.frm.doc.items.find(i => i.name == name);
		} else {
			// if item is clicked twice from item selector
			// then "item_code, batch_no, uom, rate" will help in getting the exact item
			// to increase the qty by one
			const has_batch_no = batch_no;
			item_row = this.frm.doc.items.find(
				i => i.item_code === item_code
					&& (!has_batch_no || (has_batch_no && i.batch_no === batch_no))
					&& (i.uom === uom)
					&& (i.rate == rate)
			);
		}

		return item_row || {};
	}

	edit_item_details_of(item_row) {
		this.item_details.toggle_item_details_section(item_row);
	}

	is_current_item_being_edited(item_row) {
		return item_row.name == this.item_details.current_item.name;
	}

	update_cart_html(item_row, remove_item) {
		this.cart.update_item_html(item_row, remove_item);
		this.cart.update_totals_section(this.frm);
	}

	check_serial_batch_selection_needed(item_row) {
		// right now item details is shown for every type of item.
		// if item details is not shown for every item then this fn will be needed
		const serialized = item_row.has_serial_no;
		const batched = item_row.has_batch_no;
		const no_serial_selected = !item_row.serial_no;
		const no_batch_selected = !item_row.batch_no;

		if ((serialized && no_serial_selected) || (batched && no_batch_selected) ||
			(serialized && batched && (no_batch_selected || no_serial_selected))) {
			return true;
		}
		return false;
	}

	async trigger_new_item_events(item_row) {
		await this.frm.script_manager.trigger('item_code', item_row.doctype, item_row.name);
		await this.frm.script_manager.trigger('qty', item_row.doctype, item_row.name);
	};

	
	async check_stock_availability(item_row, qty_needed, warehouse) {
		const resp = (await this.get_available_stock(item_row.item_code, warehouse)).message;
		const available_qty = resp[0];
		const is_stock_item = resp[1];

		frappe.dom.unfreeze();
		const bold_item_code = item_row.item_code.bold();
		const bold_warehouse = warehouse.bold();
		const bold_available_qty = available_qty.toString().bold()
		if (!(available_qty > 0)) {
			if (is_stock_item) {
				frappe.model.clear_doc(item_row.doctype, item_row.name);
				frappe.throw({
					title: __("Not Available"),
					message: __('Item Code: {0} is not available under warehouse {1}.', [bold_item_code, bold_warehouse])
				});
			} else {
				return;
			}
		} else if (available_qty < qty_needed) {
			frappe.throw({
				message: __('Stock quantity not enough for Item Code: {0} under warehouse {1}. Available quantity {2}.', [bold_item_code, bold_warehouse, bold_available_qty]),
				indicator: 'orange'
			});
			frappe.utils.play_sound("error");
		}
		frappe.dom.freeze();
	}

	async check_serial_no_availablilty(item_code, warehouse, serial_no) {
		const method = "erpnext.stock.doctype.serial_no.serial_no.get_pos_reserved_serial_nos";
		const args = {filters: { item_code, warehouse }}
		const res = await frappe.call({ method, args });

		if (res.message.includes(serial_no)) {
			frappe.throw({
				title: __("Not Available"),
				message: __('Serial No: {0} has already been transacted into another POS Invoice.', [serial_no.bold()])
			});
		}
	}

	get_available_stock(item_code, warehouse) {
		const me = this;
		return frappe.call({
			method: "erpnext.accounts.doctype.pos_invoice.pos_invoice.get_stock_availability",
			args: {
				'item_code': item_code,
				'warehouse': warehouse,
			},
			callback(res) {
				if (!me.item_stock_map[item_code])
					me.item_stock_map[item_code] = {};
				me.item_stock_map[item_code][warehouse] = res.message[0];
			}
		});
	}

	update_item_field(value, field_or_action) {
		if (field_or_action === 'checkout') {
			this.item_details.toggle_item_details_section(null);
		} else if (field_or_action === 'remove') {
			this.remove_item_from_cart();
		} else {
			const field_control = this.item_details[`${field_or_action}_control`];
			if (!field_control) return;
			field_control.set_focus();
			value != "" && field_control.set_value(value);
		}
	}

	remove_item_from_cart() {

		// new code Start for GH customization #PRE00715
		let me = this
		var d = new frappe.ui.Dialog({
			title: __("Supervisor Authorization"),
			fields: [
				{
					label : "Supervisor ID",
					fieldname: "user",
					fieldtype: "Link",
					reqd: 1,
					options: "User"
				},
				{
					label: "Password",
					fieldname: "password",
					fieldtype: "Password",
					reqd: 1,
				}
			],
			primary_action: function() {
				var data = d.get_values();
				frappe.call({
					method: "erpnext.selling.page.point_of_sale.point_of_sale.remove_authorize",
					
					args: {
						 "user": data.user,
						"password": data.password,
						"action" : "Remove Item",
						"pos_profile": cur_frm.doc.pos_profile,
						"owner" : cur_frm.doc.owner,
						"item": me.item_details.item_row.item_code,
						"canceled_transaction" : "" },
					callback: (res) => {
						if (res.message){
							d.hide();
							frappe.dom.freeze();
							
							const { doctype, name, current_item } = me.item_details;

							return frappe.model.set_value(doctype, name, 'qty', 0)
								.then(() => {
									frappe.model.clear_doc(doctype, name);
									me.update_cart_html(current_item, true);
									me.item_details.toggle_item_details_section(null);
									frappe.dom.unfreeze();
									
								})
								.catch(e => console.log(e));
						}else{
							d.hide();
							frappe.msgprint(__("Invalid Credentials. You cannot remove this item"));
							
						}
					}
				});

				d.hide();
			},
			primary_action_label: __('Authorize')
		});
		d.show();

		// new doc end

		// frappe.dom.freeze();
		// console.log(" this is item_details ", this.item_details)
		// const { doctype, name, current_item } = this.item_details;

		// return frappe.model.set_value(doctype, name, 'qty', 0)
		// 	.then(() => {
		// 		frappe.model.clear_doc(doctype, name);
		// 		this.update_cart_html(current_item, true);
		// 		this.item_details.toggle_item_details_section(null);
		// 		frappe.dom.unfreeze();
		// 	})
		// 	.catch(e => console.log(e));
	}

	async save_and_checkout() {
		if (this.frm.is_dirty()) {
			let save_error = false;
			await this.frm.save(null, null, null, () => save_error = true);
			// only move to payment section if save is successful
			!save_error && this.payment.checkout();
			// show checkout button on error
			save_error && setTimeout(() => {
				this.cart.toggle_checkout_btn(true);
			}, 300); // wait for save to finish
		} else {
			this.payment.checkout();
		}
	}
	
	
	myfunction(name, data){
		var b = this.pos_profile;
		var a=this.cart.update_totals_section(this.frm)
		frappe.call({
			method: "erpnext.selling.page.point_of_sale.pos.pole_display",
			args:{
				"item":name[0],
				"amount":name[1],
				"grand_total":a,
				"pos_profile":b
			},
			
        });
		};	

	check(name, data){
		var b = this.pos_profile;
		var a=this.cart.update_totals_section(this.frm)
		frappe.call({
			method: "erpnext.selling.page.point_of_sale.pos.check",
			args:{
				"grand_total":a,
				"pos_profile":b
			},
			
		});
		};	

	

	getScreenDetails(){
		const screenDetails = window.getScreenDetails();
		console.log(screenDetails)
		console.log(window.location)

		var url = window.location.href
		var arr = url.split("/");
		var result = arr[0] + "//" + arr[2] + '/' + 'app' + '/'  + 'pos-display-cart'
		console.log(result)

		const popup = window.open(
			result,
			'My Popup',
			'left=1920,top=0,width=1920,height=1080',
		  );

		  popup.moveTo(2500, 50);
	}


	getItem(data){
		var a=this.pos_profile
		console.log('QQQQQQQQQQQQ',data)
		frappe.call({
			method: "grandhyper.grandhyper.doctype.temporary_cart.temporary_cart.item",
			args:{
				"pos_profile":a,
				"data":data
				
			},
			
        });
		console.log('@@@@@@@@@@@current page',cur_page)
		};	

	add_item(){

		if (!this.$components_wrapper.is(":visible")) return;

		if (this.frm.doc.items.length == 0) {
			frappe.show_alert({
				message: __("You must add atleast one item to save it as draft."),
				indicator:'red'
			});
			frappe.utils.play_sound("error");
			return;
		}
		

		this.frm.save(undefined, undefined, undefined, () => {
			frappe.show_alert({
				message: __("There was an error saving the document."),
				indicator: 'red'
			});
			frappe.utils.play_sound("error");
		}).then(() => {
			frappe.run_serially([
				() => frappe.dom.freeze(),
				() => frappe.dom.unfreeze(),
			]);
		});
		
	};

	


};

