import frappe
from datetime import timedelta
from frappe.model.document import Document
from erpnext.hr.utils import share_doc_with_approver
from frappe.utils import add_days,time_diff,format_duration
import datetime

class Overtime(Document):
	def validate(self):
		self.validate_duplicate_date()
		self.validate_date_range()


	def validate_duplicate_date(self):
		date_list = []
		for i in self.get("overtime_details"):
			date = i.get("login").split(" ")[0]
			if date in date_list:
				m = "{0} is already present in overtime details table".format(date)
				frappe.throw(m)
			if date not in date_list:
				date_list.append(date)
	
	def validate_date_range(self):
		for i in self.get("overtime_details"):
			date = i.get("login").split(" ")[0]
			start = datetime.datetime.strptime(self.from_date, "%Y-%m-%d")
			end = datetime.datetime.strptime(self.to_date, "%Y-%m-%d")
			today = datetime.datetime.strptime(date, "%Y-%m-%d")
			if start <= today <= end:
				pass
			else:
				frappe.throw("Login date not in range.")

	@frappe.whitelist()
	def set_date(self):
		return add_days(self.from_date,29)

	@frappe.whitelist()
	def get_overtime(self,login,logout):
		total_working_hrs = time_diff(logout,login) 
		standard_working_hrs = timedelta(hours=9, minutes=00)
		if total_working_hrs > timedelta(hours=9, minutes=00):
			ot = total_working_hrs - standard_working_hrs
			ot_in_hrs = str(ot/3600)
			ot_time = round(float((ot_in_hrs.split(':'))[2]),2)
			return ot_time
		else:
			return 0