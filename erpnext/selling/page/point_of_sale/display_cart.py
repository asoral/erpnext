from frappe.utils import get_site_name 
import frappe
import screeninfo
# from Tkinter import *
# import webbrowser


def get_url(result):
    site_name = get_site_name(frappe.local.request.host) 
    print('FFFFFFFFFFjkkkkkkkkkkkkkxnhsGDXYU',site_name)
    # url = window.location.href
	# arr = url.split("/");
	# result = arr[0] + "//" + arr[2] + '/' + 'app' + '/'  + 'pos-display-cart'
    # print('**************************************result',result)
    # # # print(screeninfo.get_monitors())
    # webbrowser.open_new(result)
# def create_win():
#     def close(): win1.destroy();win2.destroy()
#     win1 = Toplevel()
#     win1.geometry('%dx%d%+d+%d'%(sw,sh,-sw,0))
#     Button(win1,text="Exit1",command=close).pack()
#     win2 = Toplevel()
#     win2.geometry('%dx%d%+d+%d'%(sw,sh,sw,0))
#     Button(win2,text="Exit2",command=close).pack()

# root=Tk()
# sw,sh = root.winfo_screenwidth(),root.winfo_screenheight()
# print "screen1:",sw,sh
# w,h = 800,600 
# a,b = (sw-w)/2,(sh-h)/2 

# Button(root,text="Exit",command=lambda r=root:r.destroy()).pack()
# Button(root,text="Create win2",command=create_win).pack()

# root.geometry('%sx%s+%s+%s'%(w,h,a,b))
# root.mainloop()





# // async getScreenDetails(){
# 	// 	console.log('window',window)
# 	// 	console.log(window.screen.isExtended)
# 	// 	console.log(window.getScreenDetails)
# 	// 	const screenDetails = window.getScreenDetails();
# 	// 	console.log(screenDetails)
# 	// 	console.log(window.location)
# 	// 		var url = window.location.href
# 	// 		var arr = url.split("/");
# 	// 		var result = arr[0] + "//" + arr[2] + '/' + 'app' + '/'  + 'pos-display-cart'
# 	// 		console.log(result)
# 	// 		const popup = window.open(
# 	// 				'result',
# 	// 				'My Popup',
# 	// 				'left=1920,top=0,width=1920,height=1080',
# 	// 				);
		
# 	// 				popup.moveTo(2500, 50);
			
		
# 	// }