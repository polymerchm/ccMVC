#ChordCalculus


A full-featured chord/scale/progression calculator/player 
by Steven K Pollack


ChordCalculus (CC) is a tool for players of fretted instruments. CC will allow the user to choose from a  large number of pre-defined fretted instruments in a variety of tunings.   Additionally, the user can define new instruments and/or tunings.    Single or multiple capos can be added.  The user then picks from one of four operatin modes:

*Chord Calculator

*Chord Identifer

*Scale Display

*Progression Player

The app has three "regions".  The right "panel" has the Insrument/Tuning, Filter  and the Capo selectors.  



There are four modes of operation: Calc, Identify and Scale, and Progression.  These are selected by the C, I,S,P selector in the middle of the screen.

# Chord Calculator

Select an instrument/tuning (upper right-hand corner), a root (key) (left-most side) and a chord type, (second column on left), and all possible fingerings will be displayed on the fretboard.  You cycle through them with the up and down arrows.  The span (the maximum number of frets from the lowest to highest fingered fret) setting is set as the default value for the instrument and can be modified to minimize display of chords with "big stretch" fingerings.   

If you sweep up or down the fretboard, it will "fast forward" the chords in proportion to the distance you sweep. If you do a long-touch (> 1/2 second), the present chords will jump to the closest chord to that fret. If you tap the fretboard, all chord tones for the selected chord (the "chord scale") will be highlighted.  Tapping again hide it. 

By choosing various filters (center right-hand list), you can  reduce the number and type of chords displayed. For example, 'LOW 3' is a mandolin filter that only presents chords played on the lower 3 strings and leaves the high E string unplayed.  The 'DOUBLE STOP' filter (also for mandolin) will show all valid double stops for a given chord (2 note chord partials). 'NO DEAD' will only show chords where every string is sounded.  For guitar type instruments, there is a LOW 4 and HIGH 4 for jazz type chording.

If a given instrument/tuning cannot represent the chord, a "No Chord" message is displayed.  The filters NO_ROOT, NO_3RD and NO_5TH will find chord shapes for 
mandolin (you notice the mandolin emphasis here) that allows those chord tones not to be 
ignored in testing for valid fingerings.  On mandolins, and other 4 stringed instrumetns, the player often abandons the root, 3rd or 5th.  The filter FULL CHORD clears filters which allow for missing chord tones (root, 3rd or 5th).  

Hitting the chord button will play the chord (see makeWaves.py above).  Hitting the arpeggio button will play the notes one by one. Hitting the button which describes the individual string tunings will play the sound of the instrument when un-fretted (when a capo(s) is applied, it effects the tones appropriately)

The slider at the bottom is a volume control and the slider at the top determines the "speed" of the arpeggio.

For any chord, touching the fretboard will display all of the chordtones on the entire fretboard.  Touching it again displays the current chord.

The chord tones and notes are displayed in the upper right 

# Chord Identifier

In identify mode, you touch the fingerboard on a string/fret to indicate a fingering.  Tapping a marked string/fret erases the fingering of that string.   Tapping at the nut will include the open string.   When you hit Find, all possible "names" for the chord are given.  If the fingering is a chord partial, then the missing chord tones are indicated.  If there are capos, you will be prevented from fretting "behind" the capo.  If you tap one of the "names" for the chord, all of its chord tones are displayed on the fretboad and the original notes in the query are circled.   Tapping the fretboard clears this "chord scale".


#Progression Player

In this mode, you select from a set of pre-programmed set of chord progressions.   One selected, chords are  calculates for all chords at all positions on the fret board (with no filters and 6 strings, there is a noticible delay).  Tapping on the selector for the chords in in the progression will display that chord on a fretboard.   All functions in chord mode apply.   If "chord centroid" is set, then when switching between chords, the program will try to maintain the next displayed chord as close as possible ot the chord lsat displayed.   What every chord is currenly displayed on each fretbaord will be played back when the PLay Progression button is hit.

# Scale Display

In scale mode, you select a key (the root) and the scale type (second column on left).  All notes on the scale across the entire fretboard are displayed.  If you touch a root position, a two octave display is highlighted.  Hitting the scale button plays the scale.  The speed/volume sliders are also effective here.  If the mode is one of the greek modes, then the base key is displayed in the upper right hand corner (for example, A Aoelian is based on C Ionian (major), A Dorian is actually the key of G Ionian (major)). Every effort is made to have the appropriate anharmonics (sharps or flats) display based on the  key signature (or for the greeek modes, its base).  You can toggle the display between scale notes and scale degrees and, for "ambiguous" key signatures (like A#/Bb), you can toggle anharmonic notes between sharps and flats. A Data Selector is presented to allow for different modes of calculating a 2 0ctave scale.  This is experimental at this point.  

# Capos:

The list (lower right hand corner) allows the user to select one or more capos. When you select a capo, you are prompted for a fret to place it.  All subsequent operations acccount for the presence of the capos.  The full capo will adjust to the number of strings (except 5-string banjo, see below)  A partial capo will only fret a subset of strings.  As supplied these assume a 6-stringed instrument.  The standard partial capos predefined are the "drop E" capo that only covers 5 consecutive guitar strings (when placed on the second fret, accomplishes a drop D tuning, up a tone without retuning) and the "sus2" capo (covers the "ADG" strings or the "DGB" strings of a guitar).  Five string banjo capos are one for the "normal" four strings and a one strng capo for the 5th string.  Multiple capos are allowed.  

# Editing the Tables (Instruments, Chord Types, Filters, Progressions)

The labels of the editable tables are actually buttons that enable/disable deleting rows or re-ordering each editable table.  If you wish to save this new "configuration", you hit the "Config" button.  It will give you the option of saving the current setup, or restoring the "factory setting"  (from the file chordcalc_constants.py).  The configuration is stored as a json object in the file "config.ini"

# Saving the Settings

The Save and Load buttons allow the user to save the current instrument, filters and capos as a named entry in the "Settings" list.  If an existing default setting is changed, the user is prompted to confirm the overwrite.  There also the option to edit the list (delete rows/reorder). The data for this list is stored in a file called "settings.ini"

# Instrument Editor

Hitting the New button on the main menu brings up an instrument editor.  It will take the current selected instrument/tuning and allow you to adjust the tuning.  You can then save this to the Intrument/tuning list.  You will be forced to use a new name.  If you want to delete it later, you can edit the intrument/tuning list to remove it.  To have this intrument saved for the next time you run chord calc, hit the "config" button to save it.  

# Progression Editor

In progression mode
