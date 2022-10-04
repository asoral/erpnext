from filecmp import cmp
from frappe.frappe.utils.data import flt
from erpnext.erpnext import get_default_company
from erpnext.setup.utils import get_exchange_rate
from frappe.www.printview import get_print_style

import frappe


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



@frappe.whitelist()
def update_pos_invoice(values,inv,paid_amount,change_amount):
    val = eval(values)
    print("dict1",val)
    main_doc = frappe.get_doc("POS Invoice",inv)
    doc = frappe.db.get_all("Sales Invoice Payment",{'parent':inv},['*'])
    print("dict2",doc)
    lst = ["mode_of_payment"]

    

    for o in lst:
        # if o in val and doc:
        #     print("yes",val.get(o),doc.get(o))
    
        if doc:
            

            # print(doc.payments)
            for i in doc:
                print(i.mode_of_payment)
                for j in val.keys():
                    print("val******************",val,j)
                    if i.mode_of_payment == val[o]:
                        frappe.db.set_value("Sales Invoice Payment",i.name,"amount",val.get("amount"))
                        frappe.db.set_value("Sales Invoice Payment",i.name,"foriegn_amount",val.get("base_amount"))
                        frappe.db.set_value("Sales Invoice Payment",i.name,"foreign_currency",val.get("currency"))

                        
                        frappe.db.set_value("POS Invoice",inv,"base_change_amount",change_amount)
                        frappe.db.set_value("POS Invoice",inv,"change_amount",change_amount)
                        frappe.db.set_value("POS Invoice",inv,"paid_amount",paid_amount)



                        

                        
                        frappe.db.commit()

                        frappe.db.sql("""
                        Update `tabPOS Invoice` 
                        set docstatus = 1 , status = "Paid"
                        where name = '{0}' """.format(inv))

                        doc2 = {}

                        pos_inv = frappe.db.get_all("POS Invoice",{'name':inv},['*'])
                        pdoc = frappe.get_doc("POS Invoice",inv)
                        print("pdoc",pdoc.items)

                        for i in pos_inv:
                            print("items",i.items)
                            items = frappe.db.get_all("POS Invoice Item",{'parent':inv},['*'])
                            print("items2",items)
                            doc2.update({
                                "company_address":i.company_address,
                                "pos_profile":i.pos_profile,
                                "customer_name":i.customer_name,
                                "posting_date":i.posting_date,
                                "posting_time":i.posting_time,
                                "items":items,
                                "total":i.total,
                                "total_taxes_and_charges":i.total_taxes_and_charges,
                                "grand_total":i.grand_total,
                                "barcode":i.barcode

                            })





                        base_template_path = "frappe/www/printview.html"
                        template_path = (
                            "erpnext/pos_invoice.html"
                        )
                        

                        html = frappe.render_template(
                            template_path,
                            doc2
                        )

                        html2 = frappe.render_template(
                            base_template_path,
                            {"body": html, "css": get_print_style(), "title": "POS Invoice"},
                        )


                        return html2
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

       return [items]

    
    else:
        print(ic,"no")
        
        

    





