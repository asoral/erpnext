import frappe
from nepali_municipalities import NepalMunicipality

@frappe.whitelist()
def get_municipality(district):
    return NepalMunicipality(district).all_municipalities()

@frappe.whitelist()
def get_district():
    return NepalMunicipality().all_districts()

    