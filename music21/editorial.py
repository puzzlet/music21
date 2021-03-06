# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:         editorial.py
# Purpose:      music21 classes for representing notes
#
# Authors:      Michael Scott Cuthbert
#               Christopher Ariza
#
# Copyright:    Copyright © 2008-2012 Michael Scott Cuthbert and the music21 Project
# License:      LGPL
#-------------------------------------------------------------------------------

'''Editorial objects store comments and other meta-data associated with specific :class:`~music21.note.Note` objects or other music21 objects. 
'''

from __future__ import unicode_literals

import doctest, unittest
from music21 import exceptions21
from music21 import base

class EditorialException(exceptions21.Music21Exception):
    pass

class CommentException(exceptions21.Music21Exception):
    pass

def getObjectsWithEditorial(listToSearch, editorialStringToFind, 
    listOfValues=None):
    '''
    provided a list of objects (typically note objects) to search through, this method returns
    only those objects that have the editorial attribute defined by the editorialStringToFind.
    An optional parameter, listOfValues, is a list of all the possible values the given
    object's editorialString can have.
    
    the editorialStringToFind can be any of the pre-defined editorial attributes (such as "ficta" or "harmonicIntervals")
    but it may also be the dictionary key of editorial notes stored in the miscellaneous (misc) dictionary.
    For example, "isPassingTone" or "isNeighborTone"
    
    >>> from music21 import *
    >>> n1 = note.Note()
    >>> n1.editorial.misc['isPassingTone'] = True
    >>> n2 = note.Note()
    >>> n2.editorial.comment = 'consider revising'
    >>> s = stream.Stream()
    >>> s.repeatAppend(n1, 5)
    >>> s.repeatAppend(note.Note(), 2)
    >>> s.repeatAppend(n2, 3)
    >>> listofNotes = s.getElementsByClass(note.Note)
    >>> listOfValues = ['consider revising', 'remove']
    >>> listofNotesWithEditorialisPassingTone = editorial.getObjectsWithEditorial(listofNotes, "isPassingTone")
    >>> listofNotesWithEditorialComment = editorial.getObjectsWithEditorial(listofNotes, "comment", listOfValues)
    >>> print len(listofNotesWithEditorialisPassingTone)
    5
    >>> print len(listofNotesWithEditorialComment)
    3
    '''
    listofOBJToReturn = []
    for obj in listToSearch:
        try:
            try:
                editorialContents = getattr(obj.editorial, editorialStringToFind)
            except:
                editorialContents = obj.editorial.misc[editorialStringToFind]
            
            if listOfValues != None:
                if editorialContents in listOfValues:
                    listofOBJToReturn.append(obj)
            else:
                listofOBJToReturn.append(obj)
        except:
            pass
    return listofOBJToReturn
    
class NoteEditorial(base.JSONSerializer):
    '''Editorial comments and special effects that can be applied to notes
    Standard ones are stored as attributes.  Non-standard/one-off effects are
    stored in the dict called "misc":
    
    >>> from music21 import *
    >>> a = editorial.NoteEditorial()
    >>> a.color = "blue"  # a standard editorial effect
    >>> a.misc['backgroundHighlight'] = 'yellow'  # non-standard.

    
    Every GeneralNote object already has a NoteEditorial object
    attached to it at object.editorial.  Normally you will just change that
    object instead.  
    
    For instance, take the case where a scribe 
    wrote F in the score, knowing that a good singer would automatically
    sing F-sharp instead.  We can store the editorial
    suggestion to sing F-sharp as a "musica ficta" accidental object:
    
    
    >>> fictaSharp = pitch.Accidental("Sharp")
    >>> n = note.Note("F")
    >>> n.editorial.ficta = fictaSharp
    >>> assert(n.editorial.ficta.alter == 1.0) #_DOCS_HIDE
    >>> #_DOCS_SHOW n.show('lily.png')  # only Lilypond currently supports musica ficta
    
    
    .. image:: images/noteEditorialFictaSharp.*
        :width: 103
    
    '''

    _DOC_ATTR = {
    'color': 'the color of the note (x11 colors and extended x11colors are allowed), only displays properly in lilypond',
    'comment': 'a reference to a :class:`~music21.editorial.Comment` object',
    'ficta': 'a :class:`~music21.pitch.Accidental` object that specifies musica ficta for the note.  Will only be displayed in LilyPond and then only if there is no Accidental object on the note itself',
    'hidden': 'boolean value about whether to hide the note or not (only works in lilypond)',
    'harmonicInterval': 'an :class:`~music21.interval.Interval` object that specifies the harmonic interval between this note and a single other note (useful for storing information post analysis',
    'harmonicIntervals': 'a list for when you want to store more than one harmonicInterval',
    'melodicInterval': 'an :class:`~music21.interval.Interval` object that specifies the melodic interval to the next note in this part/voice/stream, etc.',
    'melodicIntervals': 'a list for storing more than one melodic interval',
    'melodicIntervalOverRests': 'same as melodicInterval but ignoring rests; MIGHT BE REMOVED SOON',
    'melodicIntervalsOverRests': 'same thing but a list',
    'misc': 'A dict to hold anything you might like to store.',
    }
    
    def __init__(self):
        base.JSONSerializer.__init__(self)

        self.ficta = None  # Accidental object -- N.B. for PRINTING only not for determining intervals
        self.color = None
        self.misc  = {}
        self.harmonicInterval = None
        self.harmonicIntervals = []
        self.hidden = False
        self.melodicInterval = None
        self.melodicIntervals = []
        self.melodicIntervalOverRests = None
        self.melodicIntervalsOverRests = []
        self.comment = Comment()

    def jsonAttributes(self):
        '''Define all attributes of this object that should be JSON serialized for storage and re-instantiation.
        '''
        # add to base class
        return ['color', 'misc', 'comment']

    def lilyStart(self):
        r'''
        A method that returns a string containing the 
        lilypond output that comes before the note.
        
        >>> from music21 import *
        >>> n = note.Note()
        >>> n.editorial.lilyStart()   
        u''
        >>> n.editorial.ficta = pitch.Accidental("Sharp")
        >>> n.editorial.color = "blue"
        >>> n.editorial.hidden = True
        >>> print n.editorial.lilyStart()
        \ficta \color "blue" \hideNotes
        
        '''
        baseRet = ""
        if self.ficta is not None:
            baseRet += self.fictaLilyStart()
        if self.color:
            baseRet += self.colorLilyStart()
        if self.hidden is True:
            baseRet += r"\hideNotes "
            
        return baseRet

    def fictaLilyStart(self):
        r''' 
        returns \ficta -- called out so it is more easily subclassed
        '''
        return r"\ficta "

    def colorLilyStart(self):
        r'''
        returns \color "theColorName" -- called out so it is more easily subclassed
        '''
        return r'\color "' + self.color + '" '

    def lilyAttached(self):
        r'''returns any information that should be attached under the note,
        currently just returns self.comment.lily or "" '''
        
        if self.comment and self.comment.text:
            return unicode(self.comment.lily)
        else:
            return ''
    
    def lilyEnd(self):
        r'''
        returns a string of editorial lily
        instructions to come after the note.  Currently it is
        just info to turn off hidding of notes.
        '''
        
        baseRet = u""
        
        if self.hidden is True:
            baseRet += u"\\unHideNotes "
        
        return baseRet

        
class Comment(base.JSONSerializer):
    '''
    an object that adds text above or below a note:
    
    >>> from music21 import *
    >>> n = note.Note()
    >>> n.editorial.comment.text = "hello"
    >>> n.editorial.comment.position = "above"
    >>> n.editorial.comment.lily
    u'^"hello"'
    
    '''
    def __init__(self):
        base.JSONSerializer.__init__(self)
        self.position = "below"
        self.text = None
    
    def _getLily(self):
        if self.text is None:
            return ""
        if self.position == 'below':
            return '_"' + self.text + '"'
        elif self.position == 'above':
            return '^"' + self.text + '"'
        else:
            raise CommentException("Cannot deal with position: " + self.position)
        
    lily = property(_getLily)


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
        a = Comment()
        self.assertEqual(a.position, 'below')





#-------------------------------------------------------------------------------
# define presented order in documentation
_DOC_ORDER = [NoteEditorial]


if __name__ == "__main__":
    #import doctest
    #doctest.testmod()
    import music21
    music21.mainTest(Test)



#------------------------------------------------------------------------------
# eof

