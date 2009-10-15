#!/usr/bin/env python2.5

from mutagen.id3 import ID3, ID3NoHeaderError, TALB, TPE1, TPE2, TBPM, COMM, TCMP, TCOM, TPE3, TDRC, TPOS, TCON, TSRC, TEXT, TPUB, TIT2, TRCK, UFID, TXXX, TSOP, TSO2, APIC
from mutagen.flac import FLAC
import string
import sys
import os.path
from subprocess import Popen, PIPE

mp3_flac_dict = {
    'TALB': (u'$ALBUM', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TALB(encoding=3, text=str)]),
    'TPE1': (u'$ARTIST', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TPE1(encoding=3, text=str)]),
    'TPE2': (u'$BAND', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TPE2(encoding=3, text=str)]),
    'TBPM': (u'$BPM', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TBPM(encoding=3, text=str)]),
    'COMM': (u'$COMMENT', lambda mp3, flac: mp3.text[0] == flac, lambda str: [COMM(encoding=3, text=str)]),
    'TCMP': (u'$COMPILATION', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TCMP(encoding=3, text=str)]),
    'TCOM': (u'$COMPOSER', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TCOM(encoding=3, text=str)]),
    'TPE3': (u'$CONDUCTOR', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TPE3(encoding=3, text=str)]),
    'TDRC': (u'$DATE', lambda mp3, flac: mp3.text[0].text == flac, lambda str: [TDRC(encoding=3, text=str)]),
    'TPOS': (u'$DISCNUMBER/$TOTALDISCS', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TPOS(encoding=3, text=str)]),
    'TCON': (u'$GENRE', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TCON(encoding=3, text=str)]),
    'TSRC': (u'$ISRC', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TSRC(encoding=3, text=str)]),
    'TEXT': (u'$LYRICIST', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TEXT(encoding=3, text=str)]),
    'TPUB': (u'$PUBLISHER', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TPUB(encoding=3, text=str)]),
    'TIT2': (u'$TITLE', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TIT2(encoding=3, text=str)]),
    'TRCK': (u'$TRACKNUMBER/$TOTALTRACKS', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TRCK(encoding=3, text=str)]),
    'TSOP': (u'$ARTISTSORT', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TSOP(encoding=3, text=str)]),
    'TSO2': (u'$ALBUMARTISTSORT', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TSO2(encoding=3, text=str)]),
    'TSOT': (u'$TITLESORT', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TSOT(encoding=3, text=str)]),
    'TSOA': (u'$ALBUMSORT', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TSOT(encoding=3, text=str)]),
    'UFID:http://musicbrainz.org':      (u'$MUSICBRAINZ_TRACKID', lambda mp3, flac: mp3.data == flac, lambda str: [UFID(encoding=3, owner=u'http://musicbrainz.org', data=str)]),
    'TXXX:MusicBrainz Album Id':        (u'$MUSICBRAINZ_ALBUMID', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TXXX(encoding=3, desc=u'MusicBrainz Album Id', text=str)]),
    'TXXX:MusicBrainz Album Status':    (u'$MUSICBRAINZ_ALBUMSTATUS', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TXXX(encoding=3, desc=u'MusicBrainz Album Status', text=str)]),
    'TXXX:MusicBrainz Album Artist Id': (u'$MUSICBRAINZ_ALBUMARTISTID', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TXXX(encoding=3, desc=u'MusicBrainz Album Artist Id', text=str)]),
    'TXXX:MusicBrainz Album Type':      (u'$MUSICBRAINZ_ALBUMTYPE', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TXXX(encoding=3, desc=u'MusicBrainz Album Type', text=str)]),
    'TXXX:MusicBrainz Artist Id':       (u'$MUSICBRAINZ_ARTISTID', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TXXX(encoding=3, desc=u'MusicBrainz Artist Id', text=str)]),
    'TXXX:MusicBrainz Sortname':        (u'$MUSICBRAINZ_SORTNAME', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TXXX(encoding=3, desc=u'MusicBrainz Sortname', text=str)]),
    'TXXX:MusicBrainz TRM Id': 	        (u'$MUSICBRAINZ_TRMID', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TXXX(encoding=3, desc=u'MusicBrainz TRM Id', text=str)]),
    'TXXX:MD5': 		                (u'$MD5', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TXXX(encoding=3, desc=u'MD5', text=str)]),
    'TXXX:ALBUMARTISTSORT':             (u'$ALBUMARTISTSORT', lambda mp3, flac: mp3.text[0] == flac, lambda str: [TXXX(encoding=3, desc=u'ALBUMARTISTSORT', text=str)]),
}

def flac_tag_dict(flac):
	ret = {}
	for key in flac.tags.as_dict().keys():
		ret[key.upper()] = flac.tags[key][0]
	ret['MD5'] = ('%x' % flac.info.md5_signature)
	if not ret.has_key('TOTALTRACKS'):
	    ret['TOTALTRACKS'] = ''
	if not ret.has_key('TOTALDISCS'):
	    ret['TOTALDISCS'] = ''
	return ret

def encode_file(flac_name, mp3_name):
    # We need to pass --tl (or any tag option) to ensure Mutagen can read the file afterwards.
    flac = Popen(["flac", "--decode", "--silent", "--stdout", flac_name], stdout=PIPE)
    lame = Popen(["lame", "--vbr-new", "-V2", "--quiet", "--noreplaygain", "--tl", "placeholder", "-", mp3_name], stdin=flac.stdout)
    lame.communicate()
    lame.wait()
    flac.wait()

def maybe_encode_file(flac_name, mp3_name):
    if os.path.isfile(mp3_name):
        # Need to check md5 to make sure they're the same:
        flac = FLAC(flac_name)
        mp3 = ID3(mp3_name)
        try:
            if (len(mp3.getall('TXXX:MD5')) == 0) or ('%x' % flac.info.md5_signature) != mp3['TXXX:MD5'].text[0]:
                try:
                    mp3_sig = mp3['TXXX:MD5'].text[0]
                except KeyError:
                    mp3_sig = 'None'
                print "Need to re-encode %s: flac:%x vs mp3:%s" % (mp3_name, flac.info.md5_signature, mp3_sig)
                encode_file(flac_name, mp3_name)
        except ID3NoHeaderError:
            print "Need to re-encode %s (invalid ID3 tag)!" % mp3_name
            encode_file(flac_name, mp3_name)
    else:
        print "Encoding %s" % mp3_name
        encode_file(flac_name, mp3_name)
    tag_sync(flac_name, mp3_name)

def tag_sync(flac_name, mp3_name):
    mp3 = ID3(mp3_name)
    flac = FLAC(flac_name)

    flactags = flac_tag_dict(flac)
    tag_differences = {}

    # First, check whether the tags that can easily be translated match:
    for frame in mp3_flac_dict.keys():
        mp3_has_frame = True
        flac_has_frame = True
        frames_differ = False
        mp3_value = None
        flac_value = None

        format, comparator, id3_generator = mp3_flac_dict[frame]

        try:
            mp3_value = mp3[frame]
        except KeyError:
            mp3_has_frame = False

        try:
            flac_value = string.Template(format).substitute(flactags)
        except KeyError:
            flac_has_frame = False
		
        if flac_has_frame and mp3_has_frame:
            frames_differ = not comparator(mp3_value, flac_value)

        if (flac_has_frame and not mp3_has_frame) or frames_differ:
            # print "%s differs: %s <> %s" % (frame, mp3_value, flac_value)
            tag_differences[frame] = id3_generator(flac_value)
        elif not flac_has_frame and mp3_has_frame:
            tag_differences[frame] = None

    # Now, check pictures:
    for picture in flac.pictures:
        have_picture = False
        
        for apic in mp3.getall('APIC'):
            if apic.mime == picture.mime and apic.type == picture.type and apic.data == picture.data:
                have_picture = True
        if not have_picture:
            if not tag_differences.has_key('APIC:'):
                tag_differences['APIC:'] = []
            tag_differences['APIC:'].append(APIC(encoding=3, desc=u'', type=picture.type, data=picture.data, mime=picture.mime))

    # And now push the changed tags to the MP3.
    for frame in tag_differences.keys():    
        if tag_differences[frame] == None:
            mp3.delall(frame)
        else:
    		mp3.setall(frame, tag_differences[frame])

    if len(tag_differences.keys()) > 0:
        print "Updating tags in %s: %s" % (mp3_name, tag_differences.keys())
        mp3.save(mp3_name, v1=1)

maybe_encode_file(sys.argv[1], sys.argv[2])