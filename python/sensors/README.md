### Nvidia based camera sync and output
Basic streaming to the screen
```
gst-launch-1.0 nvarguscamerasrc sensor-id=0 silent=false ! "video/x-raw(memory:NVMM), width=(int)1920, height=(int)1080, format=(string)NV12, framerate=(fraction)30/1" ! nvvidconv flip-method=2 ! "video/x-raw,width=1920,height=1080"  ! nveglglessink sync=false
```

Dual camera to two frames side by side:
```
gst-launch-1.0 nvcompositor name=comp \
sink_0::xpos=0 sink_0::ypos=0 sink_0::width=1920 sink_0::height=1080 \
sink_1::xpos=1920 sink_1::ypos=0 sink_1::width=1920 sink_1::height=1080 ! \
'video/x-raw(memory:NVMM),format=RGBA' ! nv3dsink \
nvarguscamerasrc sensor_id=0 ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! nvvidconv flip-method=0 ! 'video/x-raw(memory:NVMM),width=1920, height=1080, format=RGBA' ! comp.sink_0 \
nvarguscamerasrc sensor_id=1 ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! nvvidconv flip-method=0 ! 'video/x-raw(memory:NVMM),width=1920, height=1080, format=RGBA' ! comp.sink_1
```

Dual camera to video:
```
gst-launch-1.0 \
nvarguscamerasrc sensor_id=0 ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! nvvidconv flip-method=0 ! 'video/x-raw(memory:NVMM),width=1920, height=1080, format=RGBA' ! comp.sink_0 \
nvarguscamerasrc sensor_id=1 ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! nvvidconv flip-method=0 ! 'video/x-raw(memory:NVMM),width=1920, height=1080, format=RGBA' ! comp.sink_1 \
nvcompositor name=comp \
sink_0::xpos=0 sink_0::ypos=0 sink_0::width=1920 sink_0::height=1080 \
sink_1::xpos=1920 sink_1::ypos=0 sink_1::width=1920 sink_1::height=1080 ! \
'video/x-raw(memory:NVMM),format=RGBA' ! nvvidconv ! 'video/x-raw(memory:NVMM),format=(string)NV12' ! nvv4l2h265enc control-rate=0 preset-level=2 maxperf-enable=true profile=1 ! h265parse ! splitmuxsink location=capture-%05d.mkv max-size-bytes=2000000000 muxer=matroskamux -e
```

Dual camera to video with trimming. It is very important not to scale video after trimming via nvvidconv. This bug is documented [here](https://forums.developer.nvidia.com/t/nvcompositor-positioning-frames-failure/259274/4): \
1080p:
```
gst-launch-1.0 nvcompositor name=comp sink_0::xpos=0 sink_0::ypos=0 sink_0::width=960 sink_0::height=1080 sink_1::xpos=960 sink_1::ypos=0 sink_1::width=960 sink_1::height=1080 ! 'video/x-raw(memory:NVMM),format=RGBA' ! nvvidconv ! 'video/x-raw(memory:NVMM),format=(string)NV12' ! nvv4l2h265enc control-rate=0 preset-level=2 maxperf-enable=true profile=1 ! h265parse ! splitmuxsink location=/home/dmitrii/Videos/capture-%05d.mkv max-size-bytes=2000000000 muxer=matroskamux -e nvarguscamerasrc sensor-id=0 ! 'video/x-raw(memory:NVMM), width=1920, height=1080, format=(string)NV12, framerate=(fraction)30/1' ! nvvidconv flip-method=0 top=0 bottom=1080 left=480 right=1440 ! 'video/x-raw(memory:NVMM),format=RGBA' ! comp.sink_0 nvarguscamerasrc sensor-id=1 ! 'video/x-raw(memory:NVMM), width=1920, height=1080, format=(string)NV12, framerate=(fraction)30/1' ! nvvidconv flip-method=0 top=0 bottom=1080 left=480 right=1440 ! 'video/x-raw(memory:NVMM),format=RGBA' ! comp.sink_1
```

1440p:
```
gst-launch-1.0 nvcompositor name=comp sink_0::xpos=0 sink_0::ypos=0 sink_0::width=1280 sink_0::height=1440 sink_1::xpos=1280 sink_1::ypos=0 sink_1::width=1280 sink_1::height=1440 ! 'video/x-raw(memory:NVMM),format=RGBA' ! nvvidconv ! 'video/x-raw(memory:NVMM),format=(string)NV12' ! nvv4l2h265enc control-rate=0 preset-level=2 maxperf-enable=true profile=1 ! h265parse ! splitmuxsink location=/home/dmitrii/Videos/capture-%05d.mkv max-size-bytes=2000000000 muxer=matroskamux -e nvarguscamerasrc sensor-id=0 ! 'video/x-raw(memory:NVMM), width=(int)3264, height=(int)1848, format=(string)NV12, framerate=(fraction)28/1' ! nvvidconv flip-method=0 top=204 bottom=1644 left=992 right=2272 ! 'video/x-raw(memory:NVMM),format=RGBA' ! comp.sink_0 nvarguscamerasrc sensor-id=1 ! 'video/x-raw(memory:NVMM), width=3264, height=1848, format=(string)NV12, framerate=(fraction)28/1' ! nvvidconv flip-method=0 top=204 bottom=1644 left=992 right=2272 ! 'video/x-raw(memory:NVMM),format=RGBA' ! comp.sink_1
```

Sample SHMSink write and SHMSrc read:
`/dev/shm` is used because it resides in RAM via tmpfs ramdisk (allowed since kernel 2.6) while /tmp is on the storage itself.
```
gst-launch-1.0 videotestsrc ! x264enc ! shmsink socket-path=/dev/shm/foo sync=true wait-for-connection=false shm-size=10000000
gst-launch-1.0 shmsrc socket-path=/dev/shm/foo ! h264parse ! avdec_h264 ! videoconvert ! ximagesink
```

Write single camera to shmsink:
```
gst-launch-1.0 nvarguscamerasrc sensor-id=0 silent=false ! 'video/x-raw(memory:NVMM), width=(int)1920, height=(int)1080, format=(string)NV12, framerate=(fraction)30/1' ! nvvidconv ! 'video/x-raw,width=1920,height=1080,format=BGRx' ! videoconvert ! 'video/x-raw,width=1920,height=1080,format=BGR' ! shmsink socket-path=/dev/shm/foo sync=false wait-for-connection=false shm-size=20000000
```

Write dual camera to shmsink:
```
gst-launch-1.0 \
nvcompositor name=comp \
sink_0::xpos=0 sink_0::ypos=0 sink_0::width=1920 sink_0::height=1080 \
sink_1::xpos=1920 sink_1::ypos=0 sink_1::width=1920 sink_1::height=1080 ! \
'video/x-raw(memory:NVMM),format=RGBA' ! nvvidconv ! 'video/x-raw,format=BGRx' ! videoconvert ! 'video/x-raw,format=BGR' ! shmsink socket-path=/dev/shm/foo sync=false wait-for-connection=false shm-size=200000000 \
nvarguscamerasrc sensor_id=0 ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! nvvidconv flip-method=0 ! 'video/x-raw(memory:NVMM),width=1920, height=1080, format=RGBA' ! comp.sink_0 \
nvarguscamerasrc sensor_id=1 ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! nvvidconv flip-method=0 ! 'video/x-raw(memory:NVMM),width=1920, height=1080, format=RGBA' ! comp.sink_1
```

Write dual camera to nv3dsink 
```
gst-launch-1.0 \
nvcompositor name=comp \
sink_0::xpos=0 sink_0::ypos=0 sink_0::width=1920 sink_0::height=1080 \
sink_1::xpos=1920 sink_1::ypos=0 sink_1::width=1920 sink_1::height=1080 ! \
'video/x-raw(memory:NVMM),format=RGBA' ! nvvidconv ! 'video/x-raw,format=BGRx' ! videoconvert ! 'video/x-raw,format=BGR' ! nv3dsink \
nvarguscamerasrc sensor_id=0 ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! nvvidconv flip-method=0 ! 'video/x-raw(memory:NVMM),width=1920, height=1080, format=RGBA' ! comp.sink_0 \
nvarguscamerasrc sensor_id=1 ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! nvvidconv flip-method=0 ! 'video/x-raw(memory:NVMM),width=1920, height=1080, format=RGBA' ! comp.sink_1
```

Write dual camera to appsink:
```
gst-launch-1.0 \
nvcompositor name=comp \
sink_0::xpos=0 sink_0::ypos=0 sink_0::width=1920 sink_0::height=1080 \
sink_1::xpos=1920 sink_1::ypos=0 sink_1::width=1920 sink_1::height=1080 ! \
'video/x-raw(memory:NVMM),format=RGBA' ! nvvidconv ! 'video/x-raw,format=BGRx' ! videoconvert ! 'video/x-raw,format=BGR' ! appsink max-buffers=1 drop=true  \
nvarguscamerasrc sensor_id=0 ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! nvvidconv flip-method=0 ! 'video/x-raw(memory:NVMM),width=1920, height=1080, format=RGBA' ! comp.sink_0 \
nvarguscamerasrc sensor_id=1 ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! nvvidconv flip-method=0 ! 'video/x-raw(memory:NVMM),width=1920, height=1080, format=RGBA' ! comp.sink_1
```

Crop single camera:
```
gst-launch-1.0 nvarguscamerasrc sensor-id=0 silent=false ! "video/x-raw(memory:NVMM), width=(int)1920, height=(int)1080, format=(string)NV12, framerate=(fraction)30/1" ! nvvidconv flip-method=0 top=0 bottom=1080 left=480 right=1440 ! "video/x-raw,width=960,height=1080"  ! nveglglessink sync=false
```

Write dual camera with crop to nv3dsink: \
1080p:
```
gst-launch-1.0 \
nvcompositor name=comp \
sink_0::xpos=0 sink_0::ypos=0 sink_0::width=960 sink_0::height=1080 \
sink_1::xpos=960 sink_1::ypos=0 sink_1::width=960 sink_1::height=1080 ! \
'video/x-raw(memory:NVMM),format=RGBA' ! nvvidconv ! 'video/x-raw,format=BGRx' ! videoconvert ! 'video/x-raw,format=BGR' ! nv3dsink \
nvarguscamerasrc sensor_id=0 silent=false ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! nvvidconv flip-method=0 top=0 bottom=1080 left=480 right=1440 ! 'video/x-raw(memory:NVMM),width=960,height=1080, format=RGBA' ! comp.sink_0 \
nvarguscamerasrc sensor_id=1 silent=false ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! nvvidconv flip-method=0 top=0 bottom=1080 left=480 right=1440 ! 'video/x-raw(memory:NVMM),width=960,height=1080, format=RGBA' ! comp.sink_1
```

1440p:
```
gst-launch-1.0 \
nvcompositor name=comp \
sink_0::xpos=0 sink_0::ypos=0 sink_0::width=1280 sink_0::height=1440 \
sink_1::xpos=1280 sink_1::ypos=0 sink_1::width=1280 sink_1::height=1440 ! \
'video/x-raw(memory:NVMM),format=RGBA' ! nvvidconv ! 'video/x-raw,format=BGRx' ! videoconvert ! 'video/x-raw,format=BGR' ! nveglglessink sync=false \
nvarguscamerasrc sensor-id=0 silent=false ! 'video/x-raw(memory:NVMM), width=(int)3264, height=(int)1848, format=(string)NV12, framerate=(fraction)28/1' ! nvvidconv top=204 bottom=1644 left=992 right=2272 ! 'video/x-raw(memory:NVMM),width=1280,height=1440, format=RGBA' ! comp.sink_0 \
nvarguscamerasrc sensor-id=1 silent=false ! 'video/x-raw(memory:NVMM), width=(int)3264, height=(int)1848, format=(string)NV12, framerate=(fraction)28/1' ! nvvidconv top=204 bottom=1644 left=992 right=2272 ! 'video/x-raw(memory:NVMM),width=1280,height=1440, format=RGBA' ! comp.sink_1
```

Write dual camera with crop to shmsink. VideoCapture will have a bug when doing this. \
1080p:
```
gst-launch-1.0 \
nvcompositor name=comp \
sink_0::xpos=0 sink_0::ypos=0 sink_0::width=960 sink_0::height=1080 \
sink_1::xpos=960 sink_1::ypos=0 sink_1::width=960 sink_1::height=1080 ! \
'video/x-raw(memory:NVMM),format=RGBA' ! nvvidconv ! 'video/x-raw,format=BGRx' ! videoconvert ! 'video/x-raw,format=BGR' ! shmsink socket-path=/dev/shm/capture sync=false wait-for-connection=false shm-size=200000000 \
nvarguscamerasrc sensor_id=0 silent=false ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! nvvidconv flip-method=0 top=0 bottom=1080 left=480 right=1440 ! 'video/x-raw(memory:NVMM),width=960,height=1080, format=RGBA' ! comp.sink_0 \
nvarguscamerasrc sensor_id=1 silent=false ! 'video/x-raw(memory:NVMM),width=1920,height=1080,framerate=30/1' ! nvvidconv flip-method=0 top=0 bottom=1080 left=480 right=1440 ! 'video/x-raw(memory:NVMM),width=960,height=1080, format=RGBA' ! comp.sink_1
```

1440p:
```
gst-launch-1.0 \
nvcompositor name=comp \
sink_0::xpos=0 sink_0::ypos=0 sink_0::width=1280 sink_0::height=1440 \
sink_1::xpos=1280 sink_1::ypos=0 sink_1::width=1280 sink_1::height=1440 ! \
'video/x-raw(memory:NVMM),format=RGBA' ! nvvidconv ! 'video/x-raw,format=BGRx' ! videoconvert ! 'video/x-raw,format=BGR' ! shmsink socket-path=/dev/shm/capture sync=false wait-for-connection=false shm-size=200000000 \
nvarguscamerasrc sensor-id=0 silent=false ! 'video/x-raw(memory:NVMM), width=(int)3264, height=(int)1848, format=(string)NV12, framerate=(fraction)28/1' ! nvvidconv top=204 bottom=1644 left=992 right=2272 ! 'video/x-raw(memory:NVMM),width=1280,height=1440, format=RGBA' ! comp.sink_0 \
nvarguscamerasrc sensor-id=1 silent=false ! 'video/x-raw(memory:NVMM), width=(int)3264, height=(int)1848, format=(string)NV12, framerate=(fraction)28/1' ! nvvidconv top=204 bottom=1644 left=992 right=2272 ! 'video/x-raw(memory:NVMM),width=1280,height=1440, format=RGBA' ! comp.sink_1
```


Scan for windows:
```
wmctrl -lp
```

Get window ID and pass it to the gst:
```
gst-launch-1.0 ximagesrc xid=0x03200002 ! videoconvert ! x264enc ! shmsink socket-path=/dev/shm/foo sync=true wait-for-connection=false shm-size=10000000

gst-launch-1.0 shmsrc socket-path=/dev/shm/foo ! h264parse ! avdec_h264 ! videoconvert ! ximagesink
```
