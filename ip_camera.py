#!/usr/bin/python
import sys
import os
import threading
import Queue
import time
import cv2
import qrcode
from PIL import Image, ImageTk
if sys.version_info[0] < 3:
    import Tkinter as tk
else:
    import tkinter as tk
import ttk

from CloudqWS import CloudqWs
from CloudqPipe import CloudqPipe
from PWM import door_component
import RPi.GPIO as gpio
import Constant

url_root = None
WebStorage = None
Pipe = None
msg_queue = None
snapshot_timer = None
IR_timer = None
ir_sensor_value = Constant.GPIO_LOW
last_face_num = 0
door_occupied = False
g_mutex = None
transfer_dict = {}#item as {transfer_idx: [transfer_type, file_name, transfer_state, transfered_size, total_size, progressbar_id]}

#config
auto_run_enable = False
auto_snapshot_enable = False
face_detect_enable = False
photo_upload_enable = False
    
def ip_camera():
    global root
    global g_mutex
    g_mutex = threading.Lock()
    #init UI
    root = tk.Tk()
    root.resizable(False, False)
    root.geometry('%sx%s+%s+%s' %(360, 510, 670, 50))#resize window
    root.title('IP Camera')
    root.protocol("WM_DELETE_WINDOW", close_app)
    #we don't use canvas to show camera video, because it need 80 micro seconds to display picture for 1 time
#     video_frame = tk.LabelFrame(root, text = 'Captured Video')
#     video_frame.grid(column = 0, row = 0, columnspan = 1, rowspan = 2, padx = 5, pady = 5,
#                      ipadx = 5, ipady = 5)
#     canvas = tk.Canvas(video_frame, width = 640, height = 480)
#     canvas.grid(column = 0, row = 0)
    
    global progress_frame
    progress_frame = tk.LabelFrame(root, width = 345, height = 350, text = 'Transfer status')
    progress_frame.grid(column = 0, row = 0, columnspan = 1, rowspan = 1, padx = 5, pady = 5,
                     ipadx = 2, ipady = 2)
    progress_frame.grid_propagate(False)
    
    button_frame = tk.LabelFrame(root, width = 345, height = 130)
    button_frame.grid(column = 0, row = 1, columnspan = 1, rowspan = 1, padx = 5, pady = 5,
                     ipadx = 2, ipady = 2)
    button_frame.grid_propagate(False)
    
    button_snapshot = tk.Button(button_frame,text = Constant.String_Snapshot, command = take_snapshot)
    button_snapshot.grid(column = 0, row = 0, padx = 2, pady = 2, sticky = 'NESW')
    button_download = tk.Button(button_frame,text = Constant.String_DownloadPhoto, height = 1, command = download_all)
    button_download.grid(column = 1, row = 0, padx = 2, pady = 2, sticky = 'NESW')
    
    global auto_run_enable
    global auto_snapshot_enable
    global face_detect_enable
    global photo_upload_enable
    auto_run_enable, auto_snapshot_enable, face_detect_enable, photo_upload_enable = read_configuration()
    
    global button_auto_run
    button_auto_run = tk.Button(button_frame, command = enable_auto_run)
    if auto_run_enable:
        button_auto_run.config(text = Constant.String_AutoRun_Disable)
    else:
        button_auto_run.config(text = Constant.String_AutoRun_Enable)
    button_auto_run.grid(column = 0, row = 1, padx = 2, pady = 2, sticky = 'NESW')
    
    global button_auto_snapshot
    global snapshot_timer
    button_auto_snapshot = tk.Button(button_frame, command = enable_auto_snapshot)
    if auto_snapshot_enable:
        button_auto_snapshot.config(text = Constant.String_AutoSnapshot_Disable)
        snapshot_timer = threading.Timer(Constant.TIMER_INTERVAL, snapshot_auto)
        snapshot_timer.start()
    else:
        button_auto_snapshot.config(text = Constant.String_AutoSnapshot_Enable)
    button_auto_snapshot.grid(column = 1, row = 1, padx = 2, pady = 2, sticky = 'NESW')
    
    global button_face_detect
    button_face_detect = tk.Button(button_frame, command = enable_face_detect)
    if face_detect_enable:
        button_face_detect.config(text = Constant.String_FaceDetect_Disable)
    else:
        button_face_detect.config(text = Constant.String_FaceDetect_Enable)
    button_face_detect.grid(column = 0, row = 2, padx = 2, pady = 2, sticky = 'NESW')
    
    global button_auto_upload
    button_auto_upload = tk.Button(button_frame, command = enable_photo_upload)
    if photo_upload_enable:
        button_auto_upload.config(text = Constant.String_UploadPhoto_Disable)
    else:
        button_auto_upload.config(text = Constant.String_UploadPhoto_Enable)
    button_auto_upload.grid(column = 1, row = 2, padx = 2, pady = 2, sticky = 'NESW')
    
    button_phone_app = tk.Button(button_frame, text = Constant.String_APP_Download_Addr, command = dispaly_phone_app_url)
    button_phone_app.grid(column = 0, row = 3, columnspan = 2, padx = 2, pady = 2, sticky = 'NESW')
    
    global out_put
    camera = cv2.VideoCapture(0)
    out_put = videoFrame_thread(camera)
    out_put.setDaemon(True)
    
#     root.after(1000, update_progress)
    global msg_queue
    msg_queue = Queue.Queue(20)
    msg_thread = workThread(msg_queue, 0.5)
    msg_thread.setDaemon(True)#thread will be killed when main thread is over
    msg_thread.start()
    global WebStorage
    WebStorage = CloudqWs()
    WebStorage.open(file_transfer_notify)
    global Pipe
    Pipe = CloudqPipe(pipe_on_connect, pipe_on_disconnect, pipe_on_publish, pipe_on_message)
    Pipe.open()
    Pipe.connect()
    global door_handle
    door_handle = door_component(10)
    
    gpio.setmode(gpio.BCM)
    gpio.setup(Constant.ir_sensor_pin, gpio.IN)
    global IR_timer
    IR_timer = threading.Timer(0.5, check_IR_Sensor)
    IR_timer.setDaemon(True)
    IR_timer.start()
    
    out_put.start()
    root.after(0, update_progress)
    
    tk.mainloop()
    WebStorage.close()
    del WebStorage
    Pipe.disconnect()
    Pipe.close()
    del Pipe
    
    camera.release
    del camera
    
def close_app():
    global root
    global out_put
    print "End by user"
    out_put.stop()
    root.destroy()
    
def pipe_on_connect(pipe,para):
    if para == "S:done":
        pipe.subscribe(Constant.PIPE_TOPIC)
    print "on_connect: %r" % para
    
def pipe_on_disconnect(pipe,para):
    if para == "S:done":
        isDisconnected = True
    print "on_disconnect: %r" % para

def pipe_on_publish(pipe,para,token):
    print "on_publish: %r,token:%s" % (para,token)

def pipe_on_message(pipe,msg):
    global msg_queue
    print "on_message: %r" % msg
    if msg_queue is None:
        print "Message queue not init"
        return
    msg_str = str(msg)
    if msg_str == "photo":
        msg_queue.put([Constant.Snapshot_Remote, "Remote"])
    elif msg_str == "alarm":
        msg_queue.put([Constant.Snapshot_RemoteControl, ""])
    else:
        print "ERROR: can't deal with this remote msg %s" %msg_str
    
    
def upload_file(file_path):
    global transfer_dict
    global g_mutex
    obj = os.path.basename(file_path)
    idx = WebStorage.upload_file(file_path)
    if idx > 0:
        with g_mutex:
            for key in transfer_dict.keys():
                transfer_dict[key][5] += 1
    #         transfer_dict[idx]=["UPLOAD", obj, "STARTED", 0, os.path.getsize(file_path), 0]#make sure the progress bar at top of list
            transfer_dict.update({idx:["UPLOAD", obj, "STARTED", 0, os.path.getsize(file_path), 0]})
        
        _, row_num = progress_frame.grid_size()
        if row_num < 14:
            progress_bar = ttk.Progressbar(progress_frame, orient = tk.HORIZONTAL, length = 140, mode = 'determinate')
            progress_bar.grid(column = 1, row = row_num, columnspan = 1, padx = 2, pady = 2, sticky = 'NESW')
            label = tk.Label(progress_frame, text = "<-" + obj, width = 24, height = 1, anchor = tk.W)
            label.grid(column = 0, row = row_num, columnspan = 1, padx = 2, pady = 2, sticky = 'NESW')
    
def download_file(file_name, dest_file_with_path):
    global transfer_dict
    global g_mutex
    file_size = WebStorage.get_file_size(file_name)
    idx = WebStorage.download_file(file_name, dest_file_with_path)
    if idx > 0:
        with g_mutex:
            for key in transfer_dict.keys():
                transfer_dict[key][5] += 1
    #         transfer_dict[idx]=["DOWNLOAD", file_name, "STARTED", 0, file_size, 0]#make sure the progress bar at top of list
            transfer_dict.update({idx:["DOWNLOAD", file_name, "STARTED", 0, file_size, 0]})
        
        _, row_num = progress_frame.grid_size()
        if row_num < 14:
            progress_bar = ttk.Progressbar(progress_frame, orient = tk.HORIZONTAL, length = 140, mode = 'determinate')
            progress_bar.grid(column = 1, row = row_num, columnspan = 1, padx = 2, pady = 2, sticky = 'NESW')
            label = tk.Label(progress_frame, text = "->" + file_name, width = 24, height = 1, anchor = tk.W)
            label.grid(column = 0, row = row_num, columnspan = 1, padx = 2, pady = 2, sticky = 'NESW')
    else:
        print "File not exist in WS!"

def file_transfer_notify(idx,ttype,obj,tstate,tsize,size):
    global transfer_dict
    print "Py App get notify: %r %r %r %r %r %r" %(idx,ttype,obj,tstate,tsize,size)
    if transfer_dict.has_key(idx):
        if size > 0:# tsize and size maybe ZERO sometime, so need an Exception
            progress_bar_id = transfer_dict[idx][5]
            transfer_dict[idx] = [ttype, obj, tstate, tsize, size, progress_bar_id]
            print "Upload key = %d, value = %s" %(idx, transfer_dict[idx])
        elif 'COMPLETED' == tstate:
            transfer_dict[idx][2] = tstate
            transfer_dict[idx][3] = transfer_dict[idx][4]
    else:
        print "No Exist!"

def update_progress():
    global progress_frame
    global transfer_dict
    global g_mutex
    
    with g_mutex:
        for key in transfer_dict.iterkeys():
            if transfer_dict[key][5] < 14:
                label_list = progress_frame.grid_slaves(transfer_dict[key][5], 0)
                if len(label_list) > 0:
                    label = label_list[0]
                    if transfer_dict[key][0] == "DOWNLOAD":
                        label["text"] = "->" + transfer_dict[key][1]
                    else:
                        label["text"] = "<-" + transfer_dict[key][1]
                pb_list = progress_frame.grid_slaves(transfer_dict[key][5], 1)
                if len(pb_list) > 0:
                    pb = pb_list[0]
                    cur_percent = 100*transfer_dict[key][3]/transfer_dict[key][4]
                    if cur_percent < 100:
                        pb.config(value = cur_percent)
                    elif pb.cget("value") != 100:
                        pb.config(value = 100)
                        if "UPLOAD" == transfer_dict[key][0] and msg_queue is not None:
                            msg_queue.put([Constant.Snapshot_UploadDone, transfer_dict[key][1]])
                        
    global root
    root.after(33, update_progress)

def take_snapshot():
    global msg_queue
    if msg_queue is not None:
        msg_queue.put([Constant.Snapshot_Active, "Active"])
    else:
        print "Message queue not init"

def download_all():
    obj_list = WebStorage.list_file()
    if os.path.exists(Constant.PHOTO_DIRECTORY) is False:
        os.mkdir(Constant.PHOTO_DIRECTORY)
    if obj_list:
        for obj in obj_list:
            file_with_path = os.path.join(Constant.PHOTO_DIRECTORY, obj)
            if os.path.isfile(file_with_path) is False:
                download_file(obj, file_with_path)
    
def enable_auto_run():
    global auto_run_enable
    global auto_snapshot_enable
    global face_detect_enable
    global photo_upload_enable
    
    global button_auto_run
    if auto_run_enable:
        auto_run_enable = False
        button_auto_run.config(text = Constant.String_AutoRun_Enable)
    else:
        auto_run_enable = True
        button_auto_run.config(text = Constant.String_AutoRun_Disable)
    save_configuration(auto_run_enable, auto_snapshot_enable, face_detect_enable, photo_upload_enable)
    
def enable_auto_snapshot():
    global auto_run_enable
    global auto_snapshot_enable
    global face_detect_enable
    global photo_upload_enable
    
    global snapshot_timer
    
    global button_auto_snapshot
    if auto_snapshot_enable:
        auto_snapshot_enable = False
        if snapshot_timer is not None:
            snapshot_timer.cancel()
        else:
            print "Timer is None"
        button_auto_snapshot.config(text = Constant.String_AutoSnapshot_Enable)
    else:
        auto_snapshot_enable = True
        snapshot_timer = threading.Timer(Constant.TIMER_INTERVAL, snapshot_auto)
        snapshot_timer.start()
        button_auto_snapshot.config(text = Constant.String_AutoSnapshot_Disable)
    save_configuration(auto_run_enable, auto_snapshot_enable, face_detect_enable, photo_upload_enable)
    
def enable_face_detect():
    global auto_run_enable
    global auto_snapshot_enable
    global face_detect_enable
    global photo_upload_enable
    
    global button_face_detect
    if face_detect_enable:
        face_detect_enable = False
        button_face_detect.config(text = Constant.String_FaceDetect_Enable)
    else:
        face_detect_enable = True
        button_face_detect.config(text = Constant.String_FaceDetect_Disable)
    save_configuration(auto_run_enable, auto_snapshot_enable, face_detect_enable, photo_upload_enable)
    
def enable_photo_upload():
    global auto_run_enable
    global auto_snapshot_enable
    global face_detect_enable
    global photo_upload_enable
    
    global button_auto_upload
    if photo_upload_enable:
        photo_upload_enable = False
        button_auto_upload.config(text = Constant.String_UploadPhoto_Enable)
    else:
        photo_upload_enable = True
        button_auto_upload.config(text = Constant.String_UploadPhoto_Disable)
    save_configuration(auto_run_enable, auto_snapshot_enable, face_detect_enable, photo_upload_enable)
    
def dispaly_phone_app_url():
    global url_root
    if url_root is not None:
        url_root.deiconify()
        return
    url_root = tk.Toplevel()
    url_root.wm_attributes('-topmost', 1)
    url_root.resizable(False, False)
    url_root.protocol("WM_DELETE_WINDOW", hide_app_url)
    
    QR_code = qrcode.QRCode(version = 1, error_correction = qrcode.constants.ERROR_CORRECT_L, box_size = 10, border = 4)
    QR_code.add_data(Constant.PHONE_APP_DOWNLOAD_URL)
    QR_code.make(fit = True)
    url_image = QR_code.make_image().convert('RGBA')
    url_rgb = ImageTk.PhotoImage(url_image)
    
    url_root.geometry('%sx%s+%s+%s' %(url_rgb.width() + 40, url_rgb.height() + 40, 
                                      root.winfo_x() + (root.winfo_width() - url_rgb.width() -40)/2, 
                                      root.winfo_y() + (root.winfo_height()- url_rgb.height() - 40)/2))
    url_root.title('Download Phone App')
    
    url_frame = tk.LabelFrame(url_root, text = 'Phone App URL')
    url_frame.pack()

    url_canvas = tk.Canvas(url_frame, width = url_rgb.width(), height = url_rgb.height())
    url_canvas.pack()
    url_canvas.create_image(0, 0, image = url_rgb, anchor = tk.NW)
    url_root.update()
    tk.mainloop()
#     url_root = None

def hide_app_url():
    global url_root
    url_root.iconify()
#     url_root = None
    
def snapshot_auto():
    global msg_queue
    global snapshot_timer
    if msg_queue is not None:
        msg_queue.put([Constant.Snapshot_Auto, "Auto"])
    else:
        print "Message queue not init"
    snapshot_timer = threading.Timer(Constant.TIMER_INTERVAL, snapshot_auto)
    snapshot_timer.start()
    
def check_IR_Sensor():
    global ir_sensor_value
    value = gpio.input(Constant.ir_sensor_pin)
    if value != ir_sensor_value:
        if Constant.GPIO_HIGH == value:
            if msg_queue is not None:
                msg_queue.put([Constant.Snapshot_IRsensor, "PIR"])
            else:
                print "Message queue not init"
        ir_sensor_value = value
    
    global IR_timer
    IR_timer = threading.Timer(0.5, check_IR_Sensor)
    IR_timer.setDaemon(True)
    IR_timer.start()
    
def read_configuration():
    config_file = os.path.join(sys.path[0], Constant.CONFIGURE_FILE)
    if os.path.isfile(config_file):#read saved configure
        file_handle = open(config_file, "r")
        lines = file_handle.readlines()
        for line in lines:
            key = line.split('=')
            print "Key:%s, Value:%d"%(key[0],float(key[1]))
            if 'Auto_Run' == key[0]:
                auto_run_value = float(key[1]) and True or False
            elif 'Auto_Snapshot' == key[0]:
                auto_snapshot_value = float(key[1]) and True or False
            elif 'Face_Detect' == key[0]:
                face_detect_value = float(key[1]) and True or False
            elif 'Photo_Upload' == key[0]:
                photo_upload_value = float(key[1]) and True or False
            else:
                print "Unsupport configure"
        file_handle.close()
    else:#init the config file
        sequence_of_strings = ["Auto_Run=0\n", "Auto_Snapshot=0\n", "Face_Detect=0\n", "Photo_Upload=0"]
        init_file = open(config_file, "w")
        init_file.writelines(sequence_of_strings)
        init_file.close()
        auto_run_value = auto_snapshot_value = face_detect_value = photo_upload_value = False
    return auto_run_value, auto_snapshot_value, face_detect_value, photo_upload_value

def save_configuration(auto_run_value, auto_snapshot_value, face_detect_value, photo_upload_value):
    config_file = os.path.join(sys.path[0], Constant.CONFIGURE_FILE)
    write_strings = "Auto_Run=%d\nAuto_Snapshot=%d\nFace_Detect=%d\nPhoto_Upload=%d" %(auto_run_value and 1 or 0, auto_snapshot_value and 1 or 0, face_detect_value and 1 or 0, photo_upload_value and 1 or 0)
    file_handle = open(config_file, "w")
    file_handle.write(write_strings)
    file_handle.close()
     
class workThread(threading.Thread):
    def __init__(self, queue, interval = 1):
        threading.Thread.__init__(self)
        self.queue = queue
        self.interval = interval
        
    def run(self):
        threading.Thread.run(self)
        while True:
            global camera
            global photo_upload_enable
            msg = self.queue.get()
            print "MSG:%s"%msg
            
            if msg[0] <= Constant.Snapshot_FaceDetect:
                if os.path.exists(Constant.PHOTO_DIRECTORY) is False:
                    os.mkdir(Constant.PHOTO_DIRECTORY)
                file_name = Constant.PHOTO_DIRECTORY + time.strftime("/%Y%m%d_%H%M%S", time.localtime(time.time())) + "_" + msg[1] + "-snap.jpg"
                print "File save as %s" %file_name
                out_put.snapshot(file_name)
                if photo_upload_enable or msg[0] == Constant.Snapshot_Remote:
                    upload_file(file_name) 
                if msg[0] == Constant.Snapshot_Remote:
                    self.queue.put([Constant.Snapshot_UploadStart, ""])
            elif Constant.Snapshot_UploadStart == msg[0]:
                if Pipe is not None:
                    Pipe.publish(Constant.PIPE_TOPIC, "snapshot uploading")
                else:
                    print "Error, Pipe not init"
            elif Constant.Snapshot_UploadDone == msg[0]:
                if Pipe is not None:
                    Pipe.publish(Constant.PIPE_TOPIC, "snapshot done-%s"%msg[1])
                else:
                    print "Error, Pipe not init"
            elif Constant.Snapshot_RemoteControl == msg[0]:
                print "Remote Control"
                if Pipe is not None:
                    Pipe.publish(Constant.PIPE_TOPIC, "alarm in process")
                    door_thread = door_open_thread(Pipe)
                    door_thread.setDaemon(True)#thread will be killed when main thread is over
                    door_thread.start()
                else:
                    print "Error, Pipe not init"
            else:
                print "MSG can not be processed"
                
            time.sleep(self.interval)
    
class door_open_thread(threading.Thread):
    def __init__(self, pipe):
        threading.Thread.__init__(self)
        self.msg_pipe = pipe
        
    def run(self):
        threading.Thread.run(self)
        
        global door_handle
        global door_occupied
        
        if door_occupied:
            return
        door_occupied = True
        
        degree = 90
        door_handle.start()
        while degree >= -40:
            door_handle.control(degree)
            degree -= 10
            time.sleep(0.2)
        door_handle.stop()
        
        time.sleep(3)
        
        degree = -50
        door_handle.start()
        while degree <= 90:
            door_handle.control(degree)
            degree += 10
            time.sleep(0.2)
        door_handle.stop()
        
        self.msg_pipe.publish(Constant.PIPE_TOPIC, "alarm done")
        door_occupied = False
    
class videoFrame_thread(threading.Thread):
    def __init__(self, camera):
        threading.Thread.__init__(self)
        self.camera = camera
        self.thread_stop = False
        self.snapshot_enable = False
        self.photo_name = None
        self.cascade = cv2.CascadeClassifier('lbpcascade_frontalface.xml')
        
    def run(self):
        global face_detect_enable
        global msg_queue
        threading.Thread.run(self)
        WINDOW_NAME = 'Captured Video'
        cv2.namedWindow(WINDOW_NAME, cv2.CV_WINDOW_AUTOSIZE)
        cv2.moveWindow(WINDOW_NAME, 10, 50)
        cv2.startWindowThread()
        while True:
            if self.thread_stop:
                break
            self.readstatus, self.frame = self.camera.read()#frame data is (B, G, R)
            if self.frame is None:
                continue
            if self.snapshot_enable:
                cv2.imwrite(self.photo_name, self.frame)
                self.snapshot_enable = False
#             self.rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
#             self.a = Image.fromarray(self.rgb)
#             self.b = ImageTk.PhotoImage(image = self.a)
#             self.canvas.create_image(0, 0, image = self.b, anchor = tk.NW)
#             self.root.update()
            vis = self.frame.copy()
            if face_detect_enable:
                faces = self.cascade.detectMultiScale(cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY), 1.3, 5)
                cur_face_num = len(faces)
                for (x, y, w, h) in faces:
                    print "Face:(%d, %d, %d, %d)"%(x, y, w, h)
                    cv2.rectangle(vis, (x, y), (x+w, y+h), (0, 255, 0), 2)
                if cur_face_num > 0:
                    if cur_face_num != last_face_num:
                        last_face_num = cur_face_num
                        if msg_queue is not None:
                            msg_queue.put([Constant.Snapshot_FaceDetect, "FaceDetect"])
                else:
                    last_face_num = 0
            cv2.imshow(WINDOW_NAME, vis)
            cv2.waitKey(1)
        cv2.destroyWindow(WINDOW_NAME)
        
    def stop(self):
        self.thread_stop = True
        
    def snapshot(self, file_name_with_path):
        self.snapshot_enable = True
        self.photo_name = file_name_with_path
        while self.snapshot_enable:
            if os.path.isfile(file_name_with_path):
                return
            else:
                time.sleep(0.01)

if __name__ == '__main__':
    ip_camera()