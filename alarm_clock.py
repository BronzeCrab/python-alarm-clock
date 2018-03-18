import gst
import gobject
import threading
import logging
from datetime import datetime
from daemonize import Daemonize
import argparse
import sys
import os
import signal

PID = "/tmp/test.pid"
# logger's settings
log_file = "/tmp/test.log"
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.propagate = False
fh = logging.FileHandler(log_file, "a")
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)
keep_fds = [fh.stream.fileno()]

# what time to play
time_weekdays = "8:30"
time_weekend = "10:00"

# paths to songs
basic_path = '/home/austinnikov/Downloads/'
song_array = (basic_path+'test.mp3', basic_path+'test2.mp3')


class AlarmClock():

    def __init__(self, musiclist):
        self.musiclist = musiclist
        self.song_num = 0
        self.construct_pipeline()
        self.set_property_file()

    def construct_pipeline(self):
        self.player = gst.element_factory_make("playbin")
        self.is_playing = False
        self.connect_signals()

    def connect_signals(self):
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.message_handler)

    def play(self):
        self.is_playing = True
        self.player.set_state(gst.STATE_PLAYING)

    def handle_error(self, message):
        logger.debug(message)

    def set_property_file(self):
        self.player.set_property(
            "uri",
            "file://"+self.musiclist[self.song_num])

    def stop(self):
        self.player.set_state(gst.STATE_NULL)
        self.is_playing = False
        logger.debug("player stopped")

    def message_handler(self, bus, message):
        msg_type = message.type
        if msg_type == gst.MESSAGE_ERROR:
            self.handle_error(message)
        elif msg_type == gst.MESSAGE_EOS:
            logger.debug("End Of Song")
            if self.song_num < len(self.musiclist)-1:
                self.song_num += 1
                self.stop()
                self.set_property_file()
                self.play()
            else:
                self.stop()
                self.song_num = 0
                self.set_property_file()


class GobInit(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        gobject.threads_init()
        self.loop = gobject.MainLoop()
        self.loop.run()


def main():
    logger.debug("start")
    gob = GobInit()
    gob.start()
    player = AlarmClock(song_array)
    logger.debug("player created")

    hour_weekdays = int(time_weekdays.split(':')[0])
    minute_weekdays = int(time_weekdays.split(':')[1])

    hour_weekend = int(time_weekend.split(':')[0])
    minute_weekend = int(time_weekend.split(':')[1])

    while True:
        now = datetime.now()
        if any((
                now.weekday() in (5, 6) and
                (hour_weekend == now.hour and minute_weekend == now.minute),
                now.weekday() not in (5, 6) and
                (hour_weekdays == now.hour and minute_weekdays == now.minute)
        )):
            player.play()


def kill(pid_f, logger):
    if os.path.isfile(pid_f):
        with open(pid_f) as pid_file:
            pid = pid_file.read()
            try:
                os.kill(int(pid), signal.SIGKILL)
            except (OSError, ValueError) as e:
                logger.debug(
                    'Process is not killed due to: {0}'.format(e))
            else:
                logger.debug('Stopped')
                os.remove(pid_f)
    else:
        logger.debug(
            'There is no pid_file, nothing to kill')


parser = argparse.ArgumentParser()
mutually_exclusive_group = parser.add_mutually_exclusive_group(
        required=True)

mutually_exclusive_group.add_argument(
    "-start", action="store_true")
mutually_exclusive_group.add_argument(
    "-stop", action="store_true")
mutually_exclusive_group.add_argument(
    "-status", action="store_true")
args = vars(parser.parse_args())

if args.get('stop'):
    kill(PID, logger)
    sys.exit()

elif args.get('status'):
    try:
        with open(PID) as pid_file:
            pid = pid_file.read()
        os.kill(int(pid), 0)
    except Exception as e:
        logger.debug("Process is stopped")
    else:
        logger.debug("Process is running")
    sys.exit()

# kill in order not to start several processes
kill(PID, logger)

daemon = Daemonize(app="test_app", pid=PID, action=main, keep_fds=keep_fds)
daemon.start()
