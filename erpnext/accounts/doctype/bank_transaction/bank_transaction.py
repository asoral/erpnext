# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from erpnext.controllers.status_updater import StatusUpdater
from frappe.utils import flt
from six.moves import reduce
from frappe import _
# from erpnext.accounts.doctype.bank_reconciliation_tool.bank_reconciliation_tool import check_matching,get_queries
class BankTransaction(StatusUpdater):
	def after_insert(self):
		self.unallocated_amount = abs(flt(self.withdrawal) - flt(self.deposit))

	def before_submitt(self):
		# get all matching payments for a bank transaction

		document_types = ['payment_entry', 'journal_entry']
		xyz = get_linked_payments(self.name,document_types)
		print("---------xyz",xyz)
		transaction = frappe.get_doc("Bank Transaction", self.name)
		bank_account = frappe.db.get_values(
			"Bank Account",
			transaction.bank_account,
			["account", "company"],
			as_dict=True)[0]
		(account, company) = (bank_account.account, bank_account.company)
		matching = check_matching(account, company, transaction, document_types)
		print("ref args-----matching",account,company,transaction,document_types)
		print("matching -pyyyy--",matching)
		if matching:
			self.payment_entries = []
			for row in matching:
				transaction.append('payment_entries',{
					"payment_document": row[1],
					"payment_entry": row[2],
					"allocated_amount": row[3]
				})
			transaction.save(ignore_permissions = True)


	def on_submit(self):
		# self.match_entries()
		self.before_submitt()
		# self.update_allocations()
		self.clear_linked_payment_entries()
		self.set_status(update=True)


	def on_update_after_submit(self):
		self.update_allocations()
		self.clear_linked_payment_entries()
		self.set_status(update=True)


	def update_allocations(self):
		if self.payment_entries:
			allocated_amount = reduce(lambda x, y: flt(x) + flt(y), [x.allocated_amount for x in self.payment_entries])
		else:
			allocated_amount = 0

		if allocated_amount:
			frappe.db.set_value(self.doctype, self.name, "allocated_amount", flt(allocated_amount))
			frappe.db.set_value(self.doctype, self.name, "unallocated_amount", abs(flt(self.withdrawal) - flt(self.deposit)) - flt(allocated_amount))

		else:
			frappe.db.set_value(self.doctype, self.name, "allocated_amount", 0)
			frappe.db.set_value(self.doctype, self.name, "unallocated_amount", abs(flt(self.withdrawal) - flt(self.deposit)))

		amount = self.deposit or self.withdrawal
		if amount == self.allocated_amount:
			frappe.db.set_value(self.doctype, self.name, "status", "Reconciled")

		self.reload()
	# def match_entries(self):

	def clear_linked_payment_entries(self):
		for payment_entry in self.payment_entries:
			if payment_entry.payment_document in ["Payment Entry", "Journal Entry", "Purchase Invoice", "Expense Claim"]:
				self.clear_simple_entry(payment_entry)

			elif payment_entry.payment_document == "Sales Invoice":
				self.clear_sales_invoice(payment_entry)

	def clear_simple_entry(self, payment_entry):
		frappe.db.set_value(payment_entry.payment_document, payment_entry.payment_entry, "clearance_date", self.date)

	def clear_sales_invoice(self, payment_entry):
		frappe.db.set_value("Sales Invoice Payment", dict(parenttype=payment_entry.payment_document,
			parent=payment_entry.payment_entry), "clearance_date", self.date)

def get_total_allocated_amount(payment_entry):
	return frappe.db.sql("""
		SELECT
			SUM(btp.allocated_amount) as allocated_amount,
			bt.name
		FROM
			`tabBank Transaction Payments` as btp
		LEFT JOIN
			`tabBank Transaction` bt ON bt.name=btp.parent
		WHERE
			btp.payment_document = %s
		AND
			btp.payment_entry = %s
		AND
			bt.docstatus = 1""", (payment_entry.payment_document, payment_entry.payment_entry), as_dict=True)

def get_paid_amount(payment_entry, currency):
	if payment_entry.payment_document in ["Payment Entry", "Sales Invoice", "Purchase Invoice"]:

		paid_amount_field = "paid_amount"
		if payment_entry.payment_document == 'Payment Entry':
			doc = frappe.get_doc("Payment Entry", payment_entry.payment_entry)
			paid_amount_field = ("base_paid_amount"
				if doc.paid_to_account_currency == currency else "paid_amount")

		return frappe.db.get_value(payment_entry.payment_document,
			payment_entry.payment_entry, paid_amount_field)

	elif payment_entry.payment_document == "Journal Entry":
		return frappe.db.get_value(payment_entry.payment_document, payment_entry.payment_entry, "total_amount")

	elif payment_entry.payment_document == "Expense Claim":
		return frappe.db.get_value(payment_entry.payment_document, payment_entry.payment_entry, "total_amount_reimbursed")

	else:
		frappe.throw("Please reconcile {0}: {1} manually".format(payment_entry.payment_document, payment_entry.payment_entry))

@frappe.whitelist()
def unclear_reference_payment(doctype, docname):
	if frappe.db.exists(doctype, docname):
		doc = frappe.get_doc(doctype, docname)
		if doctype == "Sales Invoice":
			frappe.db.set_value("Sales Invoice Payment", dict(parenttype=doc.payment_document,
				parent=doc.payment_entry), "clearance_date", None)
		else:
			frappe.db.set_value(doc.payment_document, doc.payment_entry, "clearance_date", None)

		return doc.payment_entry

# for bank reconcilation matching entries on submit
@frappe.whitelist()
def get_linked_payments(bank_transaction_name, document_types ):

	# get all matching payments for a bank transaction
	transaction = frappe.get_doc("Bank Transaction", bank_transaction_name)
	bank_account = frappe.db.get_values(
		"Bank Account",
		transaction.bank_account,
		["account", "company"],
		as_dict=True)[0]
	(account, company) = (bank_account.account, bank_account.company)
	matching = check_matching(account, company, transaction, document_types)
	return matching

def check_matching(bank_account, company, transaction, document_types):
	# combine all types of vocuhers
	print("check matching -------------------------------------------------",transaction.reference_number)
	company = company
	subquery = get_queries(transaction, document_types)
	print("------------  subquery",subquery)
	filters = {
			"amount": transaction.unallocated_amount,
			"payment_type" : "Receive" if transaction.deposit > 0 else "Pay",
			"reference_no": transaction.reference_number,
			"party_type": transaction.party_type,
			"party": transaction.party,
			"bank_account":  bank_account
		}
	print("filters--------------",filters)
	matching_vouchers = []
	for query in subquery:
		print("------------  query", query)
		abc = frappe.db.sql(query, filters)
		print("abc----------------------",abc)
		matching_vouchers.extend(
			frappe.db.sql(query, filters)
		)
	print("------------  matching_vouchers", matching_vouchers)
	return sorted(matching_vouchers, key = lambda x: x[0], reverse=True) if matching_vouchers else []

def get_queries(transaction, document_types):
	# get queries to get matching vouchers
	amount_condition = "="
	account_from_to = "paid_to" if transaction.deposit > 0 else "paid_from"
	queries = []

	if "payment_entry" in document_types:
		pe_amount_matching = get_pe_matching_query(amount_condition, account_from_to, transaction)
		queries.extend([pe_amount_matching])

	if "journal_entry" in document_types:
#		print("*********************Amt******",je_amount_matching)
		je_amount_matching = get_je_matching_query(amount_condition, transaction)
		print("*********************Amt******",je_amount_matching)
		queries.extend([je_amount_matching])

	# if transaction.deposit > 0 and "sales_invoice" in document_types:
	# 	si_amount_matching =  get_si_matching_query(amount_condition)
	# 	queries.extend([si_amount_matching])
	#
	# if transaction.withdrawal > 0:
	# 	if "purchase_invoice" in document_types:
	# 		pi_amount_matching = get_pi_matching_query(amount_condition)
	# 		queries.extend([pi_amount_matching])
	#
	# 	if "expense_claim" in document_types:
	# 		ec_amount_matching = get_ec_matching_query(bank_account, company, amount_condition)
	# 		queries.extend([ec_amount_matching])

	return queries

def get_pe_matching_query(amount_condition, account_from_to, transaction):
	# get matching payment entries query
	if transaction.deposit > 0:
		currency_field = "paid_to_account_currency as currency"
	else:
		currency_field = "paid_from_account_currency as currency"
	return  f"""
	SELECT
		(CASE WHEN reference_no=%(reference_no)s THEN 1 ELSE 0 END
		+ CASE WHEN (party_type = %(party_type)s AND party = %(party)s ) THEN 1 ELSE 0  END
		+ 1 ) AS rank,
		'Payment Entry' as doctype,
		name,
		paid_amount,
		reference_no,
		reference_date,
		party,
		party_type,
		posting_date,
		{currency_field}
	FROM
		`tabPayment Entry`
	WHERE
		paid_amount {amount_condition} %(amount)s
		AND docstatus = 1
		AND payment_type IN (%(payment_type)s, 'Internal Transfer')
		AND ifnull(clearance_date, '') = ""
		AND {account_from_to} = %(bank_account)s and reference_no = %(reference_no)s
	"""


def get_je_matching_query(amount_condition, transaction):
	# get matching journal entry query
	cr_or_dr = "credit" if transaction.withdrawal > 0 else "debit"
	return f"""

		SELECT
			(CASE WHEN je.cheque_no=%(reference_no)s THEN 1 ELSE 0 END
			+ 1) AS rank ,
			'Journal Entry' as doctype,
			je.name,
			jea.{cr_or_dr}_in_account_currency as paid_amount,
			je.cheque_no as reference_no,
			je.cheque_date as reference_date,
			je.pay_to_recd_from as party,
			jea.party_type,
			je.posting_date,
			jea.account_currency as currency
		FROM
			`tabJournal Entry Account` as jea
		JOIN
			`tabJournal Entry` as je
		ON
			jea.parent = je.name
		WHERE
			(je.clearance_date is null or je.clearance_date='0000-00-00')
			AND jea.account = %(bank_account)s
			AND jea.{cr_or_dr}_in_account_currency {amount_condition} %(amount)s
			AND je.docstatus = 1 and je.cheque_no = %(reference_no)s
	"""

