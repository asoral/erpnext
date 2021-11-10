import frappe
import sendgrid
import os
from sendgrid.helpers.mail import *
from sendgrid import Mail
API_KEY = "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"
@frappe.whitelist(allow_guest = True)
def verify_email():
	# sg = sendgrid.SendGridAPIClient(API_KEY)
	# sg = sendgrid.SendGridAPIClient(api_key=os.environ.get(API_KEY))
	# sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
	# from_email = Email("notification@capitalvia.com")
	# to_email = Email("jagdaleomkar4@gmail.com")
	# msg = "you have became a user to fintastiq app from capitalVia your OTP is "
	# subject = "Welcome to CapitalVia"
	# mail = Mail(from_email, to_email, msg, subject)
	# response = sg.client.mail.send.post(request_body=mail.get())
	# return "Success"

	sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
	data = {
		"personalizations": [
			{
				"to": [
					{
						"email": "jagdaleomkar4@gmail.com"
					}
				],
				"subject": "Sending with SendGrid is Fun"
			}
		],
		"from": {
			"email": "notification@capitalvia.com"
		},
		"content": [
			{
				"type": "text/plain",
				"value": "Hey.............."
			}
		]
	}
	response = sg.client.mail.send.post(request_body=data)
	return "Success"
#
#from frappe.core.doctype.communication.email import make

# if frappe.db.exists("User Details",{"email": email}):
# return "User already exist"
# else:
# string = '0123456789'
# otp = ""
# length = len(string)
# print("OTP Generation")
# for i in range(4):
# otp += string[math.floor(random.random() * length)]

# fullname=name.split(" ", 1)
# first_name=fullname[0]
# last_name=fullname[1]
# user = frappe.get_doc({
# "doctype": "User Details",
# "email": email,
# "first_name": first_name,
# "last_name": last_name,
# "channel": channel,
# "fcm":fcm,
# "device_details":device_details,
# "user_status": "Signup email sent",
# # "mobile_no": mobile_no,
# "email_otp": otp,
# #"new_password": name + "@123",
# #"enabled": 1,
# #"send_welcome_email": False,
# #"user_type": "Website User",
# #"roles": [{"role": "Investor"}],
# })

# user.flags.ignore_permissions = True
# user.flags.ignore_password_policy = True
# user.insert()
# user.save()
#
# userid= frappe.db.sql("""select name from `tabUser Details` where email='{0}';""".format(email), as_dict=False)

# userdoc = frappe.get_doc({
# "doctype": "User",
# "email": email,
# "first_name": first_name,
# "last_name":last_name,
# "user_id":userid[0][0],
# "enabled": 1,
# "send_welcome_email": False,
# "user_type": "Website User",
# "roles": [{"role": "Investor"}],
# })

# userdoc.flags.ignore_permissions = True
# userdoc.flags.ignore_password_policy = True
# userdoc.insert()
# userdoc.save()

# if channel == "default":
# msg = "you have became a user to fintastiq app from capitalVia your OTP is " + otp
# subject = "Welcome to CapitalVia"
# make(subject = subject, content=msg, recipients=email,
# send_email=True, sender= 'notification@capitalvia.com')

# sendgrid
#sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
# sg = sendgrid.SendGridAPIClient(API_KEY)
# from_email = Email("notification@capitalvia.com")
# to_email = Email("jagdaleomkar4@gmail.com")
# msg = "you have became a user to fintastiq app from capitalVia your OTP is " + otp
# subject = "Welcome to CapitalVia"
# mail = Mail(from_email, to_email, msg, subject)
# response = sg.client.mail.send.post(request_body=mail.get())
# # sendgrid

# set default signup role as per Portal Settings
# default_role = frappe.db.get_value("Portal Settings", None, "default_role")
# if default_role:
#   user.add_roles(default_role)
# frappe.db.commit()
# return "success"
# else:
# frappe.db.commit()
# return "success"
# return "success"
