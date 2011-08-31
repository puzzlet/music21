# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         audioSearch.repetitionGame.py
# Purpose:      Repetition game, human player vs human player
#               
#
# Authors:      Jordi Bartolome
#               Michael Scott Cuthbert
#
# Copyright:    (c) 2011 The music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------


from music21 import environment
from music21 import scale, stream, note, pitch
from music21.audioSearch.base import *
from music21.audioSearch import recording
import time


class repetitionGame():
    
    def __init__(self):
        self.useScale = scale.ChromaticScale('C4')
        self.round = 0
        self.good = True
        self.gameNotes = []        
        print "Welcome to the music21 game!"
        print "Rules:"
        print "Two players: the first one plays a note. \nThe second one has to play the first note and a new one."
        print "Continue doing the same until one fails."
#        time.sleep(2)
        print "3, 2, 1 GO!"    
         
     
    def game(self):       
        
        self.round = self.round + 1
        print "self.round %d" % self.round
    #    print "NOTES UNTIL NOW: (this will not be shown in the final version)"
    #    for k in range(len(self.gameNotes)):
    #        print self.gameNotes[k].fullName
        
        seconds = 2 + self.round
        freqFromAQList = getFrequenciesFromMicrophone(length=seconds, storeWaveFilename=None)
        detectedPitchesFreq = detectPitchFrequencies(freqFromAQList, self.useScale)
        detectedPitchesFreq = smoothFrequencies(detectedPitchesFreq)
        (detectedPitchObjects, listplot) = pitchFrequenciesToObjects(detectedPitchesFreq, self.useScale)
        (notesList, durationList) = joinConsecutiveIdenticalPitches(detectedPitchObjects)
        j = 0
        i = 0
        while i < len(notesList) and j < len(self.gameNotes) and self.good == True:
            if notesList[i].name == "rest":
                i = i + 1
            elif notesList[i].name == self.gameNotes[j].name:              
                i = i + 1
                j = j + 1
            else:
                print "WRONG NOTE! You played", notesList[i].fullName, "and should have been", self.gameNotes[j].fullName
                self.good = False
           
        if self.good == True and j != len(self.gameNotes):
            self.good = False
            print "YOU ARE VERY SLOW!!! PLAY FASTER NEXT TIME!"
            
        if self.good == False:
            print "YOU LOSE!! HAHAHAHA"
    
        else:
            while i < len(notesList) and notesList[i].name == "rest":
                i = i + 1
            if i < len(notesList):
                self.gameNotes.append(notesList[i])  #add a new note
                print "WELL DONE!"
            else:
                print "YOU HAVE NOT ADDED A NEW NOTE! REPEAT AGAIN NOW"
                self.round = self.round - 1
        return self.good
                

if __name__ == "__main__":
    rG = repetitionGame()
    good = True
    while good == True:
        good = rG.game()
            
#------------------------------------------------------------------------------
# eof
