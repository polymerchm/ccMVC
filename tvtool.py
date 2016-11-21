class TVTools(): # Mixin for TableViews
	def setTableViewItemsRow(self,row):
		for item in self.items:
			item['accessory_type'] = 'none'
		self.items[row]['accessory_type'] = 'checkmark'
