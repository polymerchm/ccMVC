# spinner class

import ui
from operator import add

def make_button(name, bg_image_name, frame):
	button = ui.Button(name=name)
	button.frame = frame
	button.bg_color = 'ivory'
	button.border_color = 'black'
	button.border_width = 1
	button.background_image = ui.Image.named(bg_image_name)
	button.enabled = True
	return button

def make_label(text, frame):
	label = ui.Label( )
	label.text = str(text)
	label.frame = frame
	label.text_color = 'black'
	label.border_color = 'black'
	label.alignment = ui.ALIGN_CENTER
	label.border_width = 1
	label.bring_to_front()
	return label

class Spinner(ui.View):
	''' creates a view with a data entry field and up/down arrows which allow for increment/decrement
	valid types are int, list, float.  A list will be fixed possibilities and limits are ignored
	'''

	def __init__(self, 	name='spinner',
											initialValue= 10,
											increment=1,
											limits=(0,100),
											action=None, # done if action was successful
											limitAction=None, #done if hit a limit
											textFraction = 0.75,
											fontSize = 12,
											spinnerSize=(80,80),
											wrap=False # if wrap is true and its a list, ignore limitAction and just wrap
											):

		self._value = self.initialValue = initialValue
		self.dataType = type(self._value)
		if self.dataType in [list,tuple]:
			self._value = self.initialValue = initialValue[0]
		elif not limits[0] <= self.initialValue <= limits[1]:
			raise ValueError("initalValue {} outside of limits {}".format(self._value,limits))
		self._increment = increment
		self._limits = limits
		self._position = (0,0)

		if self.dataType in (list,tuple):
			self.list = [x for x in initialValue]
			self._limits = len(self.list)-1
			self._increment = 1
			self._pointer = 0
		self.wrap = wrap
		self.action = action
		self.limitAction = limitAction if not wrap else None
		self.textFraction = textFraction
		self.spinnerSize = spinnerSize
		self.frame = (0,0)+(self.spinnerSize)
		self.fontSize = fontSize
		self.textWidth = int(self.textFraction*spinnerSize[1])
		self.buttonSize  = (int((1.0 - self.textFraction)*self.spinnerSize[0]), int(0.5*self.spinnerSize[1]))
		self.textSize =  (int(self.textFraction*self.spinnerSize[0]), spinnerSize[1])
		self.name = name
		self.add_ui()

	def add_ui(self):
		# add user interface elements
		self.background_color = "white"
		self.border_color = 'black'
		self.border_width = 1

		txtLocation = (0,0)+self.textSize
		self.label = make_label(self._value, txtLocation)
		self.label.font = ('<system>',self.fontSize)
		self.add_subview(self.label)

		txtOriginX,txtOriginY, txtWidth, txtHeight = txtLocation

		arrowX = txtOriginX + txtWidth + self.frame[0]
		upArrowY = txtOriginY
		dnArrowY = txtOriginY + txtHeight-self.buttonSize[1]

		upLocation = (arrowX,upArrowY)+self.buttonSize
		self.upArrow = make_button('upBtn', 'ionicons-arrow-up-b-24', frame=upLocation)
		self.upArrow.action = self.onArrow
		self.add_subview(self.upArrow)
		dnLocation = (arrowX,dnArrowY) + self.buttonSize
		self.downArrow = make_button('downBtn', 'ionicons-arrow-down-b-24', frame=dnLocation)
		self.downArrow.action = self.onArrow
		self.add_subview(self.downArrow)

	def updateLabel(self):
		if self.dataType in [list,tuple]:
			self.label.text = str(self._value)
		else: # a scalar
			if self._limits[0] <= self._value + self._increment <= self._limits[1]:
				self.label.text = str(self._value)
				
	@property
	def position(self):
		return self._position
		
	@position.setter
	def position(self,value):
		self._position = value
		self.frame = value + tuple(self.frame)[2:]

	@property
	def value(self):
		return self._value

	@value.setter
	def value(self,input):
		self._value = input
		self.updateLabel()

	@property
	def limits(self):
		return self._limits

	@limits.setter
	def limits(self,input):
		self._limits = input
		self.updateLabel()
		
	@property
	def pointer(self):
		return self._pointer
		
	@pointer.setter
	def pointer(self,input):
		self._pointer = input
		self._value = self.list[input]
		self.updateLabel()
		
	@property
	def increment(self):
		return self._increment
		
	@increment.setter
	def increment(self,input):
		self._increment = input

	def onArrow(self,sender):
		# you might want to consider tap-and-hold functionality
		direction = -1 if 'down' in sender.name.lower() else 1
		increment = self.increment * direction
		if self.dataType in [list,tuple]:
			if 0 <= self._pointer + increment <= self._limits:
				self._pointer += increment
				self._value = self.list[self._pointer]
				self.label.text = str(self._value)
				if self.action: self.action(self)
			else:
				if self.limitAction: 
					self.limitAction(self,sender)
				elif self.wrap:
					if self._pointer:
						self._pointer = 0
					else:
						self._pointer = self._limits
					self._value = self.list[self._pointer]
					self.label.text = str(self._value)
					if self.action: self.action(self)
		else: # a scalar
			if self._limits[0] <= self._value + increment <= self._limits[1]:
				self._value += increment
				self.label.text = str(self._value)
				if self.action: self.action(self)
			else:
				if self.limitAction: self.limitAction(self,sender)

	def reset(self):
		self._value = self.initialValue
		if self.action: self.action(self)

if __name__ == '__main__':

	def spinnerPrint(spinner,arrow):
		print(spinner.value)
		print(arrow.name)
		
	def hitLimit(spinner,arrow):
		import console
		console.hud_alert('stop!!! {}'.format(arrow.name) )

	view = ui.View(background_color = 'white')
	spinner1 = Spinner(name='Spinner1',
	                   initialValue = "this is a test".split(),spinnerSize=(60,50),textFraction=0.50,fontSize=16,limitAction=hitLimit,
											wrap=False)
	spinner2 = Spinner(name='Spinner2',initialValue = 0, increment = 2, 
	                   limits = (-10,10),action=spinnerPrint, limitAction=hitLimit)
	view.present('full_screen')
	spinner1.position = (110,150)
	spinner2.position = (300,150)
	view.add_subview(spinner1)
	view.add_subview(spinner2)
	print(spinner1.value)
	print(view.subviews[0].value)
