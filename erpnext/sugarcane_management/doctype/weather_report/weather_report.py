# Copyright (c) 2021, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe
from frappe.model.document import Document
from pyowm import OWM
from pyowm.utils import config
from pyowm.utils import timestamps

class WeatherReport(Document):
	def before_save(self):
		api = '804320718aa332369200faf1971816da'
		OpenWMap = pyowm.OWM(api)
		wt = frappe.db.get_value('Weather Report','a51952f063','city')
		Weather = OpenWMap.weather_at_place(wt)
		Data = Weather.get_weather()
		frappe.db.set_value('Weather Report','a51952f063','weather',Data)
		
	
	
