# coding: utf-8
''' DropDown 

A custom view that acts as a flyout selector, based on a ListView and button.  
It does not allow text input, as does jsbain's version.

Author: Steven Pollack, Ph.D.
Date:		July 26, 2015

'''


import ui,inspect,console
import _ui # needed for Beta 1.6

class _DropDownDelegate(object):
	
	def setitems(self,values):
		if not values:
			self.items = []
		if not isinstance(values[0],dict):
			self.items = [{'title':x, 'accessory_type':'none'} for x in values]
		else:
			self.items = []
			for item in values:
				if 'title' not in list(item.keys()):
					raise ValueError("invalid dictionary.  missing critical key")
				else:
					item['accessory_type']='none' # just in case its not there.
					self.items.append(item)
		self._row = 0
	
	def __init__(self,dd):
		self.dd = dd
		self.setitems(dd._data)

	def tableview_number_of_rows(self, tableview, section):
		# Return the number of rows in the section
		return len(self.items)

	def tableview_cell_for_row(self, tableview, section, row):
		# Create and return a cell for the given section/row
		cell = ui.TableViewCell()
		cell.text_label.text = self.items[row]['title']
		return cell


	def tableview_did_select(self, tableview, section, row):
		# Called when a row was selected.
		def animate():
			self.dd.tv.frame = self.dd.tvFrame
			self.dd.frame = tuple([self.dd.frame[x] for x in (0,1)]) + (self.dd.frame[2], self.dd.smallSize)
		self._row = row
		for i,_ in enumerate(self.items):
			self.items[i]['accessory_type'] = 'none'
		self.items[row]['accessory_type'] = 'checkmark'
		tableview.content_offset = (0,row*tableview.row_height+self.dd.offset_eps)
		tableview.reload_data()
		self.dd.expanded = False
		ui.animate(animate,duration=0.2)
		if self.dd.action:
			self.dd.action(self.dd,row)
			

			
		
		
class DropDown(ui.View):
	def __init__(self,	frame=(0,0,150,32),
										buttonSize = (32,32),
										data = "this is a test".split(),
										font = None,
										initialItem = 0,
										offset_eps = 0,
										action = None,
										fullSize = 300,
										name = 'dropdown'):
		self.frame = frame	
		self._position = [ self.frame[x] for x in (0,1)]
		self.smallSize = frame[3]
		self.bg_color = None	
		self.border_width = 0
		self.border_color = 'black'
		self.buttonSize	= buttonSize	
		self._data = data			
		self.delegate = _DropDownDelegate(self)
		if action:
			if inspect.isfunction(action) and len(inspect.getargspec(action).args) == 2:
				self.action = action
			else:
				raise TypeError('single argument function')	
		self.tvFrame = (0,0, self.frame[2] - self.buttonSize[0], self.buttonSize[1])
		self.tv = ui.TableView(frame=self.tvFrame)
		self.tv.row_height = self.smallSize
		self.tv.name = 'tableview'
		self.tv.allows_selection = True
		self.tv.delegate = self.tv.data_source = self.delegate
		self.tv.border_color = 'black'
		self.tv.border_width = 1
		self.button = ui.Button(frame = (self.frame[2]-self.buttonSize[0], 0) + self.buttonSize)
		self.button.bg_color = 'white'
		self.button.name = 'button'
		self.button.action = self.onArrow
		self.button.border_width = 1
		self.button.border_color = 'black'
		self.button.image=ui.Image.named('ionicons-arrow-down-b-24')
		self.expanded = False
		self.add_subview(self.tv)
		self.tv.frame = self.tvFrame
		self.add_subview(self.button)
		#self.fullSize = fullSize
		self.fullSize = self.smallSize*len(self._data) 
		self.smallSize = self.frame[3]
		self.offset_eps = offset_eps
		self.name = name
		self._hidden = False
		
	def send_to_back(self):
		self.tv.send_to_back()
		self.button.send_to_back()
		
	def bring_to_front(self):
		self.tv.bring_to_front()
		self.button.bring_to_front()
		
	def onArrow(self,button):
		#console.hud_alert("{}".format(self.expanded))
		self.bring_to_front()
		if not self.expanded:
			self.frame = tuple([self.frame[x] for x in (0,1)]) + (self.frame[2],self.fullSize)
			self.tv.frame = tuple([self.tv.frame[x] for x in (0,1)]) + (self.tv.frame[2],self.fullSize)
			self.expanded = True
		else:
			self.frame = tuple([self.frame[x] for x in (0,1)]) + (self.frame[2],self.smallSize)
			self.tv.frame = tuple([self.tv.frame[x] for x in (0,1)]) + (self.tv.frame[2],self.smallSize)
			self.tv.content_offset = (0,self.row*self.tv.row_height+self.offset_eps)
			self.expanded = False
												
		
	@property
	def position(self):
		return self._position

	@position.setter
	def position(self,value):
		self._position = value
		self.frame = self._position + tuple([self.frame[x] for x in (2,3)])
		
	@property
	def hidden(self):
		return self._hidden
		
	@hidden.setter
	def hidden(self,value):
		self._hidden = value
		self.button.hidden = value
		self.tv.hidden = value
		
	@property
	def data(self):
		return self._data
	
	@data.setter
	def data(self,value):
		self._data = value
		self.delegate.setitems(value)
		self.tv.reload_data()
		
	@property
	def row(self):
		return self.delegate._row
		
	@row.setter
	def row(self,value):
		if 0 <= value <= (len(self.delegate.items)-1):
			self.delegate._row = value
			self.tv.content_offset = (0,self.delegate._row*self.tv.row_height+self.offset_eps)
			
	@property
	def current(self):
		return self.delegate.items[self.delegate._row]
		
														
if __name__ == '__main__':
	def setRow():
		dd.row = 2
	
	def test(sender,row):
		print("from test row={}".format(row))
		print(sender.current)
		
		
	ddd = DropDown(data='Mary had a little lamb'.split(),action=test)
	dd = DropDown(data=[{'title':'fred'}, # will autopopulate 'accessory_type" entry
											{'title':'arthur', 'accessory_type':'none'},
											{'title':'tina', 'accessory_type':'none', 'flag':'a'}], action=test)
	root = ui.View(frame = (0,0,1000,900))
	root.bg_color = '#deff92'
	root.add_subview(ddd)
	dd.position = (50,50)
	root.present()

		
