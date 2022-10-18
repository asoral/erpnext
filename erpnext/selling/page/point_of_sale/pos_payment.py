# from ast import main
from filecmp import cmp
from frappe.utils.data import flt
from erpnext import get_default_company
from erpnext.setup.utils import get_exchange_rate
from frappe.utils import fmt_money
from frappe.www.printview import get_print_style
# from erpnext.accounts.doctype.loyalty_program_collection.row_wise_loyalty import row_wise_loyalty_point

# from erpnext.erpnext.accounts.doctype.pos_invoice.pos_invoice import (check_phone_payments,set_status)

# from erpnext.erpnext.accounts.doctype.sales_invoice.sales_invoice import (make_loyalty_point_entry , apply_loyalty_points)


import frappe


@frappe.whitelist()
def get_barcode(sf):
    print("jnsnbjdbkjjbdbs",sf)


@frappe.whitelist()
def get_dets(mop,amount):
    
    to_curr = frappe.get_doc("Mode of Payment",mop).currency
    def_comp = get_default_company()
    from_curr = frappe.get_doc("Company",def_comp).default_currency
    xchg_rate = get_exchange_rate(from_curr,to_curr)
    equi = flt(flt(amount)*xchg_rate)
    print("equi",equi)
    final = {
        mop.replace(' ','_').lower():[to_curr,equi]
    }
    return final

@frappe.whitelist()
def get_gt(mop,amount):
    
    to_curr = frappe.get_doc("Mode of Payment",mop).currency
    def_comp = get_default_company()
    from_curr = frappe.get_doc("Company",def_comp).default_currency
    xchg_rate = get_exchange_rate(from_curr,to_curr)
    print("xchg",xchg_rate)
    equi = flt(flt(amount)/xchg_rate)
    print("equi in gt",equi)
    final = {
        mop.replace(' ','_').lower():[to_curr,equi]
    }
    return final



@frappe.whitelist()
def get_total_amount(equi):
    ap = {"gt":equi}

    return ap


# def inv_sub(doc):
#     if doc.loyalty_program:
#         doc.make_loyalty_point_entry()
#     elif doc.is_return and doc.return_against and doc.loyalty_program:
#         against_psi_doc = frappe.get_doc("POS Invoice", doc.return_against)
#         against_psi_doc.delete_loyalty_point_entry()
#         against_psi_doc.make_loyalty_point_entry()
#     if doc.redeem_loyalty_points and doc.loyalty_points:
#         doc.apply_loyalty_points()
#     check_phone_payments()
#     set_status(update=True)

#     if doc.coupon_code:
#         from erpnext.accounts.doctype.pricing_rule.utils import update_coupon_code_count
#         update_coupon_code_count(doc.coupon_code,'used')



@frappe.whitelist()
def update_pos_invoice(values,inv,paid_amount,change_amount):
    lod = []
    val = eval(values)
    print("dict1",val)
    for kl in val:
        print("********************",kl)
        lod.append({
            kl["mode_of_payment"]:[kl["base_amount"],kl["amount"]]
        })

    print("****************new",lod)


    main_doc = frappe.get_doc("POS Invoice",inv)
    # doc = frappe.db.get_all("Sales Invoice Payment",{'parent':inv},['*'])
    # print("dict2",doc)
    lst = ["mode_of_payment"]

    

    for o in lst:
        # if o in val and doc:
        #     print("yes",val.get(o),doc.get(o))
    
        if main_doc:
            main_doc.set("payments",[])
            

            # print(doc.payments)
            for k in val:
                mop = frappe.get_doc("Mode of Payment",k.get("mode_of_payment"))
                print("(@$@*********************0",k)
                main_doc.append("payments",{
                    "mode_of_payment":k.get("mode_of_payment"),
                    "amount":k.get("amount"),
                    "paid_currency":mop.currency,
                    "amount_paid_currency":fmt_money(k.get("base_amount"),currency = mop.currency)
                })

                                
                        
                              



                        

            main_doc.base_change_amount = change_amount
            main_doc.change_amount = change_amount

            main_doc.paid_amount = paid_amount

            main_doc.save(ignore_permissions = True)
            if float(main_doc.paid_amount) > 0:
                # row_wise_loyalty_point(main_doc.name)
                main_doc.submit()    
                if main_doc.docstatus == 1:
                    print("jsnjnvjsnjnsjvjsjvj j")
                    return "reload"      
                        # frappe.db.commit()

                        

                        

                        # doc2 = {}

                        # pos_inv = frappe.db.get_all("POS Invoice",{'name':inv},['*'])
                        # pdoc = frappe.get_doc("POS Invoice",inv)
                        # print("pdoc",pdoc.items)

                        # inv_sub(pdoc)

                        # for i in pos_inv:
                        #     print("items",i.items)
                        #     items = frappe.db.get_all("POS Invoice Item",{'parent':inv},['*'])
                        #     print("items2",items)
                        #     doc2.update({
                        #         "company_address":i.company_address,
                        #         "pos_profile":i.pos_profile,
                        #         "customer_name":i.customer_name,
                        #         "posting_date":i.posting_date,
                        #         "posting_time":i.posting_time,
                        #         "items":items,
                        #         "total":i.total,
                        #         "total_taxes_and_charges":i.total_taxes_and_charges,
                        #         "grand_total":i.grand_total,
                        #         "barcode":i.barcode

                        #     })





                        
                        # main_doc.save(ignore_permissions=True)
                        # main_doc.submit()

                        
            #             i.base_amount = val.get("amount")
            #             i.foriegn_amount = val.get("base_amount")
            #             i.foriegn_currency = val.get("currency")
            # # doc.save()



@frappe.whitelist()
def update_cart(ic,barcode,ip):
    print(ip)
    res = list(ip)
    res.insert(3,'.')
    res = ''.join(res)
    print("res****************",res)

    


    fi = []
    items_list = frappe.db.get_all("Item",["name"])
    for i in items_list:
        fi.append(i.get("name"))
    
    
    
    if str(ic) in fi:
        print("yes")
    
    elif ic[1:] in fi:
       item =  frappe.get_doc("Item",ic[1:])
       rate =frappe.get_doc("Item Price",{'item_code':item.name})
       qty = float(res)/rate.price_list_rate
       items = {}
       uom = frappe.db.get_value("Item Barcode",{'parent':item.name},["uom"])
       items.update({
           "actual_qty":100,
           "barcode":barcode,
           "batch_no":"",
           "currency":"INR",
           "description":item.description,
           "is_stock_item":item.is_stock_item,
           "item_code":item.name,
           "item_name":item.item_name,
           "item_image":item.image,
           "price_list_rate":rate.price_list_rate,
           "serial_no":"",
           "stock_uom":item.stock_uom,
           "cprice":res,
           "qty":str(qty)
       })

       print("9242frwfwfwgwrg",items)

       return [items]

    
    else:
        print(ic,"no")
        
        

    





