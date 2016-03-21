
import jCloudq.jGowPipe as CPipe

Pipe = None

class CloudqPipe():
    def __init__(self, on_connect=None, on_disconnect=None, on_publish=None, on_message=None):
        global Pipe
        Pipe = CPipe.GowPipe()
        if on_connect is not None:
            Pipe.on_connect = on_connect
        if on_disconnect is not None:
            Pipe.on_disconnect = on_disconnect
        if on_publish is not None:
            Pipe.on_publish = on_publish
        if on_message is not None:
            Pipe.on_message = on_message
        print "Pipe init"
        
    def open(self):
        global Pipe
        if Pipe is not None:
            Pipe.open()
            print "Pipe open"
        else:
            print "Pipe not init"
    
    def close(self):
        global Pipe
        if Pipe is not None:
            Pipe.close()
            print "Pipe close"
        else:
            print "Pipe not init"
            
    def connect(self):
        global Pipe
        if Pipe is not None:
            Pipe.connect()
            print "Pipe connect"
        else:
            print "Pipe not init"
            
    def disconnect(self):
        global Pipe
        if Pipe is not None:
            Pipe.disconnect()
            print "Pipe disconnect"
        else:
            print "Pipe not init"
            
    def subscribe(self, topic):
        global Pipe
        if Pipe is not None:
            Pipe.subscribe(topic)
            print "Pipe subscribe"
        else:
            print "Pipe not init"
            
    def publish(self, topic, message):
        global Pipe
        if Pipe is not None:
            Pipe.publish(topic, message)
            print "Pipe publish"
        else:
            print "Pipe not init"
            
    def isConnect(self):
        global Pipe
        status = False
        if Pipe is not None:
            status = Pipe.isConnected()
            print "Pipe isConnected %b" %status
        else:
            print "Pipe not init"
        return status

