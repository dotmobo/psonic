# -*- coding: utf-8 -*-

import libsonic
import os
from vlc import vlc
import yaml
import sys
import threading

"""
Psonic - a python subsonic client

"""

def mspf():
    """Milliseconds per frame."""
    return int(1000 // (player.get_fps() or 25))

def print_info():
    """Print information about the media"""
    try:
        media = player.get_media()
        print('State: %s' % player.get_state())
        print('Media: %s' % vlc.bytes_to_str(media.get_mrl()))
        print('Track: %s/%s' % (player.video_get_track(), player.video_get_track_count()))
        print('Current time: %s/%s' % (player.get_time(), media.get_duration()))
        print('Position: %s' % player.get_position())
        print('FPS: %s (%d ms)' % (player.get_fps(), mspf()))
        print('Rate: %s' % player.get_rate())
        print('Video size: %s' % str(player.video_get_size(0)))
        print('Scale: %s' % player.video_get_scale())
        print('Aspect ratio: %s' % player.video_get_aspect_ratio())
    except Exception:
        print('Error: %s' % sys.exc_info()[1])

def sec_forward():
    """Go forward one sec"""
    player.set_time(player.get_time() + 1000)

def sec_backward():
    """Go backward one sec"""
    player.set_time(player.get_time() - 1000)

def frame_forward():
    """Go forward one frame"""
    player.set_time(player.get_time() + mspf())

def frame_backward():
    """Go backward one frame"""
    player.set_time(player.get_time() - mspf())

def print_help():
    """Print help"""
    print('Single-character commands:')
    for k, m in sorted(keybindings.items()):
        m = (m.__doc__ or m.__name__).splitlines()[0]
        print('  %s: %s.' % (k, m.rstrip('.')))

def quit_app():
    """Stop and exit"""
    global player
	# release media
    player.release()
	#stop thread
    global stop_thread
    stop_thread = True;
    sys.exit(0)

def toggle_echo_position():
    """Toggle echoing of media position"""
    global echo_position
    echo_position = not echo_position

try:
	from msvcrt import getch
except ImportError:
	import termios
	import tty

	def getch():  # getchar(), getc(stdin)  #PYCHOK flake
		fd = sys.stdin.fileno()
		old = termios.tcgetattr(fd)
		try:
			tty.setraw(fd)
			ch = sys.stdin.read(1)
		finally:
			termios.tcsetattr(fd, termios.TCSADRAIN, old)
		return ch


def end_callback(event):
	global change_song
	change_song = True

def pos_callback(event, player):
    global echo_position
    if echo_position:
        sys.stdout.write('\r%s to %.2f%% (%.2f%%)' % (event.type,event.u.new_position * 100, player.get_position() * 100))
        sys.stdout.flush()


def playRandomSong():
    "Change song"
    global conn
    global vlc_instance
    global player

    # get a random song
    song = conn.getRandomSongs(size=1)

    # get song info
    song_id = song['randomSongs']['song']['id']
    song_artist = song['randomSongs']['song']['artist']
    song_album = song['randomSongs']['song']['album']
    song_title = song['randomSongs']['song']['title']
    # print the song on the terminal
    print("%s - %s : %s" % (song_artist, song_album,song_title))
	
	# get the stream url
    audio_file="%s:%s/%s/stream.view?u=%s&p=%s&id=%s&v=%s&c=py-sonic" % \
		(config['serverurl'], config['serverport'], config['serverpath'], config['username'],config['password'], song_id, config['apiversion'])
	
	# set the media
    media = vlc_instance.media_new(audio_file, '--loop', '--http-caching=500')
    player.set_media(media)
		
	#play the song
    player.play()

def check_change_song():
    global change_song
    global stop_thread
    while True and not stop_thread:
        if change_song:
            change_song = False
            playRandomSong()

def main():
    """
    Method to play a random song
    """

    #Connection
    global conn
    conn = libsonic.Connection(\
            config['serverurl'], \
            config['username'], \
            config['password'], \
            serverPath=config['serverpath'], \
            port=config['serverport']\
    )

    # if connection ok
    if conn.ping:
        # create player and vlc instance
        global player
        global vlc_instance
        vlc_instance = vlc.Instance()
        player = vlc_instance.media_player_new()
        
        #event
        event_manager = player.event_manager()
        event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, end_callback)
        event_manager.event_attach(vlc.EventType.MediaPlayerPositionChanged, pos_callback, player)


        global keybindings
        keybindings = {
            ' ': player.pause,
            '+': sec_forward,
            '-': sec_backward,
            '.': frame_forward,
            ',': frame_backward,
            'i': print_info,
            'p': toggle_echo_position,
            'q': quit_app,
            '?': print_help,
            'n': playRandomSong,
        }

        #play random song
        playRandomSong()

        print('Press q to quit, ? to get help.%s' % os.linesep)
		
		# Thread to check change song
        ccsthread = threading.Thread(None, check_change_song, None)
        ccsthread.start()
		
		# Loop for key bindings
        while True:
            k = getch()
            if type(k) is bytes:
                k = k.decode("utf-8")
            print('> %s' % k)
            if k in keybindings:
                keybindings[k]()
            elif k.isdigit():
                 # jump to fraction of the movie.
                player.set_position(float('0.'+k))
    

if __name__ == "__main__":
    print("Start ...")
    # variables
    config = yaml.load(open('config.yaml', 'r'))
    echo_position = False
    player = None
    keybindings = {}
    conn = None
    vlc_instance = None
    change_song = False
    stop_thread = False
    # launch main
    main()










