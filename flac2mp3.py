#!/usr/bin/env python2.5

from mutagen.id3 import ID3, ID3NoHeaderError, TALB, TPE1, TPE2, TBPM, COMM, TCMP, TCOM, TPE3, TDRC, TPOS, TCON, TSRC, TEXT, TPUB, TIT2, TRCK, UFID, TXXX, TSOP, TSO2, APIC, TSOT, TSOA
from mutagen.flac import FLAC
import string
import sys
import os.path
from subprocess import Popen, PIPE

def one_to_one_conversion(flac_frame_name, frame_class):
    return (flac_frame_name, lambda mp3, flac: mp3.text[0] == flac, lambda str:[frame_class(encoding=3, text=str)])

def one_to_one_conversion_txxx(flac_frame_name, desc):
    return (flac_frame_name, lambda mp3, flac: mp3.text[0] == flac, lambda str:[TXXX(encoding=3, desc=desc, text=str)])

mp3_flac_dict = {
    'TDRC':                             (u'$DATE', lambda mp3, flac: mp3.text[0].text == flac, lambda str: [TDRC(encoding=3, text=str)]),
    'UFID:http://musicbrainz.org':      (u'$MUSICBRAINZ_TRACKID', lambda mp3, flac: mp3.data == flac, lambda str: [UFID(encoding=3, owner=u'http://musicbrainz.org', data=str)]),
    'TALB':                             one_to_one_conversion(u'$ALBUM', TALB),
    'TPE1':                             one_to_one_conversion(u'$ARTIST', TPE1),
    'TPE2':                             one_to_one_conversion(u'$BAND', TPE2),
    'TBPM':                             one_to_one_conversion(u'$BPM', TBPM),
    'COMM':                             one_to_one_conversion(u'$COMMENT', COMM),
    'TCMP':                             one_to_one_conversion(u'$COMPILATION', TCMP),
    'TCOM':                             one_to_one_conversion(u'$COMPOSER', TCOM),
    'TPE3':                             one_to_one_conversion(u'$CONDUCTOR', TPE3),
    'TPOS':                             one_to_one_conversion(u'$DISCNUMBER/$TOTALDISCS', TPOS),
    'TCON':                             one_to_one_conversion(u'$GENRE', TCON),
    'TSRC':                             one_to_one_conversion(u'$ISRC', TSRC),
    'TEXT':                             one_to_one_conversion(u'$LYRICIST', TEXT),
    'TPUB':                             one_to_one_conversion(u'$PUBLISHER', TPUB),
    'TIT2':                             one_to_one_conversion(u'$TITLE', TIT2),
    'TRCK':                             one_to_one_conversion(u'$TRACKNUMBER/$TOTALTRACKS', TRCK),
    'TSOP':                             one_to_one_conversion(u'$ARTISTSORT', TSOP),
    'TSO2':                             one_to_one_conversion(u'$ALBUMARTISTSORT', TSO2),
    'TSOT':                             one_to_one_conversion(u'$TITLESORT', TSOT),
    'TSOA':                             one_to_one_conversion(u'$ALBUMSORT', TSOA),
    'TXXX:MusicBrainz Album Id':        one_to_one_conversion_txxx(u'$MUSICBRAINZ_ALBUMID', 'MusicBrainz Album Id'),
    'TXXX:MusicBrainz Album Status':    one_to_one_conversion_txxx(u'$MUSICBRAINZ_ALBUMSTATUS', 'MusicBrainz Album Status'),
    'TXXX:MusicBrainz Album Artist Id': one_to_one_conversion_txxx(u'$MUSICBRAINZ_ALBUMARTISTID', 'MusicBrainz Album Artist Id'),
    'TXXX:MusicBrainz Album Type':      one_to_one_conversion_txxx(u'$MUSICBRAINZ_ALBUMTYPE', 'MusicBrainz Album Type'),
    'TXXX:MusicBrainz Artist Id':       one_to_one_conversion_txxx(u'$MUSICBRAINZ_ARTISTID', 'MusicBrainz Artist Id'),
    'TXXX:MusicBrainz Sortname':        one_to_one_conversion_txxx(u'$MUSICBRAINZ_SORTNAME', 'MusicBrainz Sortname'),
    'TXXX:MusicBrainz TRM Id': 	        one_to_one_conversion_txxx(u'$MUSICBRAINZ_TRMID', 'MusicBrainz TRM Id'),
    'TXXX:MD5': 		                one_to_one_conversion_txxx(u'$MD5', 'MD5'),
    'TXXX:ALBUMARTISTSORT':             one_to_one_conversion_txxx(u'$ALBUMARTISTSORT', 'ALBUMARTISTSORT'),
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