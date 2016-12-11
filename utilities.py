import math

def listShuffle(list,row_from, row_to):
	''' a method to re-order a list '''
	from_item = list[row_from]
	del list[row_from]
	list.insert(row_to,from_item)
	return list
	
def rotate(list,index):
	''' take the input list and rotate it by indicated number of positions
	positive index move items form left side of list to right
	so list[0] become list[-1]
	negative is vice versa'''
	pointer = index % len(list)
	outlist = [list[x] for x in range(pointer,len(list))] + [list[x] for x in range(0,pointer)] 
	return  outlist if index else list
	
def NoneOrNoneList(object):
	''' test if an object is a None or a list of None '''
	if type(object) == type(None):
		return True
	if type(object) == type([]):
		for item in object:
			if type(item) != type(None):
				return False
		return True
		
def uniqify(sequence, idfun=None):
	''' return a unique, order preserved version in input list'''
	if not idfun:
		def idfun(x): return x
	seen = {}
	result = []
	for item in sequence:
		marker = idfun(item)
		if marker in seen.keys():
			continue
		seen[marker] = 1
		result.append(item)
	return result
	
def fingeringToString(list):
	''' turn fingering to a text string for hashing'''
	hashcodes = 'abcdefghijklmnopqrstuvwxyz-'
	return ''.join([hashcodes[item] for item in list])
	
def getChordTypeEntry(chordtype,chord_list):
	''' search chordtype list and create relevant entry for fingeringng search '''
	for i,item in enumerate(chord_list):
		if item['title'] == chordtype:
			return {'row':i, 'fingering':item['fingering'],'title':item['title']}
	return None
	
def isInChord(key, chordtype, note):
	for chordrelnote in chordtype:
		chordnote = (key + chordrelnote) % 12
		if note == chordnote:
			return True
	return False
	
def chordFingeringCentroid(fingering):
	''' determine the "average" fret of a fingering 
	    ignore open or unplayed notes '''
	sum = 0
	count = 0
	for fret in fingering:
		if fret >= 0:
			sum += fret
			count += 1
	return sum/count
			
	
	
import ui

def PathCenteredCircle(x,y,r):
	""" return a path for a filled centered circle """
	return ui.Path.oval(x -r, y -r, 2*r,2*r)
	
def PathCenteredSquare(x,y,r):
	""" return a path for a filled centered circle """
	return ui.Path.rect(x -r, y -r, 2*r,2*r)
