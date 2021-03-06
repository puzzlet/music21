.. _usersGuide_06_chords:

User's Guide, Chapter 6: Chords
=============================================================

Note and Chord objects, as both subclasses of the :class:`~music21.note.GeneralNote` object, share many features. Both contain a Duration object. A Note has only one Pitch; a Chord, however, contains a list one or more Pitch objects accessed via the :attr:`~music21.chord.Chord.pitches` property. The Chord object additional has numerous analytic methods (such as :meth:`~music21.chord.Chord.isDiminishedSeventh`) as well as a variety of post-tonal tools (such as :attr:`~music21.chord.Chord.forteClass`; see :ref:`overviewPostTonal`).

A Chord can be created with a list of Pitch objects or strings identical to those used for creating Pitches. Additional, pitch class integers can be provided. 

>>> from music21 import *
>>> c1 = chord.Chord(['a#3', 'g4', 'f#5'])
>>> c1.pitches
[A#3, G4, F#5]

Like with a Note, Duration object properties can be configured from properties on Chord. For example, the Quarter Length of the Chord can be accessed from the :attr:`~music21.chord.Chord.quarterLength` property. (Note that, to get expected results in Python 2.x, one of the values in division must be a floating point value.) The :meth:`~music21.base.Music21Object.show` method can be used to display the results.

>>> c1.quarterLength = 1 + 1/3.0
>>> c1.show()   # doctest: +SKIP

.. image:: images/usersGuide/overviewNotes-05.*
    :width: 600
    

A Chord, like a Note and Pitch, can be transposed by an interval specified in any format permitted by the :class:`~music21.interval.Interval` object. The :meth:`~music21.chord.Chord.transpose` method returns a new Chord instance. 

>>> c2 = c1.transpose('m2')
>>> c2.show()   # doctest: +SKIP

.. image:: images/usersGuide/overviewNotes-06.*
    :width: 600


Finally, a Chord, like a Note, can have one or more lyrics. The :meth:`~music21.note.GeneralNote.addLyric` method functions the same as it does for Note. In the following example, a text annotation of the Forte set class name is added to the Chord.


>>> c2.addLyric(c2.forteClass)
>>> c2.show()     # doctest: +SKIP
 
.. image:: images/usersGuide/overviewNotes-07.*
    :width: 600
