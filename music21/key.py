# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         key.py
# Purpose:      Classes for keys
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2009, 2010, 2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------
'''This module defines objects for representing key signatures as well as key 
areas. The :class:`~music21.key.KeySignature` is used in 
:class:`~music21.stream.Measure` objects for defining notated key signatures.

The :class:`~music21.key.Key` object is a fuller representation not just of
a key signature but also of the key of a region. 
'''

import doctest, unittest
import copy

from music21 import base
from music21 import exceptions21

from music21 import pitch
from music21 import note
from music21 import interval
from music21 import common
from music21 import scale

from music21 import environment
_MOD = "key.py"
environLocal = environment.Environment(_MOD)

import re


#-------------------------------------------------------------------------------
# store a cache of already-found values
_sharpsToPitchCache = {}

def convertKeyStringToMusic21KeyString(textString):
    '''
    Utility function to change strings in the form of "Eb" to
    "E-" (for E-flat major) and leaves alone proper music21 strings
    (like "E-" or "f#").  A little bit complex because of parsing
    bb as B-flat minor and Bb as B-flat major.
    
    
    >>> from music21 import *
    >>> key.convertKeyStringToMusic21KeyString('Eb')
    'E-'
    >>> key.convertKeyStringToMusic21KeyString('f#')
    'f#'
    >>> key.convertKeyStringToMusic21KeyString('bb')
    'b-'
    >>> key.convertKeyStringToMusic21KeyString('Bb')
    'B-'
    >>> key.convertKeyStringToMusic21KeyString('b#')
    'b#'
    >>> key.convertKeyStringToMusic21KeyString('c')    
    'c'
    '''
    if textString == 'bb':
        textString = 'b-'
    elif textString == 'Bb':
        textString = 'B-'
    elif textString.endswith('b') and not textString.startswith('b'):
        textString = textString.rstrip('b') + '-'
    return textString

def sharpsToPitch(sharpCount):
    '''Given a number a positive/negative number of sharps, return a Pitch 
    object set to the appropriate major key value.

    >>> from music21 import *
    >>> key.sharpsToPitch(1)
    <music21.pitch.Pitch G>
    >>> key.sharpsToPitch(1)
    <music21.pitch.Pitch G>
    >>> key.sharpsToPitch(2)
    <music21.pitch.Pitch D>
    >>> key.sharpsToPitch(-2)
    <music21.pitch.Pitch B->
    >>> key.sharpsToPitch(-6)
    <music21.pitch.Pitch G->
    
    Note that these are :class:`music21.pitch.Pitch` objects not just names:
    
    >>> k1 = key.sharpsToPitch(6)
    >>> k1
    <music21.pitch.Pitch F#>
    >>> k1.step
    'F'
    >>> k1.accidental
    <accidental sharp>
    '''
    if sharpCount is None:
        sharpCount = 0 # fix for C major
    
    if sharpCount in _sharpsToPitchCache.keys():
        # return a deepcopy of the pitch
        return copy.deepcopy(_sharpsToPitchCache[sharpCount])

    pitchInit = pitch.Pitch('C')
    pitchInit.octave = None
    # keyPc = (self.sharps * 7) % 12
    if sharpCount > 0:
        intervalStr = 'P5'
    elif sharpCount < 0:
        intervalStr = 'P-5'
    else:
        return pitchInit # C

    intervalObj = interval.Interval(intervalStr)
    for x in range(abs(sharpCount)):
        pitchInit = intervalObj.transposePitch(pitchInit)    
    pitchInit.octave = None

    _sharpsToPitchCache[sharpCount] = pitchInit
    return pitchInit


# store a cache of already-found values
#_pitchToSharpsCache = {}

fifthsOrder = ['F','C','G','D','A','E','B']
modeSharpsAlter = {'major':0,
                   'minor':-3,
                   'dorian':-2,
                   'phrygian': -4,
                   'lydian': 1,
                   'mixolydian':-1,
                   'locrian':-5,}


def pitchToSharps(value, mode=None):
    '''Given a pitch or :class:`music21.pitch.Pitch` object, 
    return the number of sharps found in that mode.

    The `mode` parameter can be 'major', 'minor', or most
    of the common church/jazz modes ('dorian', 'mixolydian', etc.)
    including Locrian.
    
    If `mode` is omitted or not found, the default mode is major.

    (extra points to anyone who can find the earliest reference to
    the Locrian mode in print.  David Cohen and I (MSC) have been
    looking for this for years).

    >>> from music21 import *

    >>> key.pitchToSharps('c')
    0
    >>> key.pitchToSharps('c', 'minor')
    -3
    >>> key.pitchToSharps('a', 'minor')
    0
    >>> key.pitchToSharps('d')
    2
    >>> key.pitchToSharps('e-')
    -3
    >>> key.pitchToSharps('a')
    3
    >>> key.pitchToSharps('e', 'minor')
    1
    >>> key.pitchToSharps('f#', 'major')
    6
    >>> key.pitchToSharps('g-', 'major')
    -6
    >>> key.pitchToSharps('c#')
    7
    >>> key.pitchToSharps('g#')
    8
    >>> key.pitchToSharps('e', 'dorian')
    2
    >>> key.pitchToSharps('d', 'dorian')
    0
    >>> key.pitchToSharps('g', 'mixolydian')
    0
    >>> key.pitchToSharps('e-', 'lydian')
    -2
    >>> key.pitchToSharps('e-', 'lydian')
    -2
    >>> key.pitchToSharps('a', 'phrygian')
    -1
    >>> key.pitchToSharps('e', 'phrygian')
    0
    >>> key.pitchToSharps('f#')
    6
    >>> key.pitchToSharps('f-')
    -8
    >>> key.pitchToSharps('f--')
    -15
    >>> key.pitchToSharps('f--', 'locrian')
    -20
    
    But quarter tones don't work:
    
    >>> key.pitchToSharps('C~')
    Traceback (most recent call last):
    KeyException: Cannot determine sharps for quarter-tone keys! silly!
    
    '''
    if common.isStr(value): 
        value = pitch.Pitch(value)
    elif 'Pitch' in value.classes:
        value = value
    elif 'Note' in value.classes:
        value = value.pitch
    else:
        raise KeyException('Cannot get a sharp number from value')
    
    sharps = fifthsOrder.index(value.step) - 1
    if value.accidental is not None:
        if value.accidental.isTwelveTone() is False:
            raise KeyException('Cannot determine sharps for quarter-tone keys! silly!')
        vaa = int(value.accidental.alter) 
        sharps = sharps + 7*vaa
    
    if mode is not None and mode in modeSharpsAlter:
        sharps += modeSharpsAlter[mode]
    
    return sharps
#    if common.isStr(value):
#        p = pitch.Pitch(value)
#    else:
#        p = value
#
#    if (p.name, mode) in _pitchToSharpsCache.keys():            
#        return _pitchToSharpsCache[(p.name, mode)]
#
#
#    # start at C and continue in both directions
#    sharpSource = [0]
#    for i in range(1,13):
#        sharpSource.append(i)
#        sharpSource.append(-i)
#
#    minorShift = interval.Interval('-m3')
#    # these modal values were introduced to translate from ABC key values that
#    # include mode specification
#    # this value/mapping may need to be dynamically allocated based on other
#    # contexts (historical meaning of dorian, for example) in the future
#    dorianShift = interval.Interval('M2')
#    phrygianShift = interval.Interval('M3')
#    lydianShift = interval.Interval('P4')
#    mixolydianShift = interval.Interval('P5')
#
#    # note: this may not be the fastest approach
#    match = None
#    for i in sharpSource:
#        pCandidate = sharpsToPitch(i)
#        # create relative transpositions based on this pitch for major
#        pMinor = pCandidate.transpose(minorShift)
#
#        pDorian = pCandidate.transpose(dorianShift)
#        pPhrygian = pCandidate.transpose(phrygianShift)
#        pLydian = pCandidate.transpose(lydianShift)
#        pMixolydian = pCandidate.transpose(mixolydianShift)
#
#        if mode in [None, 'major']:
#            if pCandidate.name == p.name:
#                match = i
#                break
#        elif mode in ['dorian']:
#            if pDorian.name == p.name:
#                match = i
#                break
#        elif mode in ['phrygian']:
#            if pPhrygian.name == p.name:
#                match = i
#                break
#        elif mode in ['lydian']:
#            if pLydian.name == p.name:
#                match = i
#                break
#        elif mode in ['mixolydian']:
#            if pMixolydian.name == p.name:
#                match = i
#                break
#        elif mode in ['minor', 'aeolian']:
#        #else: # match minor pitch
#            if pMinor.name == p.name:
#                match = i
#                break
#
#    _pitchToSharpsCache[(p.name, mode)] = match
#    return match


class KeySignatureException(exceptions21.Music21Exception):
    pass
class KeyException(exceptions21.Music21Exception):
    pass

#-------------------------------------------------------------------------------




#def keyFromString(strKey):
#    '''Given a string representing a key, return the appropriate Key object. 
#    '''
#    #TODO: Write keyFromString
#    #    return None
#    #raise KeyException("keyFromString not yet written")




#-------------------------------------------------------------------------------
class KeySignature(base.Music21Object):
    '''
    A KeySignature object specifies the signature to be used for a piece; it takes
    in zero, one, or two arguments.  The first argument is an int giving the number of sharps,
    or if negative the number of flats.  The second argument (deprecated -- do not use)
    specifies the mode of the piece ('major', 'minor', or None for unknown).
    
    If you are starting with the name of a key, see the :class:`~music21.key.Key` object.

    >>> from music21 import *

    >>> A = key.KeySignature(3)
    >>> A
    <music21.key.KeySignature of 3 sharps>

    >>> Eflat = key.KeySignature(-3)
    >>> Eflat
    <music21.key.KeySignature of 3 flats>

    Some specification of mode can go into the KeySignature object:

    >>> Eflat.mode = 'phrygian'
    >>> Eflat
    <music21.key.KeySignature of 3 flats, mode phrygian>

    But if you want to get a real Key, then use the :class:`~music21.key.Key` object instead:

    >>> illegal = key.KeySignature('c#')
    Traceback (most recent call last):
    KeySignatureException: Cannot get a KeySignature from this "number" of sharps: "c#"; did you mean to use a key.Key() object instead?
    
    >>> legal = key.Key('c#')
    >>> legal.sharps
    4
    >>> legal
    <music21.key.Key of c# minor>
    '''


    # note that musicxml permits non-tradtional keys by specifying
    # one or more altered tones; these are given as pairs of 
    # step names and semiton alterations

    classSortOrder = 2
    
    def __init__(self, sharps=None, mode=None):
        base.Music21Object.__init__(self)
        # position on the circle of fifths, where 1 is one sharp, -1 is one flat

        try:
            if sharps is not None and \
                  (sharps != int(sharps)):
                raise KeySignatureException('Cannot get a KeySignature from this "number" of sharps: "%s"; ' % sharps + 
                    'did you mean to use a key.Key() object instead?')
        except ValueError:
            raise KeySignatureException('Cannot get a KeySignature from this "number" of sharps: "%s"; ' % sharps + 
                    'did you mean to use a key.Key() object instead?')
            
        self._sharps = sharps
        # optionally store mode, if known
        self._mode = mode
        # need to store a list of pitch objects, used for creating a 
        # non traditional key
        self._alteredPitches = None

        # cache altered pitches
        self._alteredPitchesCached = []

    #---------------------------------------------------------------------------
    def _attributesChanged(self):
        '''Clear the altered pitches cache
        '''
        self._alteredPitchesCached = []


    def _strDescription(self):
        output = ""
        ns = self.sharps
        if ns == None:
            output = 'None'
        elif ns > 1:
            output = "%s sharps" % str(ns)
        elif ns == 1:
            output = "1 sharp"
        elif ns == 0:
            output = "no sharps or flats"
        elif ns == -1:
            output = "1 flat"
        else:
            output = "%s flats" % str(abs(ns))
        if self.mode is None:
            return output
        else:
            output += ", mode %s" % (self.mode)
            return output
        
    def __repr__(self):
        return "<music21.key.KeySignature of %s>" % self._strDescription()

    def __str__(self):
        return self.__repr__()

    def _getPitchAndMode(self):
        '''Returns a a two value list containing 
        a :class:`music21.pitch.Pitch` object that 
        names this key and the value of :attr:`~music21.key.KeySignature.mode`.

        >>> from music21 import *
       
        >>> key.KeySignature(-7).pitchAndMode
        (<music21.pitch.Pitch C->, None)
        >>> key.KeySignature(-6).pitchAndMode
        (<music21.pitch.Pitch G->, None)
        >>> key.KeySignature(-3).pitchAndMode
        (<music21.pitch.Pitch E->, None)
        >>> key.KeySignature(0).pitchAndMode
        (<music21.pitch.Pitch C>, None)
        >>> key.KeySignature(1).pitchAndMode
        (<music21.pitch.Pitch G>, None)
        >>> csharp = key.KeySignature(4)
        >>> csharp.mode = "minor"
        >>> csharp.pitchAndMode
        (<music21.pitch.Pitch C#>, 'minor')
        >>> csharpPitch = csharp.pitchAndMode[0]
        >>> csharpPitch.accidental
        <accidental sharp>
        '''
        # this works but returns sharps
        # keyPc = (self.sharps * 7) % 12
        if self.mode is not None and self.mode.lower() == 'minor':
            pitchObj = sharpsToPitch(self.sharps + 3)
        else:
            pitchObj = sharpsToPitch(self.sharps)
        return pitchObj, self.mode

    pitchAndMode = property(_getPitchAndMode)


    def _getAlteredPitches(self):
        if self._alteredPitchesCached: # if list not empty
            #environLocal.printDebug(['using cached altered pitches'])
            return self._alteredPitchesCached

        post = []
        if self.sharps > 0:
            pKeep = pitch.Pitch('B')
            if self.sharps > 8:
                pass
            for i in range(self.sharps):
                pKeep.transpose('P5', inPlace=True)
                p = copy.deepcopy(pKeep)
                p.octave = None
                post.append(p)

        elif self.sharps < 0:
            pKeep = pitch.Pitch('F')
            for i in range(abs(self.sharps)):
                pKeep.transpose('P4', inPlace=True)
                p = copy.deepcopy(pKeep)
                p.octave = None
                post.append(p)

        # assign list to altered pitches; list will be empty if not set
        self._alteredPitchesCached = post
        return post


    alteredPitches = property(_getAlteredPitches, 
        doc='''
        Return a list of music21.pitch.Pitch objects that are altered by this 
        KeySignature. That is, all Pitch objects that will receive an accidental.  

        >>> from music21 import *

        >>> a = key.KeySignature(3)
        >>> a.alteredPitches
        [<music21.pitch.Pitch F#>, <music21.pitch.Pitch C#>, <music21.pitch.Pitch G#>]
        >>> b = key.KeySignature(1)
        >>> b.alteredPitches
        [<music21.pitch.Pitch F#>]

        >>> c = key.KeySignature(9)
        >>> [str(p) for p in c.alteredPitches]
        ['F#', 'C#', 'G#', 'D#', 'A#', 'E#', 'B#', 'F##', 'C##']

        >>> d = key.KeySignature(-3)
        >>> d.alteredPitches
        [<music21.pitch.Pitch B->, <music21.pitch.Pitch E->, <music21.pitch.Pitch A->]

        >>> e = key.KeySignature(-1)
        >>> e.alteredPitches
        [<music21.pitch.Pitch B->]

        >>> f = key.KeySignature(-6)
        >>> [str(p) for p in f.alteredPitches]
        ['B-', 'E-', 'A-', 'D-', 'G-', 'C-']

        >>> g = key.KeySignature(-8)
        >>> [str(p) for p in g.alteredPitches]
        ['B-', 'E-', 'A-', 'D-', 'G-', 'C-', 'F-', 'B--']
        ''')

    def accidentalByStep(self, step):
        '''
        Given a step (C, D, E, F, etc.) return the accidental
        for that note in this key (using the natural minor for minor)
        or None if there is none.

        >>> from music21 import *
        
        >>> g = key.KeySignature(1)
        >>> g.accidentalByStep("F")
        <accidental sharp>
        >>> g.accidentalByStep("G")

        >>> f = KeySignature(-1)
        >>> bbNote = note.Note("B-5")
        >>> f.accidentalByStep(bbNote.step)
        <accidental flat>     

        Fix a wrong note in F-major:
        
        >>> wrongBNote = note.Note("B#4")
        >>> if f.accidentalByStep(wrongBNote.step) != wrongBNote.accidental:
        ...    wrongBNote.accidental = f.accidentalByStep(wrongBNote.step)
        >>> wrongBNote
        <music21.note.Note B->

        Set all notes to the correct notes for a key using the 
        note's Key Context.  Before:              
        
        >>> from music21 import *
        >>> s1 = stream.Stream()
        >>> s1.append(key.KeySignature(4))  # E-major or C-sharp-minor
        >>> s1.append(note.HalfNote("C"))
        >>> s1.append(note.HalfNote("E-"))
        >>> s1.append(key.KeySignature(-4)) # A-flat-major or F-minor
        >>> s1.append(note.WholeNote("A"))
        >>> s1.append(note.WholeNote("F#"))
        >>> #_DOCS_SHOW s1.show()

        .. image:: images/keyAccidentalByStep_Before.*
            :width: 400
  
        After:

        >>> for n in s1.notes:
        ...    n.accidental = n.getContextByClass(key.KeySignature).accidentalByStep(n.step)
        >>> #_DOCS_SHOW s1.show()

        .. image:: images/keyAccidentalByStep.*
            :width: 400

        OMIT_FROM_DOCS
        >>> s1.show('text')
        {0.0} <music21.key.KeySignature of 4 sharps>
        {0.0} <music21.note.Note C#>
        {2.0} <music21.note.Note E>
        {4.0} <music21.key.KeySignature of 4 flats>
        {4.0} <music21.note.Note A->
        {8.0} <music21.note.Note F>
                
        Test to make sure there are not linked accidentals (fixed bug 22 Nov. 2010)
        
        >>> nB1 = note.WholeNote("B")
        >>> nB2 = note.WholeNote("B")
        >>> s1.append(nB1)
        >>> s1.append(nB2)
        >>> for n in s1.notes:
        ...    n.accidental = n.getContextByClass(key.KeySignature).accidentalByStep(n.step)
        >>> (nB1.accidental, nB2.accidental)
        (<accidental flat>, <accidental flat>)
        >>> nB1.accidental.name = 'sharp'
        >>> (nB1.accidental, nB2.accidental)
        (<accidental sharp>, <accidental flat>)
        
        '''
        # temp measure to fix dbl flats, etc.
        for thisAlteration in reversed(self.alteredPitches): 
            if thisAlteration.step.lower() == step.lower():
                return copy.deepcopy(thisAlteration.accidental) # get a new one each time otherwise we have linked accidentals, YUK!
        
        return None


    #---------------------------------------------------------------------------
    # properties
    def transpose(self, value, inPlace=False):
        '''
        Transpose the KeySignature by the user-provided value. 
        If the value is an integer, the transposition is treated 
        in half steps. If the value is a string, any Interval string 
        specification can be provided. Alternatively, a 
        :class:`music21.interval.Interval` object can be supplied.

        >>> a = KeySignature(2)
        >>> a.pitchAndMode
        (<music21.pitch.Pitch D>, None)
        >>> b = a.transpose('p5')
        >>> b.pitchAndMode
        (<music21.pitch.Pitch A>, None)
        >>> b.sharps
        3
        >>> c = b.transpose('-m2')
        >>> c.pitchAndMode
        (<music21.pitch.Pitch G#>, None)
        >>> c.sharps
        8
        
        >>> d = c.transpose('-a3')
        >>> d.pitchAndMode
        (<music21.pitch.Pitch E->, None)
        >>> d.sharps
        -3
        '''
        if hasattr(value, 'diatonic'): # its an Interval class
            intervalObj = value
        else: # try to process
            intervalObj = interval.Interval(value)

        if not inPlace:
            post = copy.deepcopy(self)
        else:
            post = self

        p1, mode = post._getPitchAndMode()
        p2 = p1.transpose(intervalObj)
        
        post.sharps = pitchToSharps(p2, mode)
        post._attributesChanged()

        # mode is already set
        if not inPlace:
            return post
        else:
            return None

    def getScale(self):
        '''
        Return a scale that is representative of this key signature
        and mode.

        >>> from music21 import *
        >>> ks = key.KeySignature(3)
        >>> ks
        <music21.key.KeySignature of 3 sharps>
        >>> ks.getScale()
        <music21.scale.MajorScale A major>
        >>> ks.mode = 'minor'
        >>> ks.getScale()
        <music21.scale.MinorScale F# minor>
        '''
        from music21 import scale
        pitchObj, mode = self._getPitchAndMode()
        if mode in [None, 'major']:
            return scale.MajorScale(pitchObj)
        elif mode in ['minor']:
            return scale.MinorScale(pitchObj)
        else:
            raise KeySignatureException('not mapping for this mode yet: %s' % mode)

    #---------------------------------------------------------------------------
    # properties


    def _getSharps(self):
        return self._sharps

    def _setSharps(self, value):
        if value != self._sharps:
            self._sharps = value
            self._attributesChanged()

    sharps = property(_getSharps, _setSharps, 
        doc = '''
        Get or set the number of sharps.  If the number is negative
        then it sets the number of flats.  Equivalent to musicxml's 'fifths'
        feature
        
        >>> from music21 import *
        >>> ks1 = key.KeySignature(2)
        >>> ks1.sharps
        2
        >>> ks1.sharps = -4
        >>> ks1
        <music21.key.KeySignature of 4 flats>
        ''')


    def _getMode(self):
        return self._mode

    def _setMode(self, value):
        if value != self._mode:
            self._mode = value
            self._attributesChanged()

    mode = property(_getMode, _setMode,
        doc = '''
        Get or set the mode.
        
        Mode is supported in a very rough manner for `KeySignature`
        objects, but for more sophisticated use of modes use the 
        :class:`~music21.key.Key` object.

        Mode may disappear in future releases so if you are counting
        on this for major or minor, consider supporting the `Key` object
        instead.
        ''')

    #---------------------------------------------------------------------------
    # override these methods for json functionality
    # not presently in use

#     def jsonAttributes(self):
#         '''Define all attributes of this object that should be JSON serialized for storage and re-instantiation. Attributes that name basic Python objects or :class:`~music21.base.JSONSerializer` subclasses, or dictionaries or lists that contain Python objects or :class:`~music21.base.JSONSerializer` subclasses, can be provided.
#         '''
#         # only string notation is stored, meaning that any non-default
#         # internal representations will not be saved
#         # a new default will be created when restored
#         return ['sharps', 'mode', '_alteredPitches']
# 
# 
#     def jsonComponentFactory(self, idStr):
#         '''Given a stored string during JSON serialization, return an object'
# 
#         The subclass that overrides this method will have access to all modules necessary to create whatever objects necessary. 
#         '''
#         return None



# some ideas
# c1 = chord.Chord(["D", "F", "A"])
# k1 = key.Key("C")
# c2 = k1.chordFromRomanNumeral("ii")
# c1 == c2
# True

# 
# key1 = Key("E", "major")
# key1
# <music21.key.Key E major>
# key1.parallel
# <music21.key.Key E minor>
# key1.relative
# <music21.key.Key c# minor>
# 
# ks1 = key1.signature
# ks1
# <music21.key.KeySignature 4 sharps>
# ks1.sharpsOrFlats
# 4
# ks1.majorKey
# <music21.key.Key E major>
# ks1.minorKey
# <music21.key.Key c# minor>
# 
# # Set this E major piece to use a signature of 1 flat
# key1.signature = KeySignature(-1)
# 
# # Check that it's still E major
# key1
# <music21.key.Key E major>
# key1.signature
# <music21.key.KeySignature 1 flat>
# key1.sharpsOrFlats
# -1
# 
# # What major key would normally have this signature?
# key1.signature.majorKey
# <music21.key.Key F major>
# 


class Key(KeySignature, scale.DiatonicScale):
    '''
    Note that a key is a sort of hypothetical/conceptual object.
    It probably has a scale (or scales) associated with it and a KeySignature,
    but not necessarily.

    >>> from music21 import *
    >>> cm = key.Key('c')  # cminor.
    >>> cm
    <music21.key.Key of c minor>
    >>> cm.sharps
    -3
    >>> cm.pitchFromDegree(3)
    <music21.pitch.Pitch E-4>
    >>> cm.pitchFromDegree(7)
    <music21.pitch.Pitch B-4>

    >>> Csharpmaj = key.Key('C#')
    >>> Csharpmaj
    <music21.key.Key of C# major>
    >>> Csharpmaj.sharps
    7

    >>> Fflatmaj = key.Key('F-')
    >>> Fflatmaj
    <music21.key.Key of F- major>
    >>> Fflatmaj.sharps
    -8
    >>> Fflatmaj.accidentalByStep('B')
    <accidental double-flat>
    '''
    _sharps = 0
    _mode = None


    def __init__(self, tonic = None, mode = None):
        if tonic is not None:
            if hasattr(tonic, 'classes') and 'Music21Object' in tonic.classes:
                if hasattr(tonic, 'name'):
                    tonic = tonic.name
                elif hasattr(tonic, 'pitches') and len(tonic.pitches) > 0: # chord
                    if mode is None:
                        if tonic.isMinorTriad() is True:
                            mode = 'minor'
                        else:
                            mode = 'major'
                    tonic = tonic.root().name
                    
            
            if mode is None:
                if 'm' in tonic:
                    mode = 'minor'
                    tonic = re.sub('m', '', tonic)
                elif 'M' in tonic:
                    mode = 'major'
                    tonic = re.sub('M', '', tonic)
                elif tonic.lower() == tonic:
                    mode = 'minor'
                else:
                    mode = 'major'
            else:
                mode = mode.lower()
            sharps = pitchToSharps(tonic, mode)
            KeySignature.__init__(self, sharps, mode)

        scale.DiatonicScale.__init__(self, tonic=tonic)

        if hasattr(tonic, 'classes') and 'Pitch' in tonic.classes:
            self.tonic = tonic
        else:
            self.tonic = pitch.Pitch(tonic)
        self.type = mode
        self.mode = mode

        # build the network for the appropriate scale
        self._abstract._buildNetwork(self.type)

        # optionally filled attributes
        # store a floating point value between 0 and 1 regarding correlation coefficent between the detected key and the algorithm for detecting the key
        self.correlationCoefficient = None

        # store an ordered list of alternative Key objects
        self.alternateInterpretations = []

    def __repr__(self):
        return "<music21.key.Key of %s>" % self.__str__()

    def __str__(self):
        # string representation needs to be complete, as is used
        # for metadata comparisons
        tonic = self.tonic
        if self.mode == 'major':
            tonic = tonic.name.upper()
        elif self.mode == 'minor':
            tonic = tonic.name.lower()
        return "%s %s" % (tonic, self.mode)



    def _tonalCertainityCorrelationCoefficient(self, *args, **keywords):
        # possible measures:
        if len(self.alternateInterpretations) == 0:
            raise KeySignatureException('cannot process amgiguity without alternative Interpretations')
        focus = []
        focus.append(self.correlationCoefficient)
        for subKey in self.alternateInterpretations:
            cc = subKey.correlationCoefficient
            if cc > 0:
                focus.append(cc)
#         print focus
#         print

        # take abs magnitude as one factor; assume between 0 and 1
        # greater certainty often has a larger number
        absMagnitude = focus[0] 

        # take distance from first to second; greater certainty
        # seems to have a greater span
        leaderSpan = focus[0] - focus[1]

        # take average of all non-negative values
        meanMagnitude = sum(focus) / float(len(focus))

        # standard deviation of all non-neg values
        standardDeviation = common.standardDeviation(focus, bassel=False)

        environLocal.printDebug(['absMagnitude', absMagnitude, 'leaderSpan', leaderSpan, 'meanMagnitude', meanMagnitude, 'standardDeviation', standardDeviation])

        # combine factors with a weighting for each 
        # estimate range as 2, normalize between zero and 1
        return (absMagnitude * 1) + (leaderSpan * 2)

    def tonalCertainty(self, method='correlationCoefficient', *args, 
        **keywords):
        '''Provide a measure of tonal ambiguity for Key determined with one of many methods. 

        The `correlationCoefficient` assumes that the alternateInterpretations list has been filled from the use of a KeyWeightKeyAnalysis subclass.
        '''
        if method == 'correlationCoefficient':
            return self._tonalCertainityCorrelationCoefficient(
                    args, keywords)





#-------------------------------------------------------------------------------
class Test(unittest.TestCase):

    def runTest(self):
        pass

    def testCopyAndDeepcopy(self):
        '''Test copying all objects defined in this module
        '''
        import sys, types, copy
        for part in sys.modules[self.__module__].__dict__.keys():
            match = False
            for skip in ['_', '__', 'Test', 'Exception']:
                if part.startswith(skip) or part.endswith(skip):
                    match = True
            if match:
                continue
            name = getattr(sys.modules[self.__module__], part)
            if callable(name) and not isinstance(name, types.FunctionType):
                try: # see if obj can be made w/ args
                    obj = name()
                except TypeError:
                    continue
                a = copy.copy(obj)
                b = copy.deepcopy(obj)


    def testBasic(self):
        a = KeySignature()
        self.assertEqual(a.sharps, None)

    def testTonalAmbiguityA(self):
        from music21 import corpus, stream, key, scale
#         s = corpus.parse('bwv64.2')
#         k = s.analyze('KrumhanslSchmuckler')
#         k.tonalCertainty(method='correlationCoefficient')
# 
        s = corpus.parse('bwv66.6')
        k = s.analyze('KrumhanslSchmuckler')
        ta = k.tonalCertainty(method='correlationCoefficient')
        self.assertEqual(ta < 2 and ta > 0.1, True)

        s = corpus.parse('schoenberg/opus19', 6)
        k = s.analyze('KrumhanslSchmuckler')
        ta = k.tonalCertainty(method='correlationCoefficient')
        self.assertEqual(ta < 2 and ta > 0.1, True)



        sc1 = scale.MajorScale('g')
        sc2 = scale.MajorScale('d')
        sc3 = scale.MajorScale('a')
        sc5 = scale.MajorScale('f#')

        s = stream.Stream()
        [s.append(note.Note(p)) for p in sc1.pitches]
        k = s.analyze('KrumhanslSchmuckler')
        ta = k.tonalCertainty(method='correlationCoefficient')
        self.assertEqual(ta < 2 and ta > 0.1, True)

        s = stream.Stream()
        [s.append(note.Note(p)) for p in sc1.pitches + sc2.pitches + sc2.pitches + sc3.pitches]
        k = s.analyze('KrumhanslSchmuckler')
        ta = k.tonalCertainty(method='correlationCoefficient')
        self.assertEqual(ta < 2 and ta > 0.1, True)

        s = stream.Stream()
        [s.append(note.Note(p)) for p in sc1.pitches + sc5.pitches]
        k = s.analyze('KrumhanslSchmuckler')
        ta = k.tonalCertainty(method='correlationCoefficient')
        self.assertEqual(ta < 2 and ta > 0.1, True)


        s = stream.Stream()
        [s.append(note.Note(p)) for p in ['c', 'g', 'c', 'c', 'e']]
        k = s.analyze('KrumhanslSchmuckler')
        ta = k.tonalCertainty(method='correlationCoefficient')
        self.assertEqual(ta < 2 and ta > 0.1, True)



#         s = corpus.parse('bwv66.2')
#         k = s.analyze('KrumhanslSchmuckler')
#         k.tonalCertainty(method='correlationCoefficient')
        #s = corpus.parse('bwv48.3')




#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [KeySignature, Key]


if __name__ == "__main__":
    import music21
    music21.mainTest(Test)





#------------------------------------------------------------------------------
# eof

