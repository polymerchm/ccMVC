#!python3

from blinker import signal

instrumentSignal = signal('instrument')
chordSignal = signal('chord')
rootSignal = signal('root')
spanSignal = signal('span')
modeSignal = signal('mode')
scaleSignal = signal('scale')
filtersSignal = signal('filter')
caposSignal = signal('capo')
volumeSignal = signal('volume')
speedSignal = signal('speed')
progrSignal = signal('progr')
changeFingeringSignal = signal('changeFingering')
playSignal= signal('play')
changeConfigSignal = signal('changeConfig')
newInstrumentSignal = signal('newInstrument')
settingSignal = signal('settings')
