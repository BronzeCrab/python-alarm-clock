import gst
import gobject
import threading
import logging
import time
from datetime import datetime, timedelta
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
time_weekend = "9:00"

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
        logger.debug("player set to play")

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


def get_delta(datetime_obj, str_date, time_weekdays, time_weekend,
              current_datetime_obj=None):
    """Function to detemine diff between to datetime objects"""

    if datetime_obj.weekday() not in (5, 6):
        datetime_play = datetime.strptime(
            str_date + " " + time_weekdays,  "%d/%m/%Y %H:%M")
    else:
        datetime_play = datetime.strptime(
            str_date + " " + time_weekend,  "%d/%m/%Y %H:%M")
    if current_datetime_obj:
        delta = datetime_play - current_datetime_obj
    else:
        delta = datetime_play - datetime_obj
    return delta


def sleep_till_next_play(
        current_datetime, time_weekdays, time_weekend, logger):
    next_datetime = current_datetime + timedelta(days=1)
    next_str_date = next_datetime.strftime('%d/%m/%Y')
    delta = get_delta(
        next_datetime, next_str_date, time_weekdays, time_weekend,
        current_datetime)
    sleep_sec = delta.total_seconds()
    logger.debug("sleep till next start for {0} sec".format(sleep_sec))
    time.sleep(sleep_sec)


def main():
    logger.debug("start")
    gob = GobInit()
    gob.start()
    player = AlarmClock(song_array)
    logger.debug("player created")

    current_datetime = datetime.now()
    current_str_date = current_datetime.strftime('%d/%m/%Y')
    delta = get_delta(
        current_datetime, current_str_date, time_weekdays, time_weekend)
    # time for play is gone, sleep till next time:
    if delta.total_seconds() < 0:
        sleep_till_next_play(
            current_datetime, time_weekdays, time_weekend, logger)
    # sleep till time to play:
    else:
        sleep_sec = delta.total_seconds()
        logger.debug("sleep till start for {0} sec".format(sleep_sec))
        time.sleep(sleep_sec)

    while True:
        player.play()
        sleep_till_next_play(
            datetime.now(), time_weekdays, time_weekend, logger)


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
