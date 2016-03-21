import sys
import os

PHONE_APP_DOWNLOAD_URL = 'https://raw.githubusercontent.com/GoWarrior/CloudQSupport/master/GoWarriorCameraDemoClient.apk'
PHOTO_DIRECTORY = os.path.join(sys.path[0], 'photo')
CONFIGURE_FILE = 'config.inf'
PIPE_TOPIC = 'IPCam'
TIMER_INTERVAL = 60.0
ir_sensor_pin = 66
GPIO_HIGH = 1
GPIO_LOW = 0
Snapshot_Auto = 1
Snapshot_Active = 2
Snapshot_IRsensor = 3
Snapshot_Remote = 4
Snapshot_FaceDetect = 5
Snapshot_UploadStart = 6
Snapshot_UploadDone = 7
Snapshot_RemoteControl = 8

String_Snapshot = "Take Snapshot"
String_DownloadPhoto = "Download Photo"
String_AutoRun_Enable = "Enable Auto Run"
String_AutoRun_Disable = "Disable Auto Run"
String_AutoSnapshot_Enable = "Enable Auto Snapshot"
String_AutoSnapshot_Disable = "Disable Auto Snapshot"
String_FaceDetect_Enable = "Enable face Detection"
String_FaceDetect_Disable = "Disable face Detection"
String_UploadPhoto_Enable = "Enable Photo Upload"
String_UploadPhoto_Disable = "Disable Photo Upload"
String_APP_Download_Addr = "Download Phone App"
