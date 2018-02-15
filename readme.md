#### What is it:
This is python and gstreamer based alarm clock for debian-based systems. It uses `daemonize` lib to
behave like a daemon.

#### How to install:
`pip install -r requirements` in order to install `daemonize` library.

Next install gstreamer python bindings:

`apt-get install python-gst0.10 gstreamer0.10-plugins-good gstreamer0.10-plugins-ugly`

#### How to start and control:

Next u can do:

`python alarm_clock.py -start`  

 to start

`python alarm_clock.py -status`  

to get status (it will be displayed in log). By default log is `/tmp/test.log`. U can change
log folder just by editing `log_file` variable.

`python alarm_clock.py -stop`  

 to stop it.

##### What time to play
Also you can specify what time to play track, just edit `time_weekdays` and `time_weekend` vars.
##### Specify tracks to play
You can specidy and change tracks, just edit `basic_path` and `song_array` vars. And set as many tracks  
as you wish.
