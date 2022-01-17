import paramiko
import numpy as np
import time
import os
import sys
import process_image
import re
import pickle

"""
Run with <send_angles> as argument to send angles, otherwise it retrieves images

Get the paths right:
    - Create folder .../<ssh_code/> on laptop Tommie
    - Put <process_image.py> in the same folder
Adjust ip-adress each time the robot (re-)connects
Run the code with python 2 (or install openpose for python 3)

Create new buffer folders on the nao and on Tommie's laptop (and remove the old one):
    - buffer_images
    - buffer_angles
    - buffer_permanent
Make sure we have the right robot (with the right password and directories)
"""


path_python_release = "C:/Program Files/openpose/build/python/openpose/Release"
path_64_release = "C:/Program Files/openpose/build/x64/Release"
path_bin = "C:/Program Files/openpose/build/bin"
path_images = "C:/Program Files/openpose/examples/media"
path_models = "C:/Program Files/openpose/models"

try:
    # Windows Import
    sys.path.append(path_python_release);
    os.environ['PATH'] = os.environ['PATH'] + ';' + path_64_release + ";" + path_bin + ";"
    import pyopenpose as op
except ImportError as e:
    print('Error: OpenPose library could not be found. Did you enable `BUILD_PYTHON` in CMake and have this Python script in the right folder?')
    raise e


def dump(path, l):
    with open(path, "wb") as f:
        pickle.dump(l, f)

class ExternalProcessor():
    
    """ Run by a laptop or PC which does some processing for the NAO. """
    
    def __init__(self, is_nao=True):
        
        self.time_started = time.time()
        
        self.port = 22
        if is_nao:
            self.ip        = "169.254.121.20" # Tends to change
            self.username  = "nao"
            self.password  = "HRI2021/"
            self.path_main_ext = "/home/nao/imitate/"
        else:
            self.ip        = "192.168.1.50"
            self.username  = "ubuntu"
            self.password  = "rpOttonr1"
            self.path_main_ext = "/home/ubuntu/HRI/"
        self.path_buffer_images_ext = self.path_main_ext+"buffer_images/"
        self.path_buffer_angles_ext = self.path_main_ext+"buffer_angles/"
        self.fnt_image  = "image_{:06d}.npy"      # The file name template for images
        self.fnt_angles = "angles_{:06d}.npy" # The file name template for angles
        
        #self.path_main_int   = "D:/University/Master/Human-Robot Interaction/Project/ssh_tests/"
        self.path_main_int = "C:/Users/tommi/Documents/Courses_2021/Human Robot Interaction/Project/ssh_code/"
        self.path_buffer_images_int = self.path_main_int+"buffer_images/"
        self.path_buffer_angles_int = self.path_main_int+"buffer_angles/"
        
        self.ftp_client = None
    
    def connect(self):
        
        def createSSHClient():
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(self.ip, self.port, self.username, self.password)
            return client
        
        ssh = createSSHClient()
        self.ftp_client = ssh.open_sftp()
        
    def clear_buffer(self, path_buffer):
        buffer = os.listdir(path_buffer)
        for filename in buffer:
            path_file = os.path.join(path_buffer, filename)
            os.remove(path_file)
        print("Cleared all {} items from buffer <{}>.".format(len(buffer), path_buffer))
    
        
    def trim_buffer(self, path_buffer, buffer_limit=10):
        buffer = sorted(os.listdir(path_buffer))
        if len(buffer) > buffer_limit:
            path_oldest_file = os.path.join(path_buffer, buffer[0])
            os.remove(path_oldest_file)
            print("Deleted file <{}>.".format(path_oldest_file))
    
    def get_nth_last_file(self, path_buffer, internal=True, n=4):
        """ 
        Find the filename of the file that was added to the buffer 
        nth-to-last. Taking the last file often results in taking a file
        that is still being saved (I think), causing errors.
        
        Assumes that there are only files in the buffer that belong there,
        i.e. files named according to the right file name template.
        """
        if internal:
            buffer = sorted(os.listdir(path_buffer))
        else:
            buffer = self.ftp_client.listdir_attr(path_buffer)
            buffer = sorted([item.filename for item in buffer])
        if len(buffer) < n:
            return "", -1
        else:
            filename = buffer[-n]
            match = re.match("[a-z]+_([0-9]+).npy", filename)
            file_index = int(match.group(1))
            return filename, file_index
    
    def get_path_log(self, prefix, path_dir):
        nth_log = 0
        for fn in os.listdir(path_dir):
            if fn[:len(prefix)] == prefix:
                nth_log += 1
        log_name = prefix+"{:03d}.pkl".format(nth_log)
        path_log = path_dir+log_name
        return path_log
    
    def transfer_images(self):
        
        self.clear_buffer(self.path_buffer_images_int)
        
        def transfer(filename):
            try:
                self.ftp_client.get(self.path_buffer_images_ext+filename, 
                                    self.path_buffer_images_int+filename)
                print("Retrieved file <{}>.".format(filename))
            except IOError:
                print("Unable to retrieve file <{}>...".format(self.path_buffer_images_ext+filename))
        
        # Keep a log of the times at which images were retrieved from the NAO by the external processor
        log_imret = [] # (index, log_time_start, log_time_end); image index is derived from the file name
        try:
                
            filename_previous = ""
            while True:
                
                # Mark the start time of a subsequent section of code
                log_time_start = time.time()
                
                filename, file_index = self.get_nth_last_file(self.path_buffer_images_ext, internal=False)
                if filename == "":
                    #print("Buffer is empty...")
                    pass
                elif filename_previous == filename:
                    #print("Same file <{}>...".format(filename_previous))
                    pass
                else: # Copy the last added file from the nao to the local machine
                    transfer(filename)
                    filename_previous = filename
                    self.trim_buffer(self.path_buffer_images_int)
                    
                    # Add an item to the image retrieval log
                    log_imret.append( (file_index, log_time_start, time.time()) )
                            
        except KeyboardInterrupt:
            # Store the image retrieval log as a numpy array
            path_log_imret = self.get_path_log("log_imret_", self.path_main_int+"logs/")
            dump(path_log_imret, log_imret)

            self.clear_buffer(self.path_buffer_images_int)
    
    def send_angles(self):
        
        self.clear_buffer(self.path_buffer_angles_int)
        
        def get_image(path_file):
            try:
                image = np.load(path_file)
                print("Retrieved image <{}>.".format(path_file))
                return image
            except Exception as error:
                print("Error retrieving image <{}>: <{}>".format(path_file, error))
                return None
        
        def send_file(filename):
            try:
                self.ftp_client.put(self.path_buffer_angles_int+filename,
                                    self.path_buffer_angles_ext+filename)
                print("Sent file <{}>.".format(filename))
                return True
            except IOError:
                print("Unable to send file <{}>...".format(filename))
                return False
        
        # Keep a log of image loading data, openpose computation data, pose-to-angle conversion data, angle saving data, and angle transfer data
        log_imload = []    # (index, log_time_start, log_time_end); index is derived from the file name
        log_opcomp = []    # (index, log_time_start, log_time_end, pose); index is derived from the file name
        log_convangle = [] # (index, log_time_start, log_time_end, angles); index is derived from the file name
        log_angsend = []   # (index, log_time_start, log_time_end, angles); index is derived from the file name
        try:
            
            
            params = dict()
            params["model_folder"] = path_models
            opWrapper = op.WrapperPython()
            opWrapper.configure(params)
            opWrapper.start()
            
            filename_previous = ""
            while True:
                
                # Mark the start time of a subsequent section of code
                log_time_start = time.time()
                
                filename, file_index = self.get_nth_last_file(self.path_buffer_images_int, internal=True)
                
                # Copy the last added file from the nao to the local machine
                if not filename == "" and not filename_previous == filename:
                    image = get_image(self.path_buffer_images_int+filename)
                    if not isinstance(image, type(None)):
                        
                        # Add an item to the image load log
                        log_imload.append( (file_index, log_time_start, time.time()) )
                        
                        # Mark the start time of a subsequent section of code
                        log_time_start = time.time()
                        
                        #angles = process_image.img_to_angle(image, file_index, log_time_start, log_opcomp, log_convangle)
                        angles = process_image.img_to_angle(image, opWrapper, file_index, log_time_start, log_opcomp, log_convangle)
                        
                        # Mark the start time of a subsequent section of code
                        log_time_start = time.time()
                        
                        fn_angles = self.fnt_angles.format(file_index)
                        np.save(self.path_buffer_angles_int+fn_angles, angles)                        
                        send_file(fn_angles)
                        self.trim_buffer(self.path_buffer_angles_int)
                        
                        # Add an item to the angle send log
                        log_angsend.append( (file_index, log_time_start, time.time(), angles) )
                    filename_previous = filename
                        
        except KeyboardInterrupt:
            # Store the image retrieval log as a numpy array
            path_log_imload    = self.get_path_log("log_imload_", self.path_main_int+"logs/")
            path_log_opcomp    = self.get_path_log("log_opcomp_", self.path_main_int+"logs/")
            path_log_convangle = self.get_path_log("log_convangle_", self.path_main_int+"logs/")
            path_log_angsend   = self.get_path_log("log_angsend_", self.path_main_int+"logs/")
            dump(path_log_imload, log_imload)
            dump(path_log_opcomp, log_opcomp)
            dump(path_log_convangle, log_convangle)
            dump(path_log_angsend, log_angsend)

            self.clear_buffer(self.path_buffer_images_int)
    
    def run(self, transfer_images=True):
        
        try:
            self.connect()
            if transfer_images:
                self.transfer_images() # Somehow this is extremely slow when run on another thread (even when making thread specific connections)
            else:
                self.send_angles()
            while True: pass # Ensures that the main thread does not end
        except KeyboardInterrupt: # Close the client
            self.ftp_client.close()
    
if __name__ == "__main__":
    
    transfer_images = True
    if len(sys.argv) > 1:
        argument = sys.argv[1]
        if (argument == "send_angles" or argument == "angles" or
            argument == "False" or argument == "false" or
            argument == "0" or argument == 0):
            transfer_images = False
    external_processor = ExternalProcessor(is_nao=True)
    external_processor.run(transfer_images=transfer_images)
    