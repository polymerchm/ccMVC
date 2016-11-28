#!python3


"""
Chord Calculator
Progressions Branch


Copyright (c) August 19th, 2014 Steven K. Pollack
Version 6.0
March 3, 2015

iPAD MVC iOS device version

View objects:
-------------
tableview_roots     - root tone of chord
tableview_type      - chord type
tableview_inst_tune - instrument/tuning selector
tableview_filters   - filters selection
tableview_find      - display and interogate found chords
tableview_scale     - display various scales
tableview_prog      - display chord progressions
view_fretEnter      - custon view for fret number entry
view_neck           - drawing of neck/fingering
button_up           - previous chord shape/position
button_down         - next chord shape/position
button_arp          - play arpeggio
button_chord        - play chord
button_tuning       - play the open strings
button_cc_modew     - change mode (show fingering for a chord, or calculate chords from a fingering
                                       of display scales, or chords shapes in progression)
button_find         - display ther calculated fingering
slider_volume       - set play volume
slider_arp          - set arpegio and scale playback speed
lbl_fullchord       - displays the notes in the display chord (full chord, no filters)
lbl_definition      - displays the scale tones in a the full chord
                    - display relative major of greek mode
btn_sharpFlat       - forces sharps for flats for non-standard keys (not in the circle of fifths)
sp_span             - spinner for changing the span and recalculating chords based on span
button_save         - bring up a menu to save the current state of the filters, capos and instrument
button_load         - bring up a menu to load a saved state
button_config       - save current configuration
button_new          - brings up the instrument builder
"""

import sys
if '.' not in sys.path: sys.path.append('.')

#--- Main imports
import os.path, re, ui, console, sound, time, math, json, importlib
from operator import add,mul
import pubsub; importlib.reload(pubsub); from pubsub import pub
from pubsub.core import TopicManager

#delete all topics (need to do this in Pythonista)
defaultPublisher = pub.getDefaultPublisher()
topicmgr = pubsub.core.TopicManager()
topicmgr.clearTree()

#--- local imports
import tvtool; importlib.reload(tvtool); from tvtool import TVTools
import utilities; importlib.reload(utilities); from utilities import *
import chordcalc_constants; importlib.reload(chordcalc_constants)
import chordcalc_constants as cccInit
import Spinner; importlib.reload(Spinner);   from Spinner import Spinner
import Shield; importlib.reload(Shield);     from Shield import Shield
import DropDown; importlib.reload(DropDown); from DropDown import DropDown

SettingsFileName = 'settings.ini'
ConfigFileName = 'config.ini'

#--- CCC 
class CCC(object):
	''' chordcalc constants '''
	def __init__(self):
		self._ccc = None
		self.restoreConfig()
		self.configActionSet = False
		self.settingsActionsSet = False
		self.smv = None #settings main view
		self.cmv = None #configuration main view
		
	def __getitem__(self,key): # all instance to be subscriptable
		return self._ccc[key] if key in self._ccc else None

# Configuration maintenance code:
#  non-default items in filters, capos, chords, progressions, and instruments
			
	def restoreConfig(self):
		if not os.path.exists(ConfigFileName):
			console.hud_alert('config file missing, restoring','error',2)
			self.createConfig()
		fh = open(ConfigFileName,'r')
		try:
			self._ccc = json.load(fh)
		except:
			self.createConfig()
				
	def createConfig(self):
		if os.path.exists(ConfigFileName):
			try:
				resp = console.alert('config exists','Restore the "factory settings"?','OK')
				os.remove(ConfigFileName)
			except KeyboardInterrupt as e:
				return
	# read in the non-local data and write it out as a json object
		self._ccc = {}
		for constant in cccInit.__dict__.keys():
			if constant[0] != '_' and constant[0].isupper(): # a real constant
				self._ccc[constant] = cccInit.__dict__[constant]
				
		fh = open(ConfigFileName,'w')
		json.dump(self._ccc,fh,indent=1)
		fh.close()
		
	def configViewInit(self,configMainView): 
		''' actual contents of customized TableViews (instrument, filters, capos, etc. definned in SPECIAL_KEYS below) '''
		if not self.configActionSet:
			self.configActionSet = True # only set actions first time
			for subview in configMainView.subviews:
				if subview.name.endswith('Cancel'):
					subview.action = self.onCancelConfig
				elif subview.name.endswith('Save'):
					subview.action = self.onSaveConfig
				elif subview.name.endswith('Restore'):
					subview.action = self.onRestoreConfig
			self.cmv = configMainView
			self.cmv.hidden = True
			
	def onConfigMain(self,button):
		mainViewShield.conceal()
		self.cmv.hidden = False
		self.cmv.bring_to_front()	
			
	def onCancelConfig(self,button):
		mainViewShield.reveal()
		self.cmv.hidden= True
		
	def onSaveConfig(self,button):
		''' saves items lists for the below mentioned tableViews. '''
		specialKeys = ''' 
		CAPOS
		FILTER_LIST_CLEAN
		TUNINGS
		TUNING_LIST_CLEAN
		CHORD_LIST_CLEAN
		ROOT_LIST_CLEAN
		PROG_LIST_CLEAN
		'''.split()
		
		cccOut = {}
		for key in self._ccc.keys():
			if key not in specialKeys:
				cccOut[key] = self._ccc[key]
				
		cccOut['CAPOS'] = [{'title':capo['title'],'fret':0,'mask':capo['mask'],
		'accessory_type':'none'} for capo in capos.items] ########
		
		cccOut['TUNING_LIST_CLEAN'] = [{'title':tuning['title'],'notes':tuning['notes'],
		'span':tuning['span'],'octave':tuning['octave'],'accessory_type':'none'}
		for tuning in instrument.items] #####
		
		cccOut['TUNINGS'] = [(tuning['title'], [tuning['notes'],tuning['span']],tuning['octave'])
		for tuning in instrument.items] #####
		
		cccOut['FILTER_LIST_CLEAN'] = []
		for filter in filters.items:
			if not (filter['title'].endswith('_3') or filter['title'].endswith('_4')):
				cccOut['FILTER_LIST_CLEAN'].append({'title': filter['title'],'desc':filter['desc'],
						'accessory_type': 'none'})		
		cccOut['CHORD_LIST_CLEAN'] = [{'title':c['title'], 'fingering':c['fingering'],                  'accessory_type':'none'} for c in chord.items]
		
		cccOut['ROOT_LIST_CLEAN'] = [{'title':r['title'], 'noteValue':r['noteValue'], 'accessory_type': 'none'} for r in root.items]
		
		ccccOUT['PROG_LIST_CLEAN'] = [{'title':r['title'], 'chords':r['chords'], 'accessory_type':'none'}for r in progr.items]
		
		fh = open(ConfigFileName, 'w')
		json.dump(cccOut,fh,indent=1)
		fh.close()
		mainViewShield.reveal()
		self.cmv.hidden = True
		
	def onRestoreConfig(self,button):
		self._ccc = {}
		for constant in cccInit.__dict__.keys():
			if constant[0] != '_' and constant[0].isupper(): # a real constant
				self._ccc[constant] = cccInit.__dict__[constant]
				
		pub.sendMessage('restore.instrument',items=self._ccc['TUNING_LIST_CLEAN'])
		pub.sendMessage('restore.capos', items=self._ccc['CAPOS'])
		pub.sendMessage('restore.filters',items=self._ccc['FILTER_LIST_CLEAN'])
		#pub.sendMessage('restore.progressions',items=self._ccc['PROGR_LIST_CLEAN'])
		pub.sendMessage('setmode',mode='C')
		
		fh = open(ConfigFileName,'w')
		json.dump(ccc,fh,indent=1)
		fh.close()
		mainViewShield.reveal()
		self.cmv.hidden = True

		
	def settingsViewInit(self,settingsMainView):
		'''' save state of filters, instruments and capos in names file'''
		if not self.settingsActionsSet:
			self.settingsActionSet = True
			for subview in settingsMainView.subviews:
				if subview.name.endswith('OK'):
					subview.action = self.onOKSettings
					self.settingsBtnOK = subview
				elif subview.name.endswith('Cancel'):
					subview.action = self.onCancelSettings
				elif subview.name.endswith('Default'):
					subview.action = self.onDefaultSettings
					self.settingsBtnDefault = subview
				elif subview.name.endswith('Edit'):
					subview.action = self.toggleListEditSettings
				elif subview.name.endswith('Name'):
					self.settingsTextField = subview
				elif subview.name.endswith('List'):
					self.tvSettingsList = subview
					self.tvSettingsList.editing = False
					self.tvSettingsListShield = Shield(self.tvSettingsList)
			self.smv = settingsMainView	
				
	def onSettingsSave(self,button):
		x,y,w,h = self.smv.frame
		self.smv.frame = (300,300,w,h)
		mainViewShield.conceal()
		self.smv.hidden = False
		self.settingsTextField.enabled = True
		self.settingsBtnOK.enabled = True
		self.settingsBtnDefault.enabled = True
		self.tvSettingsListShield.conceal()
		self.smv.bring_to_front()
		
	def onSettingsLoad(self,button):
		#%%%%%%%%
		x,y,w,h = self.smv.frame
		self.smv.frame = (300,300,w,h)
		mainViewShield.conceal()
		self.smv.hidden = False
		self.settingsTextField.enabled = False
		self.settingsBtnOK.enabled = False
		self.settingsBtnDefault.enabled = False
		self.tvSettingsListShield.reveal()
		self.tvSettingsList.reload_data()
		self.smv.bring_to_front()
		#rest will be done by did_select of delegate
		
	def onOKSettings(self,button):
		global settings
		if self.settingsTextField.text in [x['title'] for x in settings.items]:
			console.hud_alert('Title already in use','error')
			return
		settingName = self.settingsTextField.text
		self.settingsTextField.text = ''
		theseCapos = [(item['title'],item['fret']) for item in capos.items if item['fret']]
		theseFilters = [item['title'] for item in filters.items if item['accessory_type'] == 'checkmark']
		thisInstrument = [item['title'] for item in instrument.items
		if item['accessory_type'] == 'checkmark'][0]
		
		item = {'title':settingName, 'capos':theseCapos,
		'filters':theseFilters, 'instrument':thisInstrument,'accessory_type':'none'}
		settings.items.append(item)
		settings.currentNumLines += 1
		
		fh = open(SettingsFileName,'w')
		json.dump(settings.items,fh,indent=1)
		fh.close()
		settings.delegator.reload_data()
		#%%%%%%%%%%
		mainViewShield.reveal()
		self.smv.hidden = True
		
		
	def onDefaultSettings(self,button):
		global settings
		theseCapos = [(item['title'],item['fret']) for item in capos.items if item['fret']]
		theseFilters = [item['title'] for item in filters.items if item['accessory_type'] == 'checkmark']
		thisInstrument = [item['title'] for item in instrument.items
		if item['accessory_type'] == 'checkmark'][0]
		
		item = {'title':'default', 'capos':theseCapos,
		'filters':theseFilters, 'instrument':thisInstrument}
		for i,entry in enumerate(settings.items):
			if entry['title'] == 'default':
				settings.items[i] = item
		self.tvSettingsList.reload_data()
		fh = open(SettingsFileName,'w')
		json.dump(settings.items,fh,indent=1)
		fh.close()
		#%%%%%%%%%%
		mainViewShield.reveal()
		self.smv.hidden = True
		
	def stopEditSettingsList(self):
		self.tvSettingsList.editing = False
		self.tvSettingsList.reload_data()
		fh = open(SettingsFileName,'w')
		json.dump(settings.items,fh,indent=1)
		fh.close()
		self.settingsTextField.enabled = True
		self.settingsBtnOK.enabled = True
		self.settingsBtnDefault.enabled = True
	
	def onCancelSettings(self,button):
		if self.tvSettingsList.editing: #finishing editing
			self.stopEditSettingsList()
		mainViewShield.reveal()
		self.tvSettingsList.editing = False
		self.smv.hidden = True
		
		
	def toggleListEditSettings(self,button):
		if self.tvSettingsList.editing: #finishing editing
			self.stopEditSettingsList()
		else: #start editing
			self.settingsTextField.enabled = False
			self.settingsBtnOK.enabled = False
			self.settingsBtnDefault.enabled = False
			self.tvSettingsList.editing = True
								
#--- Model	

class Model(object):
	''' primary ChordCalc Model '''
	def __init__(self,ccc):
		self._Constants = cccInit # master database for constants	
		self._ccc = ccc       # constants form configurato file, dictionary of lists/dictionalies
		self._Mode = 'C'       # str in ('C', 'I', 'S', 'P') for operating mode
		self._Root = None     # {'title':str NoteName, 'value':int NoteValue}
		self._ChordName = None   
		self._ChordNoteValues = None
		self._InstrumentName = ''
		self._InstrumentType = None
		self._InstrumentTuning = []
		self._InstrumentOctave = None
		self._Filters = None  # ('filtername1', 'filtername2',........)
		self._Capos = {}   # {fretnumber:(0/1,0/1,....),} 			
		self._ScaleName = ''	  # ('scalename','interval string TS3#')
		self._ScaleIntervals = ''
		self._Span = None	  # int number of frets to search for a chord range	
		self._playbackSpeed = None  # int
		self._Volume = None # int number
		
		self._Fingerings = []	
		self._FingeringPointer = 0
		self._NumberofFingerings = None
		
		self._ChordNotes = ''		
		self._ScaleNotes = None
		self._RootNoteValue = None
		self._RootNoteName = None
		self._ShowChordScale = False
		self._ChordScale = None
		self._multiDisplayText = ''
		self._is5StringBanjo = None
		self._ScaleFrets = None
		self._TwoOctaveScale=None
		
		self._FindKey = None
		self._FindChord = None
		
		self._ProgChordPointer = 0 # which progression
		self._ProgFingerings = None # array of array of progression fingerings
		self._ProgFingeringsPointers = None # array of progression fingerings pointers
		self._ProgChords = None # array of  progression chords and roots
		self._ProgCentroid = None # fret centroid of currently displayed chord
		self._ProgCentroidMode = False
	
#--- ---fretboard constants

		self.fretboard_NutOffset = 20
		self.fretboard_NumFrets = 14
		self.fretboard_OffsetFactor = 0.1
		self.fretboard_MarkerRadius = 10
		self.fretboard_FingerRadius = 15

		self.fretboard_fret5thStringBanjo = 5
		self.fretbaord_longTouchDelay = 0.5
		self.fretboard_location = None
		self.fretboard_mode = None

#--- ---playback constants
		
		self.play_arpMin = 0.05
		self.play_arpMax = 0.5
		self.play_arpSpeed = (self.play_arpMax + self.play_arpMin)/2.0
											
		pub.subscribe(self.changeMode,'changemode')	
		pub.subscribe(self.changeRoot,'changeroot')
		pub.subscribe(self.changeChord,'changechord')
		pub.subscribe(self.changeInstrument,'changeinstrument')
		pub.subscribe(self.changeFilters,'changefilters')
		pub.subscribe(self.changeScale,'changescale')		
		pub.subscribe(self.changeSpan,'changespan')
		pub.subscribe(self.changeSpeed,'changespeed')
		pub.subscribe(self.changeVolume,'changevolume')
		pub.subscribe(self.changeFingering,'changefingering')		
		pub.subscribe(self.changeConfig,'changeconfig')		
		pub.subscribe(self.newInstrument,'newinstrument')	
		pub.subscribe(self.fingerboardRequest,'fingerboardrequest')
		pub.subscribe(self.toggleChordScaleView,'toggleshowchordscaleview')
		pub.subscribe(self.setScaleFrets,'setscalefrets')
		pub.subscribe(self.setFindScale,'updatefindscale')
		pub.subscribe(self.setCapoFret,'setcapofret')
		pub.subscribe(self.changeSettings,'changesettings')
		pub.subscribe(self.setProgressions,'setprogressiondata')
		pub.subscribe(self.updateProgressionPointers,'updateprogressionpointers')
		pub.subscribe(self.updateCentroidSwitch,'centroidswitch')

			
		######################################		
		#handy status variable

	def changeMode(self,mode=None):
		self._Mode = mode
		self._FingeringPointer = 0
		self._Fingering = None
		self._ScaleFrets = None
		self._twoOctaveScale = []
		self.updateFretboard()
		
	def changeChord(self,name=None, chordTones=None):
		self._ChordName = name
		self._ChordNoteValues = chordTones
		self._Fingerings = self.calc_fingerings()
		self.updateFretboard()
		
	def changeRoot(self, root=None, value=None):
		self._RootNoteValue = value
		self._RootNoteName = root
		if self._Mode in ('C', 'S'):
			self._Fingerings = self.calc_fingerings()
		elif self._Mode == 'P':
			pub.sendMessage('updateProgressionSettings')
		if self._Mode == 'S':
			self._TwoOctaveScale = []
		self.updateFretboard()
		
	def updateCentroidSwitch(self,switch=None):
		self._ProgCentroidMode = switch

		
	def changeScale(self,scale=None):
		self._ScaleName = scale['title']
		self._ScaleIntervals = scale['scaleintervals']
		self._TwoOctaveScale = []
		self.updateFretboard()
		
		
	def setScaleFrets(self,location=None,mode=None):
		self.fretboard_location = location
		self.fretboard_mode = mode
		self._TwoOctaveScale = self.calc_two_octave_scale()
		self.updateFretboard()
		
	def setFindScale(self,pKey=None, pChord=None):
		self._FindKey = pKey
		self._FindChord= pChord
		self.updateFretboard()
		
	def setCapoFret(self,fret=None, mask=None):
		if not mask:
			del self._Capos[fret]
		else:
			self._Capos[fret] = mask
		if self._Mode in ('C', 'S'):
			self._Fingerings = self.calc_fingerings()
		elif self._Mode == 'P':
			pub.sendMessage('updateProgressionSettings')
		# clear out any only fretboard displaying lists
		self._ChordScale = []
		self._showChordScale = False
		self.updateFretboard()
									
	def changeInstrument(self,data=None):
		self._Span = data['span']
		self._InstrumentName = data['title']
		self._InstrumentTuning = data['notes']
		self._InstrumentType = self.instrument_type()
		self._InstrumentOctave = data['octave']
		self._is5StringBanjo = (self._InstrumentType[0] == 'banjo' and 
										len(self._InstrumentTuning) == 5)
		self._ShowChordScale = False
		self._ChordScale = []
		self._TwoOctaveScale = []
		self._Fingerings = self.calc_fingerings()
		self._FindKey = None
		self._FindChord = []
		self._Capos = {}
		self._ProgChordPointer = 0 
		self._ProgFingerings = None 
		self._ProgFingeringsPointers = None 
		self._ProgChords = None 
		self._ProgCentroid = None 

		
		pub.sendMessage('update.tuningbuttontext',text=self._InstrumentTuning)
		pub.sendMessage('syncspanspinner',span=self._Span)
		pub.sendMessage('syncnumstrings',numstr=len(self._InstrumentTuning))
		pub.sendMessage('updatetuningdisplay',text=self.tuningLabel(self._InstrumentTuning))
		pub.sendMessage('updateFilterSet',instrument_type=self._InstrumentType)
		pub.sendMessage('resetcapositems')
		pub.sendMessage('resetfound')
		pub.sendMessage('updatefind',chordlist=[])
		self.updateFretboard()

	def updateFretboard(self):
		if not self._InstrumentTuning:
			return	
		if self._Mode == 'C': # chord Finder
			if (self._ChordNoteValues and self._RootNoteName):
				self._ChordScale = self.calc_chord_scale()
				setChordSpelling(keyNoteValue=self._RootNoteValue, keyName=self._RootNoteName, 							chordNoteValues=self._ChordNoteValues)
		elif self._Mode == 'S':
			if (self._RootNoteName and self._ScaleName):
				self._ScaleNotes = self.calc_scale_notes()
				setRelativeMajorDisplay()
		elif self._Mode == 'I':
			if (self._FindKey and self._FindChord):			
				self._ChordScale = self.calc_chord_scale(pKey=self._FindKey, pChord=self._FindChord)
		elif self._Mode == 'P':
			if not self._ProgFingeringsPointers:
				return
			elif not self._ProgFingerings:
				return
			elif not self._ProgChordPointer:
				return
			else:
				theseFingerings = self._ProgFingerings[self._ProgChordPointer]
				thisPointer = self._ProgFingeringsPointers[self._ProgChordPointer]
				self._ProgFingerings[self._ProgChordPointer] = self.calc_fingerings()
				self._ProgCentroid = theseFingerings[thisPointer][-1]	
				setChordSpelling(keyNoteValue=self._RootNoteValue, keyName=self._RootNoteName, 							chordNoteValues=self._ChordNoteValues)		
		pub.sendMessage('update.fretboard',	
						mode=self._Mode, 
						fingerings=self._Fingerings,
						fingeringPointer = self._FingeringPointer, 
						scaleNotes=self._ScaleNotes,
						showScale=self._ShowChordScale,
						chordScale = self._ChordScale,
						twoOctaveScale = self._TwoOctaveScale,
						tuning=self._InstrumentTuning,
						type = self._InstrumentType,
						is5StringBanjo = self._is5StringBanjo,
						root = self._RootNoteName,
						chordName=self._ChordName,
						chordNoteValues=self._ChordNoteValues,
						rootNoteValue = self._RootNoteValue,
						scale = self._ScaleNotes,
						capos=self._Capos,
						progFingeringsPointers = self._ProgFingeringsPointers,
						progChordPointer = self._ProgChordPointer,
						progFingerings = self._ProgFingerings,
						progChordInfo = self._ProgChords,
						progCentroid = self._ProgCentroid	
						)
						
											
	def updateMultiDisplays(self):
		if self._Mode == 'C':
			midText,lowText = self.getChordSpelling()
		elif self._Mode == 'S':
			midText,lowText = self.getRelativeMajorDIsplay()
		elif self._Mode == 'I':
			midText = None
			lowText = None
		elif self._Mode == 'P':
			midText = 'TBD'
			lowText = 'TBD'
		pub.sendMessage('update.middledisplay',display=(midText,lowText))
	
	def tuningLabel(self,notes):
		'''return the notes for the current tuning'''
		note_string = ''
		note_accents = ["","'",'"',"`","^"]
		for note in notes:
			note_range,base_note = divmod(note,12)
			note_char = re.split('/', self._ccc['NOTE_NAMES'][base_note])[0]
			if not note_range:
				note_string += note_char
			else:
				note_string += note_char.lower() + note_accents[note_range-1]
			note_string += ' '
		return note_string.strip()
											
	def getChordSpelling(self):
		''' calculate and return the current Chord Spellings'''	
		try:
			chordTones = self._Fingering
			key = self._RootValue
			keyName = self._RootName
		except:
			return
		if not key:
			return
		NameString = ''
		ToneString = ''
		for tone in chordTones:
			NameChar = self._ccc['NOTE_NAMES'][(tone + key) % 12].split('/')
			if len(NameChar) == 1:
				NameChecked = NameChar[0]
			else:
				try:
					sf = self._ccc['CIRCLE_OF_FIFTHS'][keyName]
				except:
					sf = 1
				if sf > 0:
					NameChecked = NameChar[0]
				else:
					NameChecked = NameChar[1]
			NameString += NameChecked + ' '
			ToneString += self._ccc['SCALENOTES'][tone] + ' '
		return (NameString.strip(),ToneString.strip())	
			
	def getRelativeMajorDisplay(self):
		''' display the relative major for a greek mode'''
		key = self._RootValue
		scaletype = self._Scale
		scaleTone = self._ccc['TRUE_ROOT'].get(scaletype) #set to None for non-modal scales 
		if scaletype in ccc['TRUE_ROOT'].keys():
			text = "rel. to {}".format(self._ccc['NOTE_NAMES'][(key-scaleTone)%12])
			return (text,None) # middle and lower display texts/status
		else:
			return (None,None)	
			
	def updateProgressionPointers(self,nextChord=None,nextFingering=None):
		''' Change pointers to chords for fretboard viewing
			nextChord = -1 (previous) 0 no change +1 next
			nextFingering = -n (up neck) 0 (no change) +n (down neck
		'''
		if nextChord >= 0:
			if self._ProgCentroidMode and self._ProgCentroid:
				found = False
				for increment in (0.5, 1.0, 2.0, 3.0):
					for i,fingering in enumerate(self._ProgFingerings[self._ProgChordPointer]):
						centroid = fingering[-1]
						if abs(centroid - model._ProgCentroid) < increment:
							found = True
							pointer = i
							break
					if found:
						break
			else:
				pointer = self._ProgFingeringsPointers[self._ProgChordPointer]
				centroid = self._ProgFingerings[self._ProgChordPointer][0][-1]
			self._ProgChordPointer = nextChord
			self._ProgFingeringsPointers[self._ProgChordPointer] = pointer
			self._ProgCentroid = centroid	
			self._RootNoteName,self._RootNoteValue,_ = self._ProgChords[self._ProgChordPointer]	
		
		if nextFingering >= 0:
			self._ProgFingeringsPointers[self._ProgChordPointer] = nextFingering
			self._ProgCentroid = self._ProgFingerings[self._ProgChordPointer][nextFingering][-1]
		self.updateFretboard()
			
	def onCentroidSwitch(self,switch):
		self._ProgCentroidMode = switch.value

			
	def changeFilters(self,filters=None):
		self._Filters = filters
		if self._Mode in ('C', 'S'):
			self._Fingerings = self.calc_fingerings()
		elif self._Mode == 'P':
			pub.sendMessage('updateProgressionSettings')
		self.updateFretboard()
		
	def changeSettings(self,settings=None):
		# setttings contains the state of the various TableViews
# instrumetns
		for i in range(len(instrument.items)):
			if instrument.items[i]['title'] == settings['instrument']:
				thisInstrument = i # used to remember which was chosen instrument in the settings
				break
		instrument.setTableViewItemsRow(thisInstrument)	
		instrument.delegator.reload_data()
		self.changeInstrument(data=instrument.items[thisInstrument])
#filters
		filters.set_filters(instrument_type=self._InstrumentType)
		filters.filter_list = []
		for i in range(len(filters.items)):
			for filter in settings['filters']:
				if filter == filters.items[i]['title']:
					filters.items[i]['accessory_type'] = 'checkmark'
					filters.filter_list.append(filter)
		filters.delegator.reload_data()

		self.changeFilters(filters=filters.filter_list)
		
# capos		
		
		self._Capos = {}
		for i in range(len(capos.items)):
			capos.items[i]['accessory_type'] = 'none'
			capos.items[i]['fret'] = 0
			for capo in settings['capos']:
				if capo[0]  == capos.items[i]['title']:
					capos.items[i]['accessory_type'] = 'checkmark'
					capos.items[i]['fret'] = int(capo[1])
					self._Capos[int(capo[1])] = capos.items[i]['mask']
		capos.delegator.reload_data()
		mainView['view_settingsView'].hidden = True
		#%%%%%%%
		mainViewShield.reveal()
	
	def handleProgressions(self):
		pass
		
	def changeSpeed(self,**kwargs):
		pass
		
	def changeVolume(self,**kwargs):
		pass
		
	def changeFingering(self,pointer=None):
		self._FingeringPointer = pointer
		self.updateFretboard()
						
	def changeSpan(self,data=None):
		self._Span = data
		self.updateFretboard()
				
	def changeConfig(self,**kwargs):
		pass
		
	def newInstrument(self,**kwargs):
		pass
		
	def toggleChordScaleView(self):
		self._ShowChordScale = not self._ShowChordScale
		if not self._ShowChordScale:
			self._ChordScale = []
		else:
			self._ChordScale = self.calc_chord_scale()
		self.updateFretboard()

	
	def fingerboardRequest(self,**kwargs):
		pass
			
	def instrument_type(self): # return the type of instrument based on current selected
		# and diretory for the soundfile
		text = self._InstrumentName
		waveDir = 'default'
		done = False
		
		for instruments,directory in self._ccc['SOUND_FILE']:
			for thisInstrument in instruments:
				if re.match("{}".format(thisInstrument),text,flags=re.I):
					waveDir = directory
					if not os.path.exists(os.path.join('waves',waveDir)):
						done = True
						waveDir = 'default'
						break
					done = True
					break
			if done:
				break
		for type in 'guitar mando ukulele banjo'.split():
			if re.match("{}".format(type),text,flags=re.I):
				return type,waveDir
		return 'generic',waveDir	
		
	def calc_fingerings(self,chordtypeEntry=None):
		'''calculate the fingerings and fretboard positions for the desired chord
		if chordtypeEntry is passed, this is part of a progression '''
		
		if chordtypeEntry:
			key,note,chordtype = chordtypeEntry
			self._ChordNoteValues = chord.getNotesByName(chordtype)
		else:
			if self._RootNoteName: # remember the note value of "C" is =
				key = self._RootNoteValue
				note = self._RootNoteName  # since "C" has a note value of zero, use note title as indicator
			else:
				return None
			if self._ChordName:
				chordtype = self._ChordName
			else:
				return None
		if self._InstrumentName:
			tuning = self._InstrumentTuning
			span = self._Span
		else:
			return None
			
		filterSet = self._Filters if self._Filters else []
			
		result = None
		fingerPositions = []
		fingerings = []
		result = []
		for position in range(0,fretboard.numFrets-span):
			fingeringThisPosition = self.findFingerings(position)
			if fingeringThisPosition:
				fingerings = fingerings + fingeringThisPosition
		fingerings = uniqify(fingerings,idfun=(lambda x: tuple(x)))
		if fingerings:
			for fingering in fingerings:
				fingerMarker = fretboard.fingeringDrawPositions(key,chordtype,tuning,fingering)
				fingerPositions.append(fingerMarker)
			for fingering,drawposition in zip(fingerings,fingerPositions):
				chordTones = []
				for entry in drawposition:
					chordTones.append(entry[2])
				result.append((drawposition,chordTones,fingering))
			if filters:
				result = apply_filters(filterSet, result)
				if result:
					result = uniqify(result,idfun=(lambda x: tuple(x[2])))
		self._FingeringPointer = 0 
		return result
		
		
	def findFingerings(self,position):
		# Get valid frets on the strings
		
		validfrets = self.findValidFrets(position)
		
		# Find all candidates
		candidates = self.findCandidates(validfrets)
		
		# Filter out the invalid candidates
		candidates = self.filterCandidates(candidates)
		
		return candidates
		
	# For a given list of starting frets and span, find the ones that are in the chord for that tuning
	# Returns a list of valid frets for each string
	# Open strings are included if valid
	
	def findValidFrets(self,position):	
		strings = []
		nutOffsets = self.capoOffsets()
		for i,string in enumerate(self._InstrumentTuning):
			# offset 5 string banjo
			if self._is5StringBanjo and i == 0:
				string -= self.fretboard_fret5thStringBanjo
			frets = []
			if nutOffsets[i] <= position:
				start = position
				stop = position + self._Span+1
			elif position <= nutOffsets[i] <= position+self._Span+1:
				start = nutOffsets[i]
				stop = position + self._Span+1
			else: #behind the capo
				continue
			searchrange = [x for x in range(start,stop)]
			if position != 0: # include open strings is not at pos 0
				searchrange = [nutOffsets[i]] + searchrange
			for fret in searchrange:
				for chordrelnote in self._ChordNoteValues:
					note = (string + fret) % 12
					chordnote = (self._RootNoteValue + chordrelnote) % 12
					if note == chordnote:
						frets.append(fret)
			strings.append(frets)
		return strings
		
		
		
	# Finds all candidate fingerings, given all valid frets
	# Includes strings that should not be played
	# Note that this is just a permutation function and is independent of keys, tunings or chords
	
	
	
	def findCandidates(self,validfrets):
		# Set up the counter which will track the permutations
		max_counter = []
		counter = []
		candidatefrets = []
		if not validfrets:
			return None
		for string in validfrets:
			# Include the possibility of not playing the string
			# Current approach prioritises open and fretted strings over unplayed strings
			candidatefrets.append(string + [-1])
			max_counter.append(len(string))
			counter.append(0)
		l = len(counter)-1
		
		# Number of possible permutations
		numperm = 1
		for c in max_counter:
			numperm *= c+1
			
		candidates = []
		# Permute
		for perm in range(numperm):
			# get the candidate
			candidate = []
			for string, fret in enumerate(counter):
			
				candidate.append(candidatefrets[string][fret])
				
			# increment counter, starting from highest index string
			for i, v in enumerate(counter):
				if counter[l-i] < max_counter[l-i]:
					counter[l-i] += 1
					break
				else:
					counter[l-i] = 0
					
			candidates += [candidate]
		return candidates
		
		
		
	# Tests whether a fingering is valid
	# Should allow various possibilities - full chord, no 5th, no 3rd, no root, etc
	
	def isValidChord(self,candidate):
		filterSet = self._Filters
		if not filterSet:
			filterSet = []
			
		result = True
		
		# which chord notes are present?
		present = {}
		for chordrelnote in self._ChordNoteValues:
			# assume chord notes are not present
			present[chordrelnote] = False
			chordnote = (self._RootNoteValue + chordrelnote) %12
			for i, v in enumerate(candidate):
				# ignore unplayed strings
				if candidate[i] != -1:
					note = (self._InstrumentTuning[i] + candidate[i]) % 12
					if chordnote == note:
						present[chordrelnote] = True
						break
						
						
		# do we accept this fingering? depends on the option
		for note in present.keys():
			if present[note] == False:
				if 'FULL_CHORD' in filterSet:
					result = False
					break
				if 'NO3RD_OK' in filterSet:
					if note == 4 or note == 3:
						continue
				if 'NO5TH_OK' in filterSet:
					if note == 7:
						continue
				if 'NOROOT_OK' in filterSet:
					if note == 0:
						continue
			result = result & present[note]
		return result
		
		
	# Tests if a given note is in the chord
	# Not used here
	
	
		
	# Filter out the invalid chords from the list of candidates
	# Criteria for invalid chords may vary
	# Returns the list of valid chords
	
	def filterCandidates(self,candidates):	
		if not candidates:
			return None
		newlist = []
		for candidate in candidates:
			if self.isValidChord(candidate):
				newlist += [candidate]
		return newlist
			
	def fingeringDrawPositions(self,fingering):
		""" given a fingering,chord and tuning information and virtual neck info,
		return the center positions all markers.  X and open strings will be
		marked at the nut"""
		scaleNotes = self.getScaleNotes(key, chordtype, tuning, fingering)
		#if len(scaleNotes) != len(fingering):
		chordDrawPositions = []
		numStrings,offset,ss = self.stringSpacing()
		for i,fretPosition in enumerate(fingering): #loop over strings, low to high
			try:
				note = scaleNotes[i]
			except:
				continue
			atNut = None
			xpos = offset + i*ss
			if fretPosition in [-1,0]: #marker at nut
				ypos = int(0.5* self.nutOffset)
				atNut = 'X' if fretPosition else 'O'
			else:
				ypos = self.fretboardYPos(fretPosition)
			chordDrawPositions.append((xpos,ypos,note,atNut))
		return chordDrawPositions
		
	def calc_two_octave_scale(self):
		''' given a starting (string,scaletoneIndex) calculate a two octave scale across the 
		strings
		returns a 2D tupple of strings and frets
		modes:
		normal                          : referenceFret is the starting fret
		down                                  : referenceFret continually updated
		open                                  : favor open strings
		FourOnString  : favor 4 notes per string (max)'''
		
		mode = self.fretboard_mode if self.fretboard_mode else 'normal'
		key = self._RootNoteValue
		if self._ScaleIntervals:
			scaleintervals = self._ScaleIntervals
		else:
			return None
			
		if self._InstrumentName:
			tuning = self._InstrumentTuning
		else:
			return None
			
		intervals = [0]
		for letter in scaleintervals:
			if letter == 'S':
				intervals.append(1)
			elif letter == 'T':
				intervals.append(2)
			else:
				intervals.append((int(letter)))
				
		nextNote = key
		notesInScale = [nextNote,]
		for interval in intervals[1:]:
			nextNote += interval
			notesInScale.append(nextNote % 12)
			
		scale_notes = self._ScaleNotes
		fretsOnStrings = []
		tonesOnStrings = []
		
		for i,string in enumerate(scale_notes):
			frets = [x[0] for x in string]
			fretsOnStrings.append(frets)
			tones = [x[0] + tuning[i] for x in string]
			tonesOnStrings.append(tones)
			
		tonesOnStrings.append([-1 for x in range(len(tonesOnStrings[0]))])
		
		numNotes = 2*len(scaleintervals) + 1
		numStrings = len(tuning)
		thisString,thisStringFret = self.fretboard_location
		
		tone = thisStringFret + tuning[thisString]
		tonesInTwoOctaveScale = [tone]
		for octave in [1,2]:
			for interval in intervals[1:]:
				tone += interval
				tonesInTwoOctaveScale.append(tone)
		referenceFret = thisStringFret # used to anchor the scale
		try:
			thisIndex = fretsOnStrings[thisString].index(thisStringFret)
		except ValueError:
			console.hud_alert('error, line793ish, see console')
			print (fretsOnStrings[thisString], thisStringFret)
		scaleNotes = [self.fretboard_location]
		thisStringCount = 1 if thisStringFret else 0
		nextStringNote = scale_notes[thisString+1][1]
		nextIndex = 0
		# always look to see if next note is on next string
		for nextTone in tonesInTwoOctaveScale[1:]: # first tone already in place
			try:
				thisIndex = tonesOnStrings[thisString][thisIndex:].index(nextTone) + thisIndex
				onThisString = True
			except ValueError:
				onThisString = False
			try:
				nextIndex = tonesOnStrings[thisString+1][nextIndex:].index(nextTone) + nextIndex
				onNextString = True
			except ValueError:
				nextIndex = 0
				onNextString = False
				
			if not onThisString: #not on this string
				if not onNextString: # nor here, must be done.
					return scaleNotes
				else: # not on current string, is on next string, save and update
					nextFret = fretsOnStrings[thisString+1][nextIndex]
					scaleNotes.append((thisString+1,nextFret))
					if mode == 'down':
						referenceFret = nextFret
					thisString += 1
					if thisString == numStrings + 1: # on phantom string
						return scaleNotes
					thisIndex = nextIndex
					nextIndex = 0
					thisStringCount = 1 if nextFret else 0
			else:
				if onNextString: # On both strings
					thisFret = fretsOnStrings[thisString][thisIndex]
					nextFret = fretsOnStrings[thisString+1][nextIndex]
					thisDelta = abs(referenceFret - thisFret)
					nextDelta = abs(referenceFret - nextFret)
					if mode == 'open':
						if nextFret == 0:
							scaleNotes.append((thisString+1,0))
							thisString += 1
							thisIndex = nextIndex
							continue # next tone
					if mode == 'FourOnString' and thisStringCount == 4:
						thisString += 1
						scaleNotes.append((thisString,nextFret))
						thisIndex = nextIndex
						thisStringCount = 1 if nextFret else 0
						continue
					if thisDelta < nextDelta: # stay in this string
						scaleNotes.append((thisString,thisFret))
						if mode == 'down':
							referenceFret = thisFret
					else:
						thisString += 1
						scaleNotes.append((thisString,nextFret))
						if mode == 'down':
							referenceFret = nextFret
						thisIndex = nextIndex
						nextIndex = 0
						thisStringCount = 1
				else: #just on this string
					thisFret = fretsOnStrings[thisString][thisIndex]
					scaleNotes.append((thisString,thisFret))
					if thisFret: #don't count open string as a fingerednote
						thisStringCount += 1
					if mode == 'down':
						referenceFret = fretsOnStrings[thisString][thisIndex]
		return scaleNotes

		
	def capoOffsets(self):
		''' calculate and return the offsets due to the applied capos'''
		numStrings = len(self._InstrumentTuning)
		offsets = [0]*numStrings
		if not self._is5StringBanjo:
			for fret in self._Capos.keys():
				mask = self._Capos[fret]
				for i in range(numStrings):
					value = fret if mask[i] else 0
					offsets[i] = max(offsets[i],value)
		else: # 5 string banjo
			offsets = [self.fretboard_fret5thStringBanjo,0,0,0,0]
			for fret in self._Capos.keys():
				mask = self._Capos[fret]
				if len(mask) == 1:
				# is the fifth string
					offsets[0] = max(offsets[0],fret)
				else:
					for i in range(1,5):
						value = fret if mask[i] else 0
						offsets[i] = max(offsets[i],value)
		return offsets
		
	def getScaleNotes(self,fingering):
		scalenotes = []
		for i, v in enumerate(fingering):
			if v == -1:
				scalenotes.append('X')
			else:
				effTuning = self._InstrumentTuning[i]
				if self._is5StringBanjo and i == 0:
					effTuning = self._InstrumentTuning[i] - self.fretboard_fret5thStringBanjo
					
				fingerednote = (self._InstrumentTuning[i] + fingering[i]) % 12
				for chordrelnote in self._ChordNoteValues:
					chordnote = (self._RootNoteValue + chordrelnote) % 12
					if fingerednote == chordnote:
						scalenotes.append(ccc['SCALENOTES'][chordrelnote])
		return scalenotes
		
	def calc_chord_scale(self,pKey=None, pChord=None): #
		_key = pKey if self._Mode == 'I' else self._RootNoteValue
		if pChord:
			_chord = pChord
		elif self._Fingerings:
			_chord = self._ChordNoteValues
		else:
			return None
		# calculate notes in the current key
		chordNotes = [(x + _key) % 12 for x in _chord]
		capoOffsets = self.capoOffsets()
		scale = []
		for i,openString in enumerate(self._InstrumentTuning):
			thisString = []
			for fret in range(capoOffsets[i],self.fretboard_NumFrets+1): # zero is the open string
				tone = (openString + fret) %12
				if tone in chordNotes:
					thisString.append((fret-1,(tone - _key)%12))
			scale.append(thisString)
		return scale
		
	def calc_scale_notes(self):
		''' calculate the scale notes for the curent key, instrument and scale type'''
		key = self._RootNoteValue
		if self._ScaleName:
			scaleintervals = self._ScaleIntervals
		else:
			return None
		if self._InstrumentTuning:
			tuning = self._InstrumentTuning
		else:
			return None
		# format of the returned data is [[[fret, scalenote, scaletone, octave],.....numer on string
		#                                                                         ] length = numStrings
		# first unpack the scale spacing from the string
		
		capoOffsets = self.capoOffsets()
		intervals = [0]
		for letter in scaleintervals:
			if letter == 'S':
				intervals.append(1)
			elif letter == 'T':
				intervals.append(2)
			else:
				intervals.append((int(letter)))
				
		nextNote = key
		notes = [nextNote]
		for interval in intervals[1:]:
			nextNote += interval
			notes.append(nextNote % 12)
			
		scaleNotes= []
		for i,string in enumerate(tuning):
			thisString = []
			for fret in range(capoOffsets[i],self.fretboard_NumFrets+1):
				note = (fret + string) % 12
				if note in notes:
					thisString.append((fret,note))
			scaleNotes.append(thisString)
		return scaleNotes
		
	def setProgressions(self,progFingerings=None, progChords=None):	
		if not NoneOrNoneList(progFingerings):
			self._ProgChordPointer = 0
			self._ProgFingerings = progFingerings
			self._ProgFingeringsPointers = [0 for x in range(len(progFingerings))]
			self._ProgChords = progChords
			self._ProgressionCentroidList = []
			chordList = []
			for entry in self._ProgFingerings:
				fingeringList = []
				for fingering in entry:
					centroid = chordFingeringCentroid(fingering[2])
					temp = [x for x in fingering]
					temp.append(centroid)
					fingeringList.append(temp)			
				fingeringList = sorted(fingeringList,key=lambda  x:x[3])
				chordList.append(fingeringList)
			self._ProgFingerings = chordList #sorted by fingering centroids
			self.updateFretboard()

			
				
		
#===============================
				
def apply_filters(filters,fingerings):
	''' for the current fingerings and filters, return only those chords that apply'''
	filter_constraint = {'FULL_CHORD':("R b3 3 #5 5".split(),3)}
	instrumentType,_ = model.instrument_type()
	if not filters:
		return fingerings
	filtered = []
	temp_fingerings = fingerings
	if 'FULL_CHORD' in filters:   # must have at least R,3 and 5 triad
		for fingering in temp_fingerings:
			notes,numNotes = filter_constraint['FULL_CHORD']
			if len(set(fingering[1]).intersection(notes)) == numNotes:
				filtered.append(fingering)
		temp_fingerings = filtered
		
	filtered = []
	if 'NO_DEAD' in filters : #remove all with dead notes
		for fingering in temp_fingerings:
			if 'X' not in fingering[1]:
				filtered.append(fingering)
		temp_fingerings = filtered
		
	filtered = []
	if 'NO_OPEN' in filters:
		for fingering in temp_fingerings:
			open_check = []
			for string in fingering[0]:
				open_check.append(string[3])
			if 'O' not in open_check:
				filtered.append(fingering)
		temp_fingerings = filtered
		
	filtered = []
	if 'HIGH_4' in filters:
		for fingering in temp_fingerings:
			validChord = True
			for i,string in enumerate(fingering[0]):
				if i in [0,1]:
					if string[3] != 'X':
						validChord = False
						break
				else:
					if string[3] == 'X':
						validChord = False
						break
			if validChord:
				filtered.append(fingering)
		temp_fingerings = filtered
		
	filtered = []
	if 'LOW_4' in filters:
		for fingering in temp_fingerings:
			validChord = True
			for i,string in enumerate(fingering[0]):
				if i in [4,5]:
					if string[3] != 'X':
						validChord = False
						break
				else:
					if string[3] == 'X':
						validChord = False
						break
			if validChord:
				filtered.append(fingering)
		temp_fingerings = filtered
		
	filtered = []
	if 'HIGH_3' in filters: #for mandolin, allow for root or 5th to be abandoned
		for fingering in temp_fingerings:
			validChord = True
			for i,string in enumerate(fingering[0]):
				if i == 0:
					if string[3] != 'X':
						if fingering[1][i] in ['R','#5', '5']:
							fingering[1][i] = 'X'
							fingering[0][i] = (fretboard.nutPosition[i][0],fretboard.nutPosition[i][1],'X','X')
							break
						validChord = False
						break
				else:
					if string[3] == 'X':
						validChord = False
						break
			if validChord:
				filtered.append(fingering)
		temp_fingerings = filtered
		
	filtered = []
	if 'LOW_3' in filters:
		for fingering in temp_fingerings:
			validChord = True
			for i,string in enumerate(fingering[0]):
				if i == 3:
					if string[3] != 'X':
						if fingering[1][i] in ['R','#5','5'] :# for mandolin, allow for root or 5th to be abandoned
							fingering[1][i] = 'X'
							fingering[0][i] = (fretboard.nutPosition[i][0],fretboard.nutPosition[i][1],'X','X')
							break
						validChord = False
						break
				else:
					if string[3] == 'X':
						validChord = False
						break
			if validChord:
				filtered.append(fingering)
		temp_fingerings = filtered
		
	filtered = []
	if 'DOUBLE_STOPS' in filters and instrumentType == 'mando': # create adjacent string double stops for the chords
		numStrings = len(fingerings[0][1])
		for fingering in temp_fingerings:
			for i,string in enumerate(fingering[1]):
				if i+1 == numStrings:
					break
				else:
					nextString = fingering[1][i+1]
				if string == 'X' or nextString == 'X': continue
				if string != nextString: #rebuild the fingering as a double stop for this pair
					field1 = []
					field2 = []
					field3 = []
					j = 0
					while j < numStrings:
						if j < i or j > i+1:
							field1.append((fretboard.nutPosition[j][0],fretboard.nutPosition[j][1],'X','X'))
							field2.append('X')
							field3.append(-1)
							j += 1
						else:
							for index in [j,j+1]:
								field1.append(fingering[0][index])
								field2.append(fingering[1][index])
								field3.append(fingering[2][index])
							j += 2
					entry = (field1,field2,field3)
					filtered.append(entry)
		temp_fingerings = filtered
		
	filtered = []
	if 'NO_WIDOW' in filters: #remove isolated dead string (but not first or last)
		numStrings = len(fingerings[0][1])
		for fingering in temp_fingerings:
			validChord = True
			for i,string in enumerate(fingering[1]):
				if (i == 0 or i == numStrings-1) and string == 'X' : #outside strings
					continue
				if string == 'X':
					validChord = False
					break
			if validChord:
				filtered.append(fingering)
		temp_fingerings = filtered
	unique =  uniqify(temp_fingerings,idfun=(lambda x: fingeringToString(x[2])))
	return unique
	
	
def tuningLabel(notes):
	'''return the notes for the current tuning'''
	note_string = ''
	note_accents = ["","'",'"',"`","^"]
	for note in notes:
		note_range,base_note = divmod(note,12)
		note_char = re.split('/', ccc['NOTE_NAMES'][base_note])[0]
		if not note_range:
			note_string += note_char
		else:
			note_string += note_char.lower() + note_accents[note_range-1]
		note_string += ' '
	return note_string.strip()
		
def setChordSpelling(keyNoteValue=None, keyName=None, chordNoteValues=None):
	''' calculate and display the current Chord Spelling'''	
	if not keyName:
		return
	outString = ''
	defString = ''
	for tone in chordNoteValues:
		outChar = ccc['NOTE_NAMES'][(tone + keyNoteValue) % 12].split('/')
		if len(outChar) == 1:
			outChecked = outChar[0]
		else:
			try:
				sf = ccc['CIRCLE_OF_FIFTHS'][keyName]
			except:
				sf = 1
			if sf > 0:
				outChecked = outChar[0]
			else:
				outChecked = outChar[1]
		outString += outChecked + ' '
		defString += ccc['SCALENOTES'][tone] + ' '
	mainView['lbl_fullchord'].hidden = False
	mainView['lbl_fullchord'].text = outString.strip()
	mainView['lbl_definition'].hidden = False
	mainView['lbl_definition'].text = defString.strip()
	return (outString.strip(),defString.strip())



		
def setRelativeMajorDisplay():
	''' display the relative major for a greek mode'''
	key = model._RootNoteValue
	scaletype = model._ScaleName
	scaleTone = ccc['TRUE_ROOT'].get(scaletype) #set to None for non-modal scales
	labelName = 'lbl_definition' 
	if scaletype in ccc['TRUE_ROOT'].keys():
		text = "rel. to {}".format(ccc['NOTE_NAMES'][(key-scaleTone)%12])
		mainView[labelName].text = text
		mainView[labelName].hidden = False
	else:
		mainView[labelName].hidden = True
						
def drawFingerboard(fingerboard):
	if fingerboard.tuning:
	# draw fingerboard
		startX = 0
		startY = 0
		width = fingerboard.width
		height = fingerboard.height
		if fingerboard.is5StringBanjo:
			segment = int(width/5.0)
			width -= segment
			startX = segment
		ui.set_color('#4C4722')
		fb = ui.Path.rect(startX, startY, width, height)
		fb.fill()
		
	# draw nut
	
		nut = ui.Path.rect(startX,startY,width,fingerboard.nutOffset)
		ui.set_color('#ECF8D7')
		nut.fill()
		
		if fingerboard.is5StringBanjo: # draw 5th string segment
			radius = 30
			fret5SB = fingerboard.fret5thStringBanjo
			ui.set_color('#4C4722')
			fretboard = ui.Path.rect(0,fingerboard.fretDistance(fingerboard.scale(),fret5SB-1)+radius,segment,height-radius)
			fretboard.fill()
			fretboard = ui.Path.rect(radius,fingerboard.fretDistance(fingerboard.scale(),fret5SB-1),segment-radius,radius)
			fretboard.fill()
			semi = ui.Path()
			semi.move_to(radius,fingerboard.fretDistance(fingerboard.scale(),fret5SB-1)+radius)
			semi.add_arc(radius,fingerboard.fretDistance(fingerboard.scale(),fret5SB-1)+radius,radius,0,270)
			semi.close()
			semi.fill()
#
			square = ui.Path.rect(segment-radius,fingerboard.fretDistance(fingerboard.scale(),fret5SB-1)-radius,radius,radius)
			square.fill()
			semi = ui.Path()
			semi.move_to(segment-radius,fingerboard.fretDistance(fingerboard.scale(),fret5SB-1)-radius)
			semi.add_arc(segment-radius,fingerboard.fretDistance(fingerboard.scale(),fret5SB-1)-radius,radius,90,180)
			ui.set_color('white')
			semi.fill()
			
#draw frets

		ui.set_color('white')  #temp
		fretSpace = int((fingerboard.height - 2*fingerboard.nutOffset)/(fingerboard.numFrets))
		
		fingerboard.fretY = [0]
		for index in range(fingerboard.numFrets):
			yFret = fingerboard.fretDistance(fingerboard.scale(),index+1)
			fingerboard.fretY.append(yFret)
			fingerboard.PrevFretY = yFret
			fret = ui.Path()
			fret.line_width = 3
			if instrument.is5StringBanjo and index < fret5SB-1:
				fret.move_to(startX,yFret)
			else:
				fret.move_to(0,yFret)
			fret.line_to(fingerboard.width,yFret)
			fret.stroke()
			
			
		markers = [3,5,7]
		if model.instrument_type()[0] == 'ukulele':
			markers.append(10)
		else:
			markers.append(9)
		for index in markers:
			markeryPos = fingerboard.fretboardYPos(index)
			marker= PathCenteredCircle(int(0.5*fingerboard.width), markeryPos, fingerboard.markerRadius)
			marker.fill()
			
			
		markery12 = markeryPos = fingerboard.fretboardYPos(12)
		for xfraction in [0.25,0.75]:
			marker= PathCenteredCircle(int(xfraction*fingerboard.width), markery12, fingerboard.markerRadius)
			marker.fill()
			
# draw strings

#assume width is 1.5" and strings are 1/8" from edge
		numStrings,offset,ss = fingerboard.stringSpacing()
		fingerboard.nutPosition = []
		ui.set_color('grey')
		fingerboard.stringX = []
		for index in range(numStrings):
			startY = 0
			if fingerboard.is5StringBanjo and index == 0:
				startY = (fingerboard.fretDistance(fingerboard.scale(),fret5SB)+fingerboard.fretDistance(fingerboard.scale(),fret5SB-1))/2
			xString = offset + index*ss
			fingerboard.stringX.append(xString)
			string = ui.Path()
			string.line_width = 3
			string.move_to(xString,startY)
			string.line_to(xString,fingerboard.height)
			string.stroke()
			fingerboard.nutPosition.append((xString,int(0.5* fingerboard.nutOffset)))
			
			
# if 5 string banjo, draw tuning peg

		if fingerboard.is5StringBanjo:
			pegX = fingerboard.stringX[0]
			pegY = (fingerboard.fretDistance(fingerboard.scale(),fret5SB)+fingerboard.fretDistance(fingerboard.scale(),fret5SB-1))/2
			peg = PathCenteredCircle(pegX,pegY,15)
			ui.set_color('#B2B2B2')
			peg.fill()
			peg = PathCenteredCircle(pegX-7,pegY-6,2)
			ui.set_color('white')
			peg.fill()						
								
	
def drawCapo(fingerboard,fret):
	width = fingerboard.width
	if fingerboard.stringSpacing():
		numStrings,offset,ss = fingerboard.stringSpacing()
	else:
		return
	segment = int(width/float(numStrings))
	mask = model._Capos[fret]
	if not fingerboard.is5StringBanjo: #conventional instrument
		padHeight = fingerboard.fretDistance(fingerboard.scale(),fret) - fingerboard.fretDistance(fingerboard.scale(),fret-1) - 10
		padY = fingerboard.fretDistance(fingerboard.scale(),fret-1) + 5
		padStartX = 0
		for i,flag in enumerate(mask):
			if not flag:
				padStartX += segment
			else:
				index = i
				break
		padEndX = index*segment
		for i in range(index,len(mask)):
			if mask[i]:
				padEndX += segment
				continue
			else:
				break
		pad = ui.Path.rect(padStartX,padY,padEndX-padStartX,padHeight)
		ui.set_color('#800040')
		pad.fill()
		
		
		barHeight = int((fingerboard.fretDistance(fingerboard.scale(),14) - fingerboard.fretDistance(fingerboard.scale(),13))*.75)
		barY = fingerboard.fretboardYPos(fret) - barHeight/2
		barX = 0
		bar = ui.Path.rounded_rect(barX,barY,width,barHeight,10)
		ui.set_color('#E5E5E5')
		bar.fill()
	elif len(mask) != 1: #is a banjo, main capo  partial capos
		padHeight = fingerboard.fretDistance(fingerboard.scale(),fret) - fingerboard.fretDistance(fingerboard.scale(),fret-1) - 10
		padY = fingerboard.fretDistance(fingerboard.scale(),fret-1)   +       5
		padStartX = segment
		width -= segment
		barX = segment
		pad = ui.Path.rect(padStartX,padY,width,padHeight)
		ui.set_color('#800040')
		pad.fill()
		barHeight = int((fingerboard.fretDistance(fingerboard.scale(),14) - fingerboard.fretDistance(fingerboard.scale(),13))*.75)
		barY = fingerboard.fretboardYPos(fret) - barHeight/2
		bar = ui.Path.rounded_rect(barX,barY,width,barHeight,10)
		ui.set_color('#E5E5E5')
		bar.fill()
	else: # is banjo, 5th string spike
		x = fingerboard.stringX[0]
		y = fingerboard.fretboardYPos(fret)
		spike = PathCenteredSquare(x,y,20)
		ui.set_color('#E5E5E5')
		spike.fill()								


#---##################################################
# instrument/tuning object

#---Instrument
class Instrument(TVTools,object):
	def __init__(self, items):
		self.items = items
		self._current = None
		self.is5StringBanjo = False
		self.delegator = mainView['tableview_inst_tune']
		self.editing = False
		self.currentNumLines = len(self.items)
		self.waveDir = "default"
		self.waveType = 'wav'
		self.tuning = {}
		pub.subscribe(self.addNewInstrument,'addnewinstrument')
		pub.subscribe(self.restoreInstrument,'restore.instrument')
	
		
	def restoreInstrument(self,items=None):
		self.items = items
		self.currentNumLines = len(self.items)
		 			
	@property
	def current(self):
		return self._current
		
	def onEdit(self,button):
		if self.editing:
			self.editing = False
			self.delegator.editing = False
			self.delegator.reload_data()
		else:
			self.editing = True
			self.delegator.editing = True
			self.tuning = {}
			for item in self.items:
				item['accessory_type'] = 'none'
								
	def reset(self):
		for item in self.items:
			item['accessory_type'] = 'none'			
			
	def updateScaleChord(self):
		mode =  modeDropDown.current['tag']
		if mode == 'C':
			self.fingerings = model.calc_fingerings()
			if model.showChordScale:
				self.fretboard.ChordScaleFrets = calc_chord_scale()
				self.fretboard.set_fingerings(self.fingerings)
			elif mode == 'S':
				self.scale_notes = calc_scale_notes()
				self.fretboard.set_scale_notes(self.scale_notes)
		self.fretboard.touched = {}
		self.fretboard.set_needs_display()
		tuningLabel(self.current['notes'])
			
	def addNewInstrument(self,entry=None):
		self.items.insert(0,entry)
		for i in range(len(self.items)):
			self.items[i]['accessory_type'] = 'none'
		self.delegator.reload_data()			
			
# when new instrument is chosen, update the global and
# redraw the fretboard
# also draw first chord for the current root/type
##############################
# Chapter ListView Select

	def isChecked(self,row): # is a checkbox set in a tableview items attribute
		return self.items[row]['accessory_type'] == 'checkmark'
		
#####################################################################
# Support routine to switch checkmark on and off in table view entry

	def toggleChecked(self,row):
		self.items[row]['accessory_type'] = 'none' if self.isChecked(row) else 'checkmark'
		
		
##############################################
# action for select

	def tableview_did_select(self,tableView,section,row): # Instrument	
		pub.sendMessage('changeinstrument',data=self.items[row])
		self.setTableViewItemsRow(row)	
		tableView.reload_data()
				
	def tableview_number_of_sections(self, tableview):
		# Return the number of sections (defaults to 1)
		return 1
		
	def tableview_number_of_rows(self, tableview, section):
		# Return the number of rows in the section
		return self.currentNumLines
		
	def tableview_cell_for_row(self, tableview, section, row):
		# Create and return a cell for the given section/row
		import ui
		cell = ui.TableViewCell()
		cell.text_label.text = self.items[row]['title']
		cell.accessory_type = self.items[row]['accessory_type']
		return cell
		
	def tableview_can_delete(self, tableview, section, row):
		# Return True if the user should be able to delete the given row.
		return self.editing
		
	def tableview_can_move(self, tableview, section, row):
		# Return True if a reordering control should be shown for the given row (in editing mode).
		return self.editing
		
	def tableview_delete(self, tableview, section, row):
		# Called when the user confirms deletion of the given row.
		self.currentNumLines -=1 # see above regarding the "syncing"
		self.delegator.delete_rows((row,)) # this animates the deletion could also 'tableview.reload_data()'
		del self.items[row]
		
	def tableview_move_row(self, tableview, from_section, from_row, to_section, to_row):
		# Called when the user moves a row with the reordering control (in editing mode).
		self.items = listShuffle(self.items,from_row,to_row)										
																												
# layout
#-----------------------------
# Fretboard Class

class Fretboard(ui.View): # display fingerboard and fingering of current chord/inversion/file
#note that this is instanciated by the load process.
	global middle_label
	def did_load(self):
		if not hasattr(self, 'initted'):
			self.initFretBoard()
			
	def __init__(self):
		if not hasattr(self, 'initted'):
			self.initFretBoard()
			
	def initFretBoard(self):
		self.initted = True
		self.nutOffset = 20
		self.numFrets = 14
		self.offsetFactor = 0.1
		self.markerRadius = 10
		self.fingerRadius = 15
		self.image = ''
		self._scale_notes = []
		self.fingerings = []
		self.fingerinngsPointer = None
		self.loaded = True
		self.snd = self.set_needs_display
		self._chordNumTextView = None
		self._numChordsTextView = None
		self.nutPositions = []
		self.stringX = []
		self.fretY = []
		self.PrevFretY = 0
		self.touched = {} # a dictionary of touched fret/string tuples as keys, note value
		self.location = (0,0)
		self.cc_mode = 'C' # versus 'identify'
		self.scale_display_mode = 'degree'
		self.scale_mode = 'normal'
		self.showChordScale = False
		self.ChordScale = []
		self.ChordScaleFrets = []
		self.arpMin = 0.05
		self.arpMax = 0.5
		self.arpSpeed = (self.arpMax + self.arpMin)/2.0
		self.sharpFlatState = '#'
		self.fret5thStringBanjo = 5
		self.wasTouched = False
		self.inLongTouch = False
		self.longTouchDelay = 0.5
		self.findScaleNotes = []
		self.tuning = None
		self.root = None
		self.chord = None
		self.chord=None
		self.key = None
		self.capos = None
		self.twoOctaveScale = None
		pub.subscribe(self.updateFretboard,'update.fretboard')
		pub.subscribe(self.resetTouched,'resetfound')
		
	
	def updateFretboard(self,mode=None,
						fingerings=None,
						fingeringPointer=None,
						scaleNotes=None,
						showScale=False,
						chordScale = None,
						twoOctaveScale = None,
						tuning=None,
						type = None,
						is5StringBanjo = False,
						root=None,
						chordName=None, 
						chordNoteValues=None,
						rootNoteValue=None, 
						scale=None,
						capos=None,
						progFingeringsPointers = None,
						progChordPointer = None,
						progFingerings = None,
						progChordInfo = None,
						progCentroid = None):
														
		self.fingerings = fingerings
		self.fingeringPointer = fingeringPointer
		self._scale_notes = scaleNotes
		self._cc_mode = mode
		self.showChordScale = showScale
		self.ChordScale = chordScale
		self.tuning = tuning
		self.root = self.keySignature = root
		self.chordName = chordName
		self.chordNoteValues = chordNoteValues
		self.key = rootNoteValue
		self.tuning = tuning
		self.type = type
		self.is5StringBanjo = is5StringBanjo
		self.capos=capos
		self.twoOctaveScale = twoOctaveScale
		self.findScaleNotes = self.ChordScale if mode == "I" else None
		self.progFingeringsPointers = progFingeringsPointers
		self.cChordPointer = progChordPointer
		self.cFingerings = progFingerings
		self.cChordInfo = progChordInfo
		self.cCentroid = progCentroid
		
		try:
			self.scaleType = scale
		except:
			pass
		self.set_needs_display()	
	
	def sharpFlat(self,sender): #toggle
		self.sharpFlatState = 'b' if self.sharpFlatState == '#' else '#'
		self.set_needs_display()
	
	def resetTouched(self):
		self.touched = {}
		
	def scale(self):
		return 2*(self.height - model.fretboard_NutOffset)
		
	def set_tuning(self,instrument): # store current value of tuning parameters
		self.tuning = model._InstrumentTuning
		
	def set_chord(self,chordlist): # store current value of chord
		self.chord = model._Chord
		
	def set_root(self,root):
		self.root = model._RootNoteValue # get value of key
		
	def set_chordnumDisplays(self,chord_num,num_chords):
		self._chordNumTextView = chord_num
		self._numChordsTextView = num_chords
		
	def set_fingerings(self,fingerings):
		self.ChordPositions = fingerings
		self._currentPosition = 0
		
	@property
	def scale_notes(self):
		return self._scale_notes
		
	@scale_notes.setter
	def scale_notes(self, sn):
		'''save scale notes'''
		self._scale_notes = sn
				
	@property
	def chord_num(self):
		return self._currentPosition
		
	@chord_num.setter
	def chord_num(self,number):
		self._currentPosition = number
		
	@property
	def num_chords(self):
		return len(self.ChordPositions)
		
	def fretDistance(self,scalelength, fretnumber):
		import math
		return int(scalelength - (scalelength/math.pow(2,(fretnumber/float(self.numFrets)))))
				
	def fretboardYPos(self,fret):
		return int((self.fretDistance(self.scale(),fret) + self.fretDistance(self.scale(),fret-1))/2.0)
		
	def stringSpacing(self):
		if model._InstrumentTuning:
			numStrings = len(model._InstrumentTuning)
		else:
			return None
		offset = int(model.fretboard_OffsetFactor*self.width)
		return (numStrings,offset,int((self.width-2*offset)/float(numStrings-1)))
						
	def draw(self):		
		''' create fretboard, and note display '''
			
		drawFingerboard(self)
		
		if model._Capos:
			for fret in model._Capos.keys():
				drawCapo(self,fret)
		if self.tuning:
			capoOffsets = model.capoOffsets()
			if (self.fingerings and self.cc_mode == 'C') or (self.cc_mode == 'P' and self.cFingerings):
				isProgression = self.cc_mode == 'P'
				# if there are some, draw current fingering or chord tone frets
				if not self.showChordScale:
					if not isProgression:
						numChord = len(self.fingerings) 
						chordNum = int(self.fingeringPointer+1)
					else:
						Fingerings = self.cFingerings[self.cChordPointer]
						if not Fingerings:
							return
						fPointer = self.progFingeringsPointers[self.cChordPointer]		
						numChord = len(Fingerings)
						chordNum = int(fPointer+1)
					self._numChordsTextView.text = "{}".format(numChord)
					self._chordNumTextView.text = "{}".format(chordNum)
					middle_field.text = 'of'
					if isProgression:
						fingering,chordTones,fretPositions,centroid = self.cFingerings[self.cChordPointer][fPointer] 
					else:	
						fingering,chordTones,fretPositions = self.fingerings[self.fingeringPointer]
					ui.set_color('red')
					for i,string in enumerate(fingering):
						x,y,chordtone,nutmarker = string
						if i == 0 and instrument.is5StringBanjo:
							if fretPositions[i] == -1:
								y = (self.fretDistance(self.scale(),self.fret5thStringBanjo)+self.fretDistance(self.scale(),self.fret5thStringBanjo-1))/2
						#a = fretPositions[i]
						#b = capoOffsets[i]
						try:

							if fretPositions[i] == capoOffsets[i]:
								nutmarker = True
						except:
							console.hud_alert('fretPositions[i] == capoOffsets[i] i= {}'.format(i),'error',5)
							
						if not nutmarker:
							ui.set_color('red')
							marker= PathCenteredCircle(x,y,self.fingerRadius)
							marker.fill()
							ui.set_color('white')
							size = ui.measure_string(chordtone,font=('AmericanTypewriter-Bold',
							22),alignment=ui.ALIGN_CENTER)
							ui.draw_string(chordtone,(int(x-0.5*size[0]),int(y-0.5*size[1]),0,0),
							font=('AmericanTypewriter-Bold',22),alignment=ui.ALIGN_CENTER)
						else:
							size = ui.measure_string(chordtone,font=('AmericanTypewriter-Bold',26),alignment=ui.ALIGN_CENTER)
							ui.draw_string(chordtone,(int(x-0.5*size[0]),int(y-0.5*size[1]),0,0),
							font=('AmericanTypewriter-Bold',26),alignment=ui.ALIGN_CENTER,color='black')
							size = ui.measure_string(chordtone,font=('AmericanTypewriter-Bold',22),alignment=ui.ALIGN_CENTER)
							ui.draw_string(chordtone,(int(x-0.5*size[0]),int(y-0.5*size[1]),0,0),
							font=('AmericanTypewriter-Bold',22),alignment=ui.ALIGN_CENTER,color='red')
				elif self.ChordScale:
					for string,fret_note_pairs in enumerate(self.ChordScale):
						for fret,note in fret_note_pairs:
							chordtone = ccc['SCALENOTES'][note]
							x = self.stringX[string]
							if fret != -1:
								y = self.fretboardYPos(fret+1)
							else:
								if string == 0 and instrument.is5StringBanjo:
									y = (self.fretDistance(self.scale(),fret5SB)+self.fretDistance(self.scale(),fret5SB-1))/2
								else:
									y = self.nutPosition[0][1]
							ui.set_color('red')
							if note == 0:
								marker= PathCenteredSquare(x,y,self.fingerRadius)
							else:
								marker= PathCenteredCircle(x,y,self.fingerRadius)
							marker.fill()
							ui.set_color('white')
							size = ui.measure_string(chordtone,font=('AmericanTypewriter-Bold',
							22),alignment=ui.ALIGN_CENTER)
							ui.draw_string(chordtone,(int(x-0.5*size[0]),int(y-0.5*size[1]),0,0),
							font=('AmericanTypewriter-Bold',22),alignment=ui.ALIGN_CENTER)
							
			elif root.current and self.chord and self.cc_mode == 'C':
				sound.play_effect('Woosh_1')
				self._chordNumTextView.text = "Try dropping"
				middle_field.text = "root, 3rd"
				self._numChordsTextView.text = "or 5th"
				
				
			elif self.cc_mode == 'I':# identify mode
				if not self.findScaleNotes:
					for key in self.touched.keys():
						values = self.touched[key]
						x = self.stringX[values[2]]
						y = self.fretboardYPos(values[3])
						outchar = ccc['NOTE_NAMES'][values[0]%12].split('/')[0]
						if values[3]:
							ui.set_color('red')
							marker= PathCenteredCircle(x,y,self.fingerRadius)
							marker.fill()
							ui.set_color('white')
							size = ui.measure_string(outchar,
							font=('AmericanTypewriter-Bold',
							22),alignment=ui.ALIGN_CENTER)
							ui.draw_string(outchar,(int(x-0.5*size[0]),int(y-0.5*size[1]),0,0),
							font=('AmericanTypewriter-Bold',22),alignment=ui.ALIGN_CENTER)
						else:
							y = self.nutPosition[0][1]
							size = ui.measure_string(outchar,font=('AmericanTypewriter-Bold',26),alignment=ui.ALIGN_CENTER)
							ui.draw_string(outchar,(int(x-0.5*size[0]),int(y-0.5*size[1]),0,0),
							font=('AmericanTypewriter-Bold',26),alignment=ui.ALIGN_CENTER,color='black')
							size = ui.measure_string(outchar,font=('AmericanTypewriter-Bold',22),alignment=ui.ALIGN_CENTER)
							ui.draw_string(outchar,(int(x-0.5*size[0]),int(y-0.5*size[1]),0,0),
							font=('AmericanTypewriter-Bold',22),alignment=ui.ALIGN_CENTER,color='red')
				else:
					for i,string in enumerate(self.findScaleNotes):
						for fret,note in string:
							if fret+1 < capoOffsets[i]:
								continue
							x = self.stringX[i]
							if fret+1:
								y = self.fretboardYPos(fret+1)
							else:
								y = self.nutPosition[0][1] + self.fingerRadius*0.3
							ui.set_color('red')
							if note == find.key:
								marker= PathCenteredSquare(x,y,self.fingerRadius)
							else:
								marker= PathCenteredCircle(x,y,self.fingerRadius)
							marker.fill()
							outchar = ccc['SCALENOTES'][(note) % 12]
							ui.set_color('white')
							size = ui.measure_string(outchar,font=('AmericanTypewriter-Bold',
							22),alignment=ui.ALIGN_CENTER)
							ui.draw_string(outchar,(int(x-0.5*size[0]),int(y-0.5*size[1]),0,0),
							font=('AmericanTypewriter-Bold',22),alignment=ui.ALIGN_CENTER)
					# mark touched notes
					for key in self.touched.keys():
						values = self.touched[key]
						x = self.stringX[values[2]]
						if values[3] == 1:
							y = self.fretboardYPos(values[3]) + 12
						elif values[3]:
							y = self.fretboardYPos(values[3])
						else:
							y = self.nutPosition[0][1] + self.fingerRadius*0.3
						ui.set_color('white')
						marker= PathCenteredCircle(x,y,self.fingerRadius + 10)
						marker.line_width = 3
						marker.stroke()
						
			elif self.cc_mode == 'S': # display scale notes
				ui.set_color('red')
				if self._scale_notes:
					for i,string in enumerate(self._scale_notes):
						for fret,note in string:
							if fret < capoOffsets[i]:
								continue
							x = self.stringX[i]
							if fret == 1:
								y = self.fretboardYPos(fret) + 12
							elif fret:
								y = self.fretboardYPos(fret)
							else:
								y = self.nutPosition[0][1] + model.fretboard_FingerRadius*0.3
							ui.set_color('red')
							if note == self.key:
								marker= PathCenteredSquare(x,y,model.fretboard_FingerRadius)
							else:
								marker= PathCenteredCircle(x,y,model.fretboard_FingerRadius)
							marker.fill()
							if self.scale_display_mode == 'degree':
								outchar = ccc['SCALENOTES'][(note - model._RootNoteValue) % 12]
							else:
								outchar = self.noteName(note)
							ui.set_color('white')
							size = ui.measure_string(outchar,font=('AmericanTypewriter-Bold',
							22),alignment=ui.ALIGN_CENTER)
							ui.draw_string(outchar,(int(x-0.5*size[0]),int(y-0.5*size[1]),0,0),
							font=('AmericanTypewriter-Bold',22),alignment=ui.ALIGN_CENTER)
				if self.twoOctaveScale: # mark the scale notes
					ui.set_color('yellow')
					self.fifthPresent = False # prevent 5 and 5# from both being highlighted chord tones.
					
					for string,fret in self.twoOctaveScale:
						if fret < capoOffsets[i]:
							continue
						x = self.stringX[string]
						if fret == 1:
							y = self.fretboardYPos(fret) + 12
						elif fret:
							y = self.fretboardYPos(fret)
						else:
							y = self.nutPosition[0][1] + model.fretboard_FingerRadius*0.3
						self.chordtone_color(string,fret)
						marker= PathCenteredCircle(x,y,model.fretboard_FingerRadius + 10)
						marker.line_width = 3
						marker.stroke()				
			else:
				pass
				
	def chordtone_color(self,string,fret):
		# convert from string/fret to note
		key = fretboard.key
		thisString = self._scale_notes[string]
		for thisFret,thisNote in thisString:
			color = 'red'
			if fret == thisFret:
				scaleTone = (thisNote - key) % 12
				if scaleTone == 0:
					color = 'green'
					break
				elif scaleTone in (3,4): # b3 and 3
					color = 'yellow'
					break
				elif scaleTone in (7,8): # 5 and 5#
					if scaleTone == 7:
						color = 'white'
						self.fifthPresent = True
						break
					elif scaleTone == 8 and not self.fifthPresent:
						color = 'white'
						break
				elif scaleTone in (10,11):
					color = 'orange'
					break
		ui.set_color(color)
		return
		
	def noteName(self,note):
		'''return the name of the note with proper use of sharps or flats'''
		key = self.key if self.cc_mode != 'I' else find.key
		keySig = self.keySignature
		if keySig in ccc['CIRCLE_OF_FIFTHS'].keys():
			sf = ccc['CIRCLE_OF_FIFTHS'][keySig]
		else:
			console.hud_alert('{} not in COF, substituting the enharmonic'.format(keySig),'error',2)
			sf = 1 if self.sharpFlatState == '#' else -1 # use preference
		if self.scaleType in ccc['TRUE_ROOT'].keys():
			origKeySig = keySig
			key = (key - ccc['TRUE_ROOT'][self.scaleType]) % 12
			keySig = ccc['NOTE_NAMES'][key].split('/')
			origSF = sf
			if len(keySig) == 1:
				keySig = keySig[0]
			else:
				if origKeySig in ccc['CIRCLE_OF_FIFTHS'].keys():
					origSF = ccc['CIRCLE_OF_FIFTHS'][origKeySig]
				else:
					origSF = 1 if self.sharpFlatState == '#' else -1
			sf = origSF
		outchar = ccc['NOTE_NAMES'][note].split('/')
		index = 0
		if len(outchar) > 1:
			if sf < 0:
				index = 1
		return outchar[index]
		
	def distance(self,x,a):
		'''return a list of distances from x to each element in a'''
		return [math.sqrt((x-item)*(x-item)) for item in a]
		
	def closest(self,x,a): #may need to fix this for upper left corner touch
		''' return index of closest element in a to x'''
		deltas = self.distance(x,a)
		index,value = min(enumerate(deltas),key=lambda val:val[1])
		return index
		
	def doLongTouch(self):
		# got here so should be a long touch
		self.wasLongTouch = True
		
		
	def touch_began(self,touch):
		''' begining of a touch'''
		self.wasTouched = True
		self.wasLongTouch = False
		self.touch_start = touch.location
		self.touchStartTime = time.time()
		# fire of a delayed function to confirm long touch if it is
		ui.delay(self.doLongTouch, self.longTouchDelay)
		
	def touch_ended(self,touch): #this one
		ui.cancel_delays() # will prevent long delay if it isn't'
		self.touch_end = touch.location
		DeltaX = self.touch_end[0] - self.touch_start[0]
		DeltaY = self.touch_end[1] - self.touch_start[1]
		touchEndTime = time.time()
		DeltaT = touchEndTime - self.touchStartTime
		distance = math.sqrt(DeltaX*DeltaX + DeltaY*DeltaY)
		rate = distance/DeltaT
		angle = math.atan2(DeltaY,DeltaX)*180/math.pi
		
		if self.cc_mode == 'I':
			if fretboard.findScaleNotes:
				find.reset()
				self.set_needs_display()
				return
			offsets = model.capoOffsets()
			x,y = touch.location
			string = self.closest(x,self.stringX)
			fret = self.closest(y,self.fretY)
			if fret < offsets[string]:
				return
			location = (string,fret)
			if location in self.touched.keys():
				del self.touched[location]
			else:
				for key in self.touched.keys():
					if key[0] == string:
						del self.touched[key]
						break
				self.touched[location] = (model._InstrumentTuning[string] +fret, model._InstrumentOctave,string,fret)
				octave,tone = divmod(model._InstrumentTuning[string]+fret,12)
				sound.play_effect(getWaveName(tone,octave+model._InstrumentOctave))
			self.set_needs_display()
		elif self.cc_mode == 'S': # label the two octave scale starting at this root
			x,y = touch.location
			string = self.closest(x,self.stringX)
			fret = self.closest(y,self.fretY)
			self.location = (string,fret)
			octave,tone = divmod((model._InstrumentTuning[string]+fret),12)
			if tone != model._RootNoteValue:
				sound.play_effect('Drums_01')
				return None
			pub.sendMessage('setscalefrets',location=self.location,mode=self.scale_mode)

		elif self.cc_mode == 'C':
			if abs(DeltaY) > 30 and abs(DeltaY) > abs(DeltaX): #  vertical sweep
				_,_,_,yrange = self.frame
				fraction = DeltaY/yrange
				try:
					increment = math.floor(fraction*len(model._Fingerings)*0.5)
				except TypeError:
					return
				current = model._FingeringPointer
				current += increment
				current = max(0,current)
				current = min(len(model._Fingerings)-1,current)
				pub.sendMessage('changefingering',pointer=current)
			elif abs(DeltaX) > 30 and abs(DeltaX) > abs(DeltaY): # horizontal sweep, small moves
				_,_,xrange,_ = self.frame
				fraction = DeltaX/xrange
				try:
					increment = math.floor(fraction*10)
				except TypeError:
					return
				current = model._FingeringPointer
				current += increment
				current = max(0,current)
				current = min(len(model._Fingerings)-1,current)
				pub.sendMessage('changefingering', pointer=current)
			elif self.wasLongTouch: #jump to this fret
				x,y = touch.location
				fret = self.closest(y,self.fretY)
				for i,fingering in enumerate(model._Fingerings):
					_,_,frets = fingering
					testVector =  sorted([x for x in frets if x > 0])
					if fret - 2 <= testVector[0] <= fret + 2:
						break
				current = i if i < len(model._Fingerings) - 1 else self._FingeringPointer
				pub.sendMessage('changefingering', pointer=current)
			else:
				# switch display to chord tones
				pub.sendMessage('toggleshowchordscaleview')
		elif self.cc_mode == 'P':
			theseFingerings = model._ProgFingerings[model._ProgChordPointer]
			if abs(DeltaY) > 30 and abs(DeltaY) > abs(DeltaX): #  vertical sweep
				_,_,_,yrange = self.frame
				fraction = DeltaY/yrange
				try:
					increment = math.floor(fraction*len(theseFingerings)*0.5)
				except TypeError:
					return
				current = model._ProgFingeringsPointers[model._ProgChordPointer]
				current += increment
				current = max(0,current)
				current = min(len(theseFingerings)-1,current) 
				pub.sendMessage('updateprogressionpointers',
								nextChord=-1,nextFingering=current)
			elif self.wasLongTouch: #jump to this fret
				x,y = touch.location
				fret = self.closest(y,self.fretY)
				for i,fingering in enumerate(theseFingerings):
					_,_,frets,_ = fingering
					testVector =  sorted([x for x in frets if x > 0])
					if fret - 2 <= testVector[0] <= fret + 2:
						break
				if i < len(theseFingerings) - 1:
					current = i 
				else:
					current =  model._ProgFingeringsPointers[model._ProgChordPointer]		
				pub.sendMessage('updateprogressionpointers',
								nextChord=-1,nextFingering=current)


			
			
#####################################
# fingering positions for drawing

	def fingeringDrawPositions(self,key,chordtype,tuning,fingering):
		""" given a fingering,chord and tuning information and virtual neck info,
		return the center positions all markers.  X and open strings will be
		marked at the nut"""
		scaleNotes = model.getScaleNotes(fingering)
		#if len(scaleNotes) != len(fingering):
		chordDrawPositions = []
		numStrings,offset,ss = self.stringSpacing()
		for i,fretPosition in enumerate(fingering): #loop over strings, low to high
			try:
				note = scaleNotes[i]
			except:
				continue
			atNut = None
			xpos = offset + i*ss
			if fretPosition in [-1,0]: #marker at nut
				ypos = int(0.5* self.nutOffset)
				atNut = 'X' if fretPosition else 'O'
			else:
				ypos = self.fretboardYPos(fretPosition)
			chordDrawPositions.append((xpos,ypos,note,atNut))
		return chordDrawPositions
		
	def get_instrument(self):
		return self.instrument
		
	def onFind(self,button):
		fingered = [self.touched[key][0] for key in self.touched.keys()]
		if fingered:
			fingered = sorted([x%12 for x in fingered])
			pure = []
			missing_1 = []
			missing_2 = []
			chord_list = []
			for root in range(12):
				notes_in_key = rotate(range(12),root)
				present = {}
				notevals = []
				for i,note in enumerate(notes_in_key):
					present[i] = True if note in fingered else False
					if present[i]:
						notevals.append(i)
				for chord in ccc['CHORDTYPE']:
					deltas = set(notevals) ^ set(chord[1]) #those notes not in both (symmetric difference)
					if not deltas:
						pure.append({'title':"{}{}".format(ccc['NOTE_NAMES'][root],chord[0]),'root':root,
						'chord':chord[0], 'accessory_type':'none'})
					if deltas == set([0]):
						missing_1.append({'title':"{}{} (no root)".format(ccc['NOTE_NAMES'][root],chord[0]),
						'root':root, 'chord':chord[0], 'accessory_type':'none'})
					if deltas == set([3]) or deltas == set([4]):
						missing_1.append({'title':"{}{} (no 3rd)".format(ccc['NOTE_NAMES'][root],chord[0]),
						'root':root, 'chord':chord[0], 'accessory_type':'none'})
					if deltas == set([7]):
						missing_1.append({'title':"{}{} (no 5th)".format(ccc['NOTE_NAMES'][root],chord[0]),
						'root':root, 'chord':chord[0], 'accessory_type':'none'})
						
			for list in [pure,missing_1]:
				if list:
					chord_list += list
					chord_list.append({'title':"-------",'root':-1, 'chord':-1, 'accessory_type':'none'})
			pub.sendMessage('updatefind',chordlist=chord_list)



#--- ##################################################
# chord type


#===============================================
class Chord(TVTools,object):
	global curentState
	def __init__(self,items):
		self.items = items
		self.delegator = mainView['tableview_type']
		self._current = None
		
	def onEdit(self,button):
		if self.delegator.editing:
			self.delegator.editing = False
			self.delegator.reload_data()
		else:
			self.delegator.editing = True
			self.chord = {}
			for item in self.items:
				item['accessory_type'] = 'none'
				
	@property
	def current(self):
		return self._current
		
	def reset(self):
		for item in self.items:
			item['accessory_type'] = 'none'
			
	def getNotesByName(self,chordName):
		for item in self.items:
			if item['title'] == chordName:
				return item['fingering']
		return None
			
# action for select

	def tableview_did_select(self,tableView,section,row):   #Chord
		self.setTableViewItemsRow(row)
		tableView.reload_data()
		pub.sendMessage('changechord', name=self.items[row]['title'], 
										chordTones=self.items[row]['fingering'] )
		
	def tableview_number_of_sections(self, tableview):
		# Return the number of sections (defaults to 1)
		return 1
		
	def tableview_number_of_rows(self, tableview, section):
		# Return the number of rows in the section
		return len(self.items)
		
	def tableview_cell_for_row(self, tableview, section, row):
		# Create and return a cell for the given section/row
		cell = ui.TableViewCell()
		cell.text_label.text = self.items[row]['title']
		cell.accessory_type = self.items[row]['accessory_type']
		return cell
		
	def tableview_can_delete(self, tableview, section, row):
		# Return True if the user should be able to delete the given row.
		return False
		
	def tableview_can_move(self, tableview, section, row):
		# Return True if a reordering control should be shown for the given row (in editing mode).
		return True
		
	def tableview_delete(self, tableview, section, row):
		# Called when the user confirms deletion of the given row.
		self.currentNumLines -=1 # see above regarding hte "syncing"
		self.delegator.delete_rows((row,)) # this animates the deletion  could also 'tableview.reload_data()'
		del self.items[row]
		
	def tableview_move_row(self, tableview, from_section, from_row, to_section, to_row):
		# Called when the user moves a row with the reordering control (in editing mode).
		self.items = listShuffle(self.items,from_row,to_row)
		
	def get_chord(self):
		return self.chord
		
		
#--- =================================================================
		
class Scale(TVTools,object):
	def __init__(self, items):
		self.items = items
		self._current = None
		
	@property
	def current(self):
		return self._current
		
	@property
	def scale(self):
		if self._current:
			return self._current['title']
		else:
			return None
			
	def onEdit(self,button):
		pass
		
	def __getitem__(self,type):
		try:
			return self.scale[type]
		except:
			return None
			
	def reset(self):
		for item in self.items:
			item['accessory_type'] = 'none'
			
			
# action for select

	def tableview_did_select(self,tableView,section,row): 
		
		  #Scale
		self.setTableViewItemsRow(row)
		tableView.reload_data()
		pub.sendMessage('changescale', scale=self.items[row])
				
	def tableview_number_of_sections(self, tableview):
		# Return the number of sections (defaults to 1)
		return 1
		
	def tableview_number_of_rows(self, tableview, section):
		# Return the number of rows in the section
		return len(self.items)
		
	def tableview_cell_for_row(self, tableview, section, row):
		# Create and return a cell for the given section/row
		cell = ui.TableViewCell()
		cell.text_label.text = self.items[row]['title']
		cell.accessory_type = self.items[row]['accessory_type']
		return cell
		
		
		
#--- ###################################################
# root tone

class Root(TVTools,object):
	def __init__(self, items):
		self.items = items
		self._current = None
		self._root = None
		self._noteValue = None
		self._row = None
		
		
	def reset(self):
		for item in self.items:
			item['accessory_type'] = 'none'
			
	@property
	def current(self):
		return self._current
		
	@property
	def root(self):
		return self._root
		
	@root.setter
	def root(self,value):
		self._root = value
		
	@property
	def row(self):
		return self._row
		
	@row.setter
	def row(self,value):
		if 0<=value<=len(self.items):
			self._row = value
			self.setTableViewItemsRow(value)
			self._noteValue = self.items[value]['noteValue']
			self._root = self.items[value]['title']
		else:
			raise ValueError('row out of range')
			
	@property
	def noteValue(self):
		return self._noteValue
		
# action for select

	def tableview_did_select(self,tableView,section,row): #Root
		self.row = row
		tableView.reload_data()
		pub.sendMessage('changeroot',root=self._root, value=self._noteValue)

	def tableview_number_of_sections(self, tableview):
		# Return the number of sections (defaults to 1)
		return 1
		
	def tableview_number_of_rows(self, tableview, section):
		# Return the number of rows in the section
		return len(self.items)
		
	def tableview_cell_for_row(self, tableview, section, row):
		# Create and return a cell for the given section/row
		cell = ui.TableViewCell()
		cell.text_label.text = self.items[row]['title']
		cell.accessory_type = self.items[row]['accessory_type']
		return cell
		
	def get_root(self):
		try:
			return self.root
		except:
			return None
			
			
#--- ##################################################


class Filters(ui.View):
	def __init__(self):
		self.filter_list = []
		self.items = ccc['FILTER_LIST_CLEAN']
		self.delegator = mainView['tableview_filters']
		self._current = None
	
	@property
	def current(self):
		return self._current
		
	def onEdit(self,button):
		if self.delegator.editing:
			self.delegator.editing = False
			self.delegator.reload_data()
		else:
			self.delegator.editing = True
			self.chord = {}
			for item in self.items:
				item['accessory_type'] = 'none'
				
	def set_filters(self,instrument_type=None):
		self.filter_list = []
		self.items = ccc['FILTER_LIST_CLEAN']
		it = instrument_type[0]
		if it == 'guitar':
			self.items = self.items + ccc['GUITAR_LIST_CLEAN']
		elif it == 'mando':
			self.items = self.items + ccc['MANDOLIN_LIST_CLEAN']
		else: # generic
			pass
		for item in self.items:
			item['accessory_type'] = 'none'
		self.delegator.reload_data()

	def reconsile_filters(self,filter):
		if filter in ccc['FILTER_MUTUAL_EXCLUSION_LIST'].keys():
			exclude = ccc['FILTER_MUTUAL_EXCLUSION_LIST'][filter]
			for exclusion in exclude:
				if exclusion in self.filter_list:
					self.filter_list.remove(exclusion)
					for item in self.items:
						if item['title'] == exclusion:
							item['accessory_type'] = 'none'
							
							
							
							
##############################
# Chapter ListView Select

	def isChecked(self,row): # is a checkbox set in a tableview items attribute
		return self.items[row]['accessory_type'] == 'checkmark'
		
#####################################################################
# Support routine to switch checkmark on and off in table view entry

	def toggleChecked(self,row):
		self.items[row]['accessory_type'] = 'none' if self.isChecked(row) else 'checkmark'
		
	def offChecked(self,row):
		self.items[row]['accessory_type'] = 'none'
		
	def onChecked(self,row):
		self.items[row]['accessory_type'] = 'checkmark'
		
##############################################
# action for select

	def tableview_did_select(self,tableView,section,row):   #Filters
	
		self.toggleChecked(row)
		filtername = self.items[row]['title']
		
		if self.isChecked(row):
			if not filtername in self.filter_list:
				self.filter_list.append(filtername)
				self.reconsile_filters(filtername)
		else:
			if filtername in self.filter_list:
				self.filter_list.remove(filtername)
				
		pub.sendMessage('changefilters',filters=self.filter_list)
		tableView.reload_data()
			
		
	def tableview_number_of_sections(self, tableview):
		# Return the number of sections (defaults to 1)
		return 1
		
	def tableview_number_of_rows(self, tableview, section):
		# Return the number of rows in the section
		return len(self.items)
		
	def tableview_cell_for_row(self, tableview, section, row):
		# Create and return a cell for the given section/row
		cell = ui.TableViewCell()
		cell.text_label.text = self.items[row]['title']
		cell.accessory_type = self.items[row]['accessory_type']
		return cell
		
	def tableview_can_delete(self, tableview, section, row):
		# Return True if the user should be able to delete the given row.
		return False
		
	def tableview_can_move(self, tableview, section, row):
		# Return True if a reordering control should be shown for the given row (in editing mode).
		return True
		
	def tableview_delete(self, tableview, section, row):
		# Called when the user confirms deletion of the given row.
		self.currentNumLines -=1 # see above regarding hte "syncing"
		self.delegator.delete_rows((row,)) # this animates the deletion  could also 'tableview.reload_data()'
		del self.items[row]
		
	def tableview_move_row(self, tableview, from_section, from_row, to_section, to_row):
		# Called when the user moves a row with the reordering control (in editing mode).
		self.items = listShuffle(self.items,from_row,to_row)
		
	def get_chord(self):
		return self.chord
		
#--- ===============================================		
class Capos(object):
	def __init__(self, items):
		self.items = items
		self._row = None
		self.delegator = mainView['tableview_capos']
		self.numstrings = None
		pub.subscribe(self.capoSetFret,'sendfrettocapo')
		pub.subscribe(self.reset,'resetcapositems')

		
	@property
	def row(self):
		return self._row
		
	def onEdit(self,button):
		if self.delegator.editing:
			self.delegator.editing = False
			self.delegator.reload_data()
		else:
			self.delegator.editing = True
			self.capos = {}
			for item in self.items:
				item['accessory_type'] = 'none'
				
	def syncNumStrings(self,numstr=None):
		if numstr:
			self.numstrings = numstr
			
	def setFretItem(row=None,fretValue=None):
		self.items[row]['fret'] =fretValue
							
	def reset(self):
		for row in range(len(self.items)):
			self.items[row]['fret'] = 0
			self.items[row]['accessory_type'] = 'none'
		self._row = 0
		self.capos = {}
		tvCapos.reload_data()
		
	def capoSetFret(self,fret=None):
		self.toggleChecked(self._row)
		self.items[self._row]['fret'] = fret
		mainView['view_fretEnter'].hidden = True
		self.delegator.reload_data()
		pub.sendMessage('setcapofret',fret=fret,mask=self.items[self._row]['mask'])
			
##############################
# Chapter ListView Select

	def isChecked(self,row): # is a checkbox set in a tableview items attribute
		return self.items[row]['accessory_type'] == 'checkmark'
		
#####################################################################
# Support routine to switch checkmark on and off in table view entry

	def toggleChecked(self,row):
		self.items[row]['accessory_type'] = 'none' if self.isChecked(row) else 'checkmark'
		
##############################################
# action for select

	def tableview_did_select(self,tableView,section,row): #capos
		if not model._InstrumentTuning:
			return None
		self._row = row
		if self.isChecked(row):
			# uncheck and remove the entry in the dictionary
			self.toggleChecked(row)
			fret = self.items[row]['fret']
			self.items[row]['fret'] = 0
			tableView.reload_data()
			pub.sendMessage('setcapofret', fret=fret, mask=None)
		else:
			# need to handle the rest via special data entry view
			numFrets = fretboard.numFrets
			fretEnter = mainView['view_fretEnter']
			x,y,w,h = fretEnter.frame
			x = 400
			y = 200
			fretEnter.frame = (x,y,w,h)
			minFret = 1
			if self.items[row]['title'] == 'Banjo 5th':
				if model.instrument_type()[0] != 'banjo':
					return None
				else:
					minFret = model.fretboard_Fret5thStringBanjo + 1
			fretEnter.label.text = "Enter fret # {}-{}".format(minFret,numFrets)
			fretEnter.setRange(minFret,numFrets)
			fretEnter.hidden = False
			fretEnter.bring_to_front()
			
	def tableview_number_of_sections(self, tableview):
		# Return the number of sections (defaults to 1)
		return 1
		
	def tableview_number_of_rows(self, tableview, section):
		# Return the number of rows in the section
		return len(self.items)
		
	def tableview_cell_for_row(self, tableview, section, row):
		# Create and return a cell for the given section/row
		cell = ui.TableViewCell()
		fret = self.items[row]['fret']
		text = self.items[row]['title']
		cell.text_label.text = "{} at fret {}".format(text,fret) if fret else text
		cell.accessory_type = self.items[row]['accessory_type']
		return cell
		
	def tableview_can_delete(self, tableview, section, row):
		# Return True if the user should be able to delete the given row.
		return False
		
	def tableview_can_move(self, tableview, section, row):
		# Return True if a reordering control should be shown for the given row (in editing mode).
		return True
		
	def tableview_delete(self, tableview, section, row):
		# Called when the user confirms deletion of the given row.
		self.currentNumLines -=1 # see above regarding hte "syncing"
		self.delegator.delete_rows((row,)) # this animates the deletion  could also 'tableview.reload_data()'
		del self.items[row]
		
	def tableview_move_row(self, tableview, from_section, from_row, to_section, to_row):
		# Called when the user moves a row with the reordering control (in editing mode).
		self.items = listShuffle(self.items,from_row,to_row)

#--- ==================================		
class FretEnter(ui.View):
	''' implement routines for fret entry'''
	def did_load(self):
		for subview in self.subviews:
			name = subview.name
			if name.startswith('btn'):
				subview.action = self.onButton
			elif name.startswith('tf'):
				self.textfield = subview
			elif name.startswith('lab'):
				self.label = subview
				
		self.spinner = Spinner(name='sp_Fret',
									initialValue= 2,
									increment=1,
									limits=(1,22),
									action=None, # done if action was successful
									limitAction=None, #done if hit a limit
									textFraction = 0.75,
									fontSize = 18,
									spinnerSize=(80,80))
		self.add_subview(self.spinner)
		self.spinner.position = (90,90)
		
	def onButton(self,button): #business end of fretEnter	
		if button.name.endswith('Cancel'):
			mainView['view_fretEnter'].hidden = True	
		else: # OK
			pub.sendMessage('sendfrettocapo', fret=self.spinner.value)
			
	def setRange(self,min,max):
		self.spinner.limits = (min,max)
		
		
		
#
# Display routines

def parseChordName(chordstr):
	p = re.compile('([A-G][#b]{0,1})(.*)', re.IGNORECASE)
	m = p.match(chordstr)
	if m != None:
		return m.group(1,2) # key and chordtype
	else:
		return ['','']
		
##########################################
##########################################
# S. Pollack Code below



###################################################
# previous/next chord form

def onPrevNext(button):
	if model._Mode in ('C','P'):
		if model._Mode == 'C':
			pointer =  model._FingeringPointer
			fingerings = model._Fingerings
		else: # 'P'
			pointer = model._ProgFingeringsPointers[model._ProgChordPointer]
			fingerings = model._ProgFingerings[model._ProgChordPointer]
		if fingerings:
			cn = pointer
			nc = len(fingerings)
			if button.name == 'button_down':
				if cn < nc-1:
					cn +=1
			else:# 'button_up'
				cn -= 1
				if cn < 0:
					cn = 0
		if model._Mode == 'C':
			pub.sendMessage('changefingering',pointer=cn)

		else: # 'P'	
			pub.sendMessage('updateprogressionpointers',
								nextChord=-1,nextFingering=cn)
										
###################################################
# play arpeggio

def getWaveName(tone,octave):
	type,directory = model.instrument_type()
	result = "waves/{}/{}{}.mp3".format(directory,ccc['NOTE_FILE_NAMES'][tone],octave)
	return result
		
def play(button):
	if os.path.exists('waves'):
		if not model._InstrumentOctave:
			return
		else:
			baseOctave = model._InstrumentOctave
		strings = model._InstrumentTuning
		if model._Mode in ('C','P'):
			try:
				if model._Mode == 'C':
					cc = model._Fingerings[model._FingeringPointer]
				else: # 'P'
					thisFingering = model._ProgFingeringsPointers[model._ProgChordPointer]
					cc = model._ProgFingerings[model._ProgChordPointer][thisFingering]
			except TypeError: # no chords yet
				return
			except IndexError: #oops
				return
	
			frets = cc[2]
			dead_notes = [item[3] == 'X' for item in cc[0]]
			tones = []
			for fret,string,dead_note in zip(frets,strings,dead_notes):
				if  dead_note:
					continue
				octave,tone = divmod(string + fret,12)
				tones.append((tone,octave+baseOctave))
		elif fretboard.cc_mode == 'I': # identify
			positions = [string_fret for string_fret in fretboard.touched.keys()]
			positions = sorted(positions,key=lambda x:x[0])
			position_dict = {}
			for string,fret in positions:
				position_dict[string] = fret
			tones = []
			for i,pitch in enumerate(strings):
				if i in position_dict:
					octave,tone = divmod(pitch + position_dict[i],12)
					tones.append((tone,octave+baseOctave))
					
		else: #scale
			pass
			
		for tone,octave in tones:
			sound.play_effect(getWaveName(tone,octave))
			time.sleep(0.05)
			if button.name == 'button_arp':
				time.sleep(fretboard.arpSpeed)
				
				
def play_tuning(button):
	if os.path.exists('waves'):
		try:
			strings = model._InstrumentTuning
		except TypeError: # no instrument delected yet
			return
		baseOctave = model._InstrumentOctave
		tones = []
		for string in strings:
			octave,tone = divmod(string,12)
			tones.append((tone,octave+baseOctave))
		for tone,octave in tones:
			sound.play_effect(getWaveName(tone,octave))
			time.sleep(fretboard.arpSpeed)
			
def playScale(button):
	if model._TwoOctaveScale:
		if os.path.exists('waves'):
			for string,fret in model._TwoOctaveScale:
				octave,tone = divmod((model._InstrumentTuning[string]+fret),12)
				sound.play_effect(getWaveName(tone,octave+model._InstrumentOctave))
				time.sleep(fretboard.arpSpeed)
		
def toggle_mode(sender,row):
	global chordProgView
	capos.reset()
	
	newmode = sender.current['tag']
	hideshow = {
	'I': 
		 {
		     'hide':
	'tableview_root tableview_type tableview_scale label1 button_scale_notes button_scale_tones chord_num label_middle button_play_scale num_chords lbl_chord lbl_fullchord lbl_definition btn_sharpFlat sp_span lbl_span tri_chord_label  button_up button_down tableview_prog tableview_prog_display label_centroid switch_centroid'.split(),
			'show':
	('tableview_find', 'button_find', 'button_chord', 'button_arp', 'fretboard')
	},
	'C':    
		{
			'hide':
	'tableview_find button_find button_scale_tones button_scale_notes tableview_scale button_play_scale lbl_chord lbl_fullchord btn_sharpFlat tableview_prog tableview_prog_display label_centroid switch_centroid'.split(),
			'show': 
	'tableview_root tableview_type label1 chord_num num_chords label_middle button_chord button_arp sp_span lbl_span tri_chord_label button_up button_down label1 fretboard'.split()
	},
	'S':   
		 {
		 	'hide':
	'tableview_type tableview_find button_find chord_num num_chords label_middle button_chord button_arp lbl_chord lbl_fullchord lbl_definition sp_span lbl_span button_up button_down tableview_prog tableview_prog_display label_centroid switch_centroid'.split(),
			'show': 
	'tableview_scale tableview_root button_scale_tones button_scale_notes button_play_scale btn_sharpFlat tri_chord_label label1 fretboard'.split(),
	},
	'P':    
		{
			'hide':
	'tableview_find button_find button_scale_tones button_scale_notes tableview_scale button_play_scale lbl_chord lbl_fullchord btn_sharpFlat tableview_type label1 tableview_type'.split(),
			'show': 
	'chord_num num_chords label_middle button_chord button_arp sp_span lbl_span tri_chord_label button_up button_down tableview_prog tableview_root fretboard tableview_prog_display label_centroid switch_centroid'.split()
	},
	}
	pub.sendMessage('changemode',mode=newmode)
	fretboard.cc_mode = newmode
	mode_hs = hideshow[newmode]
	for view in mode_hs['hide']:
		try:
			mainView[view].hidden = True
		except:
			console.hud_alert('in toggle_mode, view {} does not exist'.format(view))
	for view in mode_hs['show']:
		try:
			mainView[view].hidden = False
		except:
			console.hud_alert('in toggle_mode, view {} does not exist'.format(view))
			
	if newmode == 'C': # special stuff for identify
		mainView['button_edit_chord'].title = 'type'
	elif newmode == 'S':
		mainView['button_edit_chord'].title = 'mode'
		# set default and C major
	elif newmode == 'I':
		mainView['button_edit_chord'].title = ''
		tvFind.data_source.items = []
		tvFind.reload_data()
		fretboard.findScaleNotes = []
		find.row = -1
		fretboard.touched = {}
	elif newmode == 'P':
		mainView['tableview_prog_display'].hidden = True
		mainView['button_edit_chord'].title = 'progr'
	fretboard.set_needs_display()
	mainView.set_needs_display()
	
	
def set_scale_display(button):
	fretboard.scale_display_mode = button.title
	fretboard.set_needs_display()
	
def onFind(button):
	fingered = [fretboard.touched[key][0] for key in fretboard.touched.keys()]
	if fingered:
		fingered = sorted([x%12 for x in fingered])
		pure = []
		missing_1 = []
		missing_2 = []
		chord_list = []
		for root in range(12):
			notes_in_key = rotate(range(12),root)
			present = {}
			notevals = []
			for i,note in enumerate(notes_in_key):
				present[i] = True if note in fingered else False
				if present[i]:
					notevals.append(i)
			for chord in ccc['CHORDTYPE']:
				deltas = set(notevals) ^ set(chord[1]) #those notes not in both (symmetric difference)
				if not deltas:
					pure.append({'title':"{}{}".format(ccc['NOTE_NAMES'][root],chord[0]),'root':root,
					'chord':chord[0], 'accessory_type':'none'})
				if deltas == set([0]):
					missing_1.append({'title':"{}{} (no root)".format(ccc['NOTE_NAMES'][root],chord[0]),
					'root':root, 'chord':chord[0], 'accessory_type':'none'})
				if deltas == set([3]) or deltas == set([4]):
					missing_1.append({'title':"{}{} (no 3rd)".format(ccc['NOTE_NAMES'][root],chord[0]),
					'root':root, 'chord':chord[0], 'accessory_type':'none'})
				if deltas == set([7]):
					missing_1.append({'title':"{}{} (no 5th)".format(ccc['NOTE_NAMES'][root],chord[0]),
					'root':root, 'chord':chord[0], 'accessory_type':'none'})
					
		for list in [pure,missing_1]:
			if list:
				chord_list += list
				chord_list.append({'title':"-------",'root':-1, 'chord':-1, 'accessory_type':'none'})
		tvFind.data_source.items = chord_list
		tvFind.data_source.currentNumLines = len(chord_list)
		tvFind.hidden = False
		tvFind.reload_data()

				
def on_slider(sender):
	sound.set_volume(sender.value)
	
def on_slider_arp(sender):
	v = sender.value
	fretboard.arpSpeed = fretboard.arpMin*v + (1.0-v)*fretboard.arpMax
	
def onSpanSpinner(sender):
	''' repond to changes in span'''
	pub.sendMessage('changespan',data=sender.value)

#--- =====================
	
class SettingListDelegate(object):
	''' list of current chord calc "settings".   '''
	def __init__(self):
		if not os.path.exists(SettingsFileName):
			console.hud_alert('Creating base settings file','error')
			self.items = [{'title':'default',
			'capos':                                           [],
			'filters':                                 [],
			'instrument':                      'GUITAR',
			'accessory_type':  'none'}]
			fh = open(SettingsFileName,'w')
			json.dump(self.items,fh,indent=1)
			fh.close()
		else:
			fh = open(SettingsFileName,'r')
			self.items = json.load(fh)
			fh.close()
			
		self.currentNumLines = len(self.items)
		self.delegator = mainView['view_settingsView']['tv_SettingsList']
		
	def tableview_number_of_sections(self, tableview):
		# Return the number of sections (defaults to 1)
		return 1
		
	def tableview_number_of_rows(self, tableview, section):
		# Return the number of rows in the section
		return self.currentNumLines
		
	def tableview_cell_for_row(self, tableview, section, row):
		# Create and return a cell for the given section/row
		import ui
		cell = ui.TableViewCell()
		cell.text_label.text = self.items[row]['title']
		return cell
		
	def tableview_can_delete(self, tableview, section, row):
		# Return True if the user should be able to delete the given row.
		return True
		
	def tableview_can_move(self, tableview, section, row):
		# Return True if a reordering control should be shown for the given row (in editing mode).
		return True
		
	def tableview_delete(self, tableview, section, row):
		# Called when the user confirms deletion of the given row.
		self.currentNumLines -=1 # see above regarding hte "syncing"
		self.delegator.delete_rows((row,)) # this animates the deletion  could also 'tableview.reload_data()'
		del self.items[row]
		
	def tableview_move_row(self, tableview, from_section, from_row, to_section, to_row):
		# Called when the user moves a row with the reordering control (in editing mode).
		self.items = listShuffle(self.items,from_row,to_row)
		
	def tableview_did_select(self, tableview, section, row):
		# Called when a row was selected.
		selection = self.items[row]
		pub.sendMessage('changesettings',settings=selection)

		
#--- ===========================================
			


class Find(object):
	def __init__(self,items=None,delegator=None):
		self.delegator = delegator
		self.items = items
		self.currentNumLines = len(self.items)
		self.row = -1
		self.key = None
		self.chord = None
		pub.subscribe(self.updateFind,'updatefind')
		
	def reset(self):
		self.items = []
		self.row = -1
		fretboard.findScaleNotes= {}
		self.delegator.reload_data()
		
	def updateFind(self,chordlist=None):
		self.items = chordlist
		self.currentNumLines = len(chordlist)
		self.delegator.hidden = False
		self.delegator.reload_data()
		
	def tableview_number_of_sections(self, tableview):
		# Return the number of sections (defaults to 1)
		return 1
		
	def tableview_number_of_rows(self, tableview, section):
		# Return the number of rows in the section
		return self.currentNumLines
		
	def tableview_cell_for_row(self, tableview, section, row):
		# Create and return a cell for the given section/row
		import ui
		cell = ui.TableViewCell()
		try:
			cell.text_label.text = self.items[row]['title']
		except IndexError:
			return
		cell.text_label.text_color = 'red' if self.items[row]['accessory_type'] == 'checkmark' else 'black'
		return cell
		
	def tableview_can_delete(self, tableview, section, row):
		# Return True if the user should be able to delete the given row.
		return False
		
	def tableview_can_move(self, tableview, section, row):
		# Return True if a reordering control should be shown for the given row (in editing mode).
		return False
		
	def tableview_delete(self, tableview, section, row):
		pass
		
	def tableview_move_row(self, tableview, from_section, from_row, to_section, to_row):
		pass
		
	def tableview_did_select(self, tableview, section, row):
		# Called when a row was selected.
		if self.items[row]['root'] == -1: # separator
			return
		if self.items[row]['accessory_type'] == 'checkmark': #deselect this one
			self.items[row]['accessory_type'] = 'none'
			self.row = -1
			fingering = []
		else: # its unmarked
			if self.row != -1: # there is one selected
				self.items[self.row]['accessory_type'] = 'none' #deselect
			self.row = row
			self.items[self.row]['accessory_type'] = 'checkmark'
			key = self.items[row]['root']
			self.chordtype = self.items[row]['chord']
			for item in chord.items:
				if item['title'] == self.items[row]['chord']:
					fingering = item['fingering']
					break
		pub.sendMessage('updatefindscale',pKey=key, pChord=fingering)
			
	
		
class InstrumentEditor(ui.View):
	def did_load(self):
		self.spinnerArray = []
		self.octaveTextArray = []
		self.textField = self['txt_title']
		self.textField.spellchecking_type = False
		self.textField.autocorrection_type = False
		self.octaveTextField = self['txt_octave']
		self.tuningButton = self['btn_tuning']
		self.notes = []
		self.octaves = []
		self['button_IE_OK'].action = self.onOkay
		self['button_IE_Cancel'].action = self.onCancel
		self['label1'].background_color = self['label2'].background_color = self.background_color
		self['label3'].background_color = self.background_color
		self.maxOctave = 7
		self.maxPointer = 11
		
	def onNewInstrument(self,sender):
		''' allow editing of new instrument based on current instrument'''
		if model._InstrumentTuning:
			notes = model._InstrumentTuning
		else:
			console.hud_alert('Please select an instrument as the base for new one','error',2)
			return
			
		mainViewShield.conceal()
		numStrings = len(notes)
		self.span = model._Span
		self.octave = model._InstrumentOctave
		self.textField.text = model._InstrumentName
		self.octaveTextField.text = "{}".format(self.octave)
		spinnerWidth = min(75,int(self.width/float(numStrings)))
		space = self.width - numStrings*spinnerWidth
		spacer = int(space/float(numStrings + 1))
		self.notes = [note for note in notes]
		self.octaves = [divmod(note,12)[0] for note in notes]
		self.spinnerFactor = 0.17
		for i in range(numStrings):
			temp = Spinner(name="string{}".format(i),
							initialValue = ccc['NOTE_NAMES'],
							spinnerSize = (spinnerWidth,40),
							fontSize = 16,
							action=self.onSpinner,
							limitAction=self.onSpinnerLimit
							)
			temp.pointer = self.notes[i] % 12
			
			tempOctave = ui.TextField(name='octave{}'.format(i),
									frame=(0,0,40,32),
									)
			tempOctave.text = "{}".format(self.octaves[i])
			temp.position = (spacer+i*(spacer+spinnerWidth), int(self.spinnerFactor*self.height))
			location = (spacer+i*(spacer+spinnerWidth),int(self.spinnerFactor*self.height+42),0.0,0.0)
			tempOctave.frame = tuple(map(add,tuple(location),tuple(tempOctave.frame)))
			self.add_subview(temp)
			self.add_subview(tempOctave)
			self.spinnerArray.append(temp)
			self.octaveTextArray.append(tempOctave)
		self.SpanSpinner = Spinner(name='EIspanSpinner',
															initialValue = self.span,
															limits=(2,self.span+2),
															spinnerSize = (spinnerWidth,32),
															fontSize = 16
															)
		self.SpanSpinner.position = (240,185)			
		self.add_subview(self.SpanSpinner)
		self.tuningButton.action = self.playTuning
		self.update_tuning_label()
		self.hidden  = False
		self.bring_to_front()
		
		
	def onOkay(self,sender):
		global mainView
		if self.textField.text in [entry['title'] for entry in instrument.items]:
			console.hud_alert("Needs new name, please edit entry",'error',2)
			return
		entry = {}
		entry['title'] = self.textField.text
		entry['octave'] = self.octave
		notes = []
		octaves = [int(tf.text) for tf in self.octaveTextArray]
		for i,note in enumerate([int(x.pointer) for x in self.spinnerArray]):
			notes.append(note+octaves[i]*12)
			
		entry['notes'] = notes
		entry['span'] = int(self.SpanSpinner.value)
		entry['accessory_type'] = 'none'
		pub.sendMessage('addnewinstrument',entry=entry)
		
		self.hidden = True
		for subview in self.spinnerArray:
			self.remove_subview(subview)
		for subview in self.octaveTextArray:
			self.remove_subview(subview)
		self.spinnerArray = []
		self.octaveTextArray = []
		mainViewShield.reveal()
					
	def onCancel(self,sender):
		self.hidden = True
		for subview in self.spinnerArray:
			self.remove_subview(subview)
		for subview in self.octaveTextArray:
			self.remove_subview(subview)
		self.spinnerArray = []
		self.octaveTextArray = []
		mainViewShield.reveal()
			
	def update_tuning_label(self):
		pointers = [spinner.pointer for spinner in self.spinnerArray]
		octaves = [int(tf.text) for tf in self.octaveTextArray]
		def mulby12(item):
			return item*12
		notes = map(add,pointers,map(mulby12,octaves))
		label = tuningLabel(notes)
		self.tuningButton.title = label
		
	def onSpinner(self,sender):
		self.update_tuning_label()
		
	def onSpinnerLimit(self,sender,arrow):
		string = int(sender.name[-1])
		direction =  -1 if 'down' in arrow.name.lower() else 1
		pointer = sender.pointer
		currentOctaves = [int(x.text) for x in self.octaveTextArray]
		thisOctave = currentOctaves[string]
		if pointer == 0:  # at begining, wants to go lower
			if thisOctave: #its non zero, so let it go lower by itself
				self.octaveTextArray[string].text = "{}".format(thisOctave-1)
			else: # it zero, need to leave it, shift all others up and shift base octave down
				if self.octave == 0 or self.maxOctave in currentOctaves:  # no can do
					console.hud_alert("out of range",'error',2)
					return
				self.octave -= 1
				self.octaveTextField.text = "{}".format(self.octave)
				for i,octaveText in enumerate(self.octaveTextArray):
					if i == string:
						continue 
					else:
						thisOctave = int(octaveText.text)
						octaveText.text = "{}".format(thisOctave+1)
			self.spinnerArray[string].pointer = self.maxPointer
		else: #we're at the top, need to increase this one
			if thisOctave < self.maxOctave: # its not too large (by itself)
				self.octaveTextArray[string].text = "{}".format(thisOctave+1)
			else: # its amxed out, neet to leave it, shift all others downa down shift base octave up
				if self.octave == self.maxOctave or 0 in currentOctaves: # no can do
					console.hud_alert("out of range",'error',2)
					return
				self.octave += 1
				self.octaveTextField.text = "{}".format(self.octave)
				for i,octaveText in enumerate(self.octaveTextArray):
					if i != string:
						continue #
					else:
						thisOctave = int(octaveText.text)
						octaveText.text = "{}".format(thisOctave-1)
			self.spinnerArray[string].pointer = 0
		self.update_tuning_label()
		
	def playTuning(self,button):
		tones =  [spinner.pointer for spinner in self.spinnerArray]
		octaves = [int(tf.text) for tf in self.octaveTextArray]
		baseOctave = self.octave
		for i,tone in enumerate(tones):
			sound.play_effect(getWaveName(tone,octaves[i]+baseOctave))
			time.sleep(fretboard.arpSpeed)
				
class ConfigView(ui.View):
	def did_load(self):
		ccc.configViewInit(self)
		
			
class SettingsView(ui.View):
	def did_load(self):
		ccc.settingsViewInit(self)
			
						
def doProgression(sender,row):
	global chordDiagrams,chordProgView # chordProgView is a container view for the chordprogs
	fullWidth = chordProgView.width
	fullHeight = chordProgView.height
	panelWidth = fullWidth/2
	panelHeight = fullHeight/2
	if sender.name == 'dd_prog':
		current = sender.current
		key = keyDropDown.current['noteValue']
	else:
		current = progDropDown.current
		key = sender.current['noteValue']
	chords = current['chords']
	for subv in chordDiagrams:
		chordProgView.remove_subview(subv)
	chordDiagrams.clear()
	splits = [(int(x.split('-')[0]),x.split('-')[1]) for x in chords]
	for i,val in enumerate(splits):
		ofs,type = val
		thisRow,thisCol = divmod(i,2)
		upperX = thisCol*panelWidth
		lowerX = upperX + panelWidth
		upperY = thisRow*panelHeight
		lowerY = upperY + panelHeight
		thisCD = ChordDiagram(frame=(upperX, upperY, lowerX, lowerY),
																			key = keyDropDown.current['noteValue'],
																			offset = ofs, 
																			chord = type,
																			row = thisRow,
																			col = thisCol,
																			margin = 20)
		chordProgView.add_subview(thisCD)
		thisCD.send_to_back()
		chordDiagrams.append(thisCD)

	chordProgView.hidden=False
	chordProgView.enabled=True

	
def doChordChange(sender,row):
	pass
	
def doScaleChange(sender,row):
	pass
	
	
	
#---##########################################


class ProgDisplay(TVTools,object):
	'''  '''
	def __init__(self,delegator):
		self.items = [{'title':'', 'accessory_type': 'none'}]
		self._Delegator = delegator
		pub.subscribe(self.updateProgressionList,'setprogressiondata')
		
	def reset(self):
		for item in self.items:
			item['accessory_type'] = 'none'
			
	def updateProgressionList(self,progFingerings=None, progChords=None):	
		self.items = [{'title':(x[0]+x[2]), 'accessory_type':'none'} for x in progChords]
		rowHeight = self._Delegator.row_height
		self._Delegator.height = len(self.items)*rowHeight
		self._Delegator.reload_data()

	def tableview_did_select(self,tableView,section,row):  
		self.setTableViewItemsRow(row)
		tableView.reload_data()
		time.sleep(0.1)
		print(self.items[row])
		pub.sendMessage('updateprogressionpointers',
								nextChord=row,nextFingering=-1)
						
	def tableview_number_of_sections(self, tableview):
		# Return the number of sections (defaults to 1)
		return 1
		
	def tableview_number_of_rows(self, tableview, section):
		# Return the number of rows in the section
		return len(self.items)
		
	def tableview_cell_for_row(self, tableview, section, row):
		# Create and return a cell for the given section/row
		cell = ui.TableViewCell()
		cell.text_label.text = self.items[row]['title']
		cell.accessory_type = self.items[row]['accessory_type']
		return cell
		
	def tableview_can_delete(self, tableview, section, row):
		# Return True if the user should be able to delete the given row.
		return False
		
	def tableview_can_move(self, tableview, section, row):
		# Return True if a reordering control should be shown for the given row (in editing mode).
		return True
		
	def tableview_delete(self, tableview, section, row):
		# Called when the user confirms deletion of the given row.
		self.currentNumLines -=1 # see above regarding hte "syncing"
		self.delegator.delete_rows((row,)) # this animates the deletion  could also 'tableview.reload_data()'
		del self.items[row]
		
	def tableview_move_row(self, tableview, from_section, from_row, to_section, to_row):
		# Called when the user moves a row with the reordering control (in editing mode).
		self.items = listShuffle(self.items,from_row,to_row)
		
	@property
	def prog(self):
		return self._prog
		
	@prog.setter
	def prog(self,value):
		self._prog = value
		
class Progr(TVTools,object):
	''' create sets of chords that are relevant to current filtering for the designated progression '''
	def __init__(self,delegator):
		self.items = [{'title':x['title'], 'chords':x['chords'], 'accessory_type':'none'} 
						for x in ccc['PROGRESSIONS']]
		self.items.insert(0,{'title':'choose prog','accessory_type':'none'})
		self._progChords = []
		self._progFingerings = []
		self._isExpanded = False
		self._Delegator = delegator
		self._expanded = None
		self._contracted  = None
		pub.subscribe(self.updateProgressionSettings, 'updateProgressionSettings')

	def setFrameConstants(self):
		x,y,width,height = self._Delegator.frame
		row_height = self._Delegator.row_height
		self._expanded = (x,y,500,row_height*len(self.items))
		self._contracted = (x,y,100,row_height)
		#self._Delegator.frame = self._contracted

		
	def expand(self):
		self._Delegator.frame = self._expanded
		self._isExpanded = True
		
	def contract(self):
		self._delegator.frame = self._contracted
		self._isExpanded = False
		
		
	def onEdit(self,button):
		if self.delegator.editing:
			self.delegator.editing = False
			self.delegator.reload_data()
		else:
			self.delegator.editing = True
			self._progChords = []
			
			for item in self.items:
				item['accessory_type'] = 'none'
								
	def reset(self):
		for item in self.items:
			item['accessory_type'] = 'none'
			
	def updateProgressionSettings(self):
		self._progFingerings = []
		self.setTableViewItemsRow(1)
		self.getProgressionChords(1) # row 0 is the "expand" request
		for chord in self._progChords:
			self._progFingerings.append(model.calc_fingerings(chordtypeEntry=chord))
		pub.sendMessage('setprogressiondata', 
						progFingerings=self._progFingerings, progChords=self._progChords)
		
			
	def createProgressionFingerings(self):
		self._progFingerings= []
		for chord in self._progChords:
			self._progFingerings.append(model.calc_fingerings(chordtypeEntry=chord))

		
	def getProgressionChords(self,row):
		key = model._RootNoteName
		keyNoteValue = model._RootNoteValue
		self._progChords = []
		if key:
			for chord in self.items[row]['chords']:
				offset,type = chord.split('-')
				realNote = (int(offset)+keyNoteValue) % 12
				self._progChords.append((ccc['NOTE_NAMES'][realNote],realNote,type))

	def tableview_did_select(self,tableView,section,row):  
		if not model._InstrumentTuning:
			return
		if not model._RootNoteValue:
			return
		def animationExpand():
			tableView.frame = self._expanded
		def animationContract():
			tableView.frame = self._contracted
		ui.animate(animationExpand, duration=0.1)
		def doContract():
			ui.animate(animationContract, duration=0.1)
		if row == 0:
			self.expand()
			mainView['tableview_prog_display'].hidden = True
		else:
			self.setTableViewItemsRow(row)
			self._prog = self.getProgressionChords(row)
			tableView.reload_data()
			ui.delay(doContract,0.1)		
			mainView['tableview_prog_display'].hidden = False
			self.createProgressionFingerings()
			pub.sendMessage('setprogressiondata', 
						progFingerings=self._progFingerings, progChords=self._progChords)
						
	def tableview_number_of_sections(self, tableview):
		# Return the number of sections (defaults to 1)
		return 1
		
	def tableview_number_of_rows(self, tableview, section):
		# Return the number of rows in the section
		return len(self.items)
		
	def tableview_cell_for_row(self, tableview, section, row):
		# Create and return a cell for the given section/row
		cell = ui.TableViewCell()
		cell.text_label.text = self.items[row]['title']
		cell.accessory_type = self.items[row]['accessory_type']
		return cell
		
	def tableview_can_delete(self, tableview, section, row):
		# Return True if the user should be able to delete the given row.
		return False
		
	def tableview_can_move(self, tableview, section, row):
		# Return True if a reordering control should be shown for the given row (in editing mode).
		return True
		
	def tableview_delete(self, tableview, section, row):
		# Called when the user confirms deletion of the given row.
		self.currentNumLines -=1 # see above regarding hte "syncing"
		self.delegator.delete_rows((row,)) # this animates the deletion  could also 'tableview.reload_data()'
		del self.items[row]
		
	def tableview_move_row(self, tableview, from_section, from_row, to_section, to_row):
		# Called when the user moves a row with the reordering control (in editing mode).
		self.items = listShuffle(self.items,from_row,to_row)
		
	@property
	def prog(self):
		return self._prog
		
	@prog.setter
	def prog(self,value):
		self._prog = value
#--- MAIN PROGRAM 

if __name__ == "__main__":


	if not os.path.exists('waves'):
		console.alert('waves sound files not present, run makeWave.py')
		sys.exit(1)
		
	missingInstr = ''
	for dir in [entry[1] for entry in cccInit.SOUND_FILE]:
		if not os.path.exists(os.path.join('waves',dir)):
			missingInstr += "{} ".format(dir)
	if missingInstr:
		console.hud_alert('{} are not available, default sounds will be used'.format(missingInstr),'error',2)

	ccc = CCC()		
	model = Model(ccc)
									
	if not os.path.exists(ConfigFileName):
		ccc.createConfig()
	else:
		ccc.restoreConfig()



	screenSize = ui.get_screen_size()
#	aspect = screenSize[0]/screenSize[1]
#	aspect = aspect if aspect > 1 else 1/aspect
	screenHeight = min(screenSize)
	screenWidth = max(screenSize)
			
	mainView = ui.load_view()	
	mainViewShield = Shield(mainView,local=True, name='mainview_shield')				
	numChordsTextView = mainView['num_chords']
	chordNumTextView = mainView['chord_num']
	middle_field = mainView['label_middle']
	fretboard = mainView['fretboard']
	tvRoot = mainView['tableview_root']
	root = Root(ccc['ROOT_LIST_CLEAN'])
	tvRoot.data_source = tvRoot.delegate = root
	
	tvType = mainView['tableview_type']
	chord = Chord(ccc['CHORD_LIST_CLEAN'])
	chord.reset()
	tvType.data_source = tvType.delegate = chord
	mainView['button_edit_chord'].action = chord.onEdit
	
	tvInst = mainView['tableview_inst_tune']
	tuningDisplay = mainView['button_tuning']
	tuningDisplay.title = ''
	tuningDisplay.action = play_tuning
	
	def updateTuningDisplay(text=None):
		global tuningDisplay
		tuningDisplay.title=text
	pub.subscribe(updateTuningDisplay,'updatetuningdisplay')
	
	
	# fretboard is a custom view and is instanciated by the ui.load_view process
	instrument = Instrument(ccc['TUNING_LIST_CLEAN'])
	mainView['button_edit_instrument'].action = instrument.onEdit
	instrument.reset()
	tvInst.data_source = tvInst.delegate = fretboard.instrument = instrument
	
	
	tvFilters = mainView['tableview_filters']
	filters = Filters()
	pub.subscribe(filters.set_filters,'updateFilterSet')
	instrument.tvFilters = tvFilters
	instrument.filters = filters
	filters.instrument = instrument
	tvFilters.data_source = tvFilters.delegate = filters
	tvFilters.hidden = False
	mainView['button_edit_filters'].action = filters.onEdit
	
	tvFind = mainView['tableview_find']
	find = Find(items=[],delegator=tvFind)
	tvFind.data_source = find
	tvFind.delegate = find
	tvFind.hidden = True
	
	tvScale = mainView['tableview_scale']
	tvScale.data_source.items = []
	tvScale.hidden = True
	scale = Scale(ccc['SCALE_LIST_CLEAN'])
	tvScale.data_source = tvScale.delegate = scale
	
	mainView['button_arp'].action = play
	mainView['button_chord'].action = play
	mainView['button_scale_notes'].action = set_scale_display
	mainView['button_scale_tones'].action = set_scale_display
	mainView['button_find'].action = fretboard.onFind
	mainView['button_find'].hidden = True
	mainView['button_up'].action = mainView['button_down'].action = onPrevNext
	mainView['button_play_scale'].action = playScale
	mainView['btn_sharpFlat'].action = fretboard.sharpFlat
	mainView['btn_sharpFlat'].hidden = True
	mainView['slider_arp'].action = on_slider_arp
	mainView['lbl_chord'].hidden = True
	mainView['lbl_fullchord'].hidden = True
	mainView['lbl_definition'].hidden = True
	
	tvCapos = mainView['tableview_capos']
	capos = Capos(ccc['CAPOS'])
	pub.subscribe(capos.syncNumStrings,'syncnumstrings')
	mainView['button_edit_capos'].action = capos.onEdit
	tvCapos.data_source = tvCapos.delegate = capos
	
	spanSpinner = Spinner(spinnerSize=(80,50),
												name='sp_span',
												fontSize = 18,
												initialValue=ccc['SPAN_DEFAULT_UNKNOWN'],
												limits=(2,ccc['SPAN_DEFAULT_UNKNOWN']+2),
												action=onSpanSpinner)
	
	mainView.add_subview(spanSpinner)
	spanSpinner.position =(580,443)		
	
	
	def syncSpanSpinner(span=None):
		global spanSpinner
		if span:
			spanSpinner.value = span
			spanSpinner.limits  = (1,span+2)
	pub.subscribe(syncSpanSpinner,'syncspanspinner')
	mainView['view_fretEnter'].hidden = True
	mainView['sp_span'].hidden = True
	mainView['button_save_config'].action = ccc.onConfigMain
	mainView['view_settingsView'].hidden = True
	settings = SettingListDelegate()
	mainView['view_settingsView']['tv_SettingsList'].data_source = settings
	mainView['view_settingsView']['tv_SettingsList'].delegate = settings
	mainView['button_save'].action = ccc.onSettingsSave
	mainView['button_load'].action = ccc.onSettingsLoad	
	mainView['view_instrumentEditor'].hidden = True
	mainView['button_new_instrument'].action = mainView['view_instrumentEditor'].onNewInstrument
	mainView['tri_chord_label'].frame = (-200,-200,0,0) # since it wont' hide,send it to hell!!!!'
	fretboard.set_chordnumDisplays(chordNumTextView,numChordsTextView)
	sound.set_volume(0.5)
	modeDropDown = DropDown(frame=(570,400,120,32),
							name='dd_mode',
							data=[{'title':'chords', 'tag':'C'},
								  {'title':'identify','tag':'I'},
								  {'title':'scale','tag':'S'},
								   {'title':'progr','tag':'P'}],
							action=toggle_mode
							)

	mainView.add_subview(modeDropDown)
	
	tvProgs = mainView['tableview_prog']
	tvProgs.hidden = True
	progs = Progr(delegator=tvProgs)
	tvProgs.data_source = tvProgs.delegate = progs
	progs.setFrameConstants()
	
	tvProgDisplay = mainView['tableview_prog_display']
	progDisplay = ProgDisplay(tvProgDisplay)
	tvProgDisplay.data_source = tvProgDisplay.delegate = progDisplay
	tvProgDisplay.scroll_enabled = False
	
	progCentroidSwitch = mainView['switch_centroid']
	progCentroidSwitch.action = model.onCentroidSwitch
	pub.sendMessage('centroidswitch',switch=progCentroidSwitch.value)
	
	toggle_mode(modeDropDown,0) # default to calc
	mainView.present(style='full_screen',orientations=('landscape',))
