import os

import jCloudq.jCWSBucket as CWSBucket

Bucket = None

class CloudqWs():
    def __init__(self):
        global Bucket
        if Bucket is None:
            Bucket = CWSBucket.CWSBucket()
            print "CWSBucket initial"
    
    def open(self, on_notify):
        global Bucket
        if Bucket is not None:
            Bucket.open("True", on_notify)
            print "CloudqWS Open!"
        else:
            print "Error! Must init first!"
            
    def list_file(self):
        global Bucket
        if Bucket is not None:
            file_list = Bucket.list()
            return file_list
        else:
            print "Error! Not init"
            
    def get_file_size(self, obj):
        global Bucket
        if Bucket is not None:
            file_size = Bucket.getobjsize(obj)
            return file_size
        else:
            print "Error! Not init"
            
    def upload_file(self, file_path):
        global Bucket
        idx = 0
        if Bucket is not None:
            local_file = os.path.abspath(file_path)
            if os.path.exists(local_file):
                idx = Bucket.upload(local_file)
                print("File %s start upload at index %d" %(local_file, idx))
            else:
                print "File is not exist!"
        else:
            print "Error! Not init"
        return idx
            
    def download_file(self, source_file, dest_file = None):
        global Bucket
        idx = 0
        if Bucket is not None:
            if dest_file is None:
                dest_file = os.path.join(os.getcwd(), source_file)
            idx = Bucket.download(source_file, dest_file)
            print("File %s start download at index %d, Store at %s" %(source_file, idx, dest_file))
        else:
            print "Error! Not init"
        return idx
            
    def delete_file(self, file):
        global Bucket
        Bucket.delete(file)
        print("File %s has already deleted!" %(file))
        
    def close(self):
        global Bucket
        if Bucket is not None:
            Bucket.close()
            print "CloudqWS Close!"
        else:
            print "Error! Must init first!"
        