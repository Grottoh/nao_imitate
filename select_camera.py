import cv2
import sys
import numpy as np
import time
import os
import shutil
import pickle

# import matplotlib.pyplot as plt

CLEAR_IMAGES = True  # If true clear the angles stored in the buffer before starting
STORE_PERMANENTLY = False  # If True move buffer items to permanent storage instead of deleting them
TIME_LIMIT = 30  # Run for the specified amount of seconds
FPS = 8  # Determine the fps of the camera
BUFFER_LIMIT = 10  # The maximum number of items allowed in the image buffer
SUBSCRIBER_ID = "SUB_TOP_057"  # Will need to be changed sometimes to avoid some strange error


def dump(path, l):
    with open(path, "wb") as f:
        pickle.dump(l, f)


class MyClass(GeneratedClass):
    def init(self):
        GeneratedClass.init(self, False)

    def onLoad(self):
        self.cameraModule = self.session().service("ALVideoDevice")

        self.path_main = "/home/nao/imitate/"
        self.path_buffer_images = self.path_main + "buffer_images/"
        self.fnt_image = "image_{:06d}.npy"  # The file name template for images

        if CLEAR_IMAGES:
            self.clear_buffer(self.path_buffer_images)

        self.store_permanently = STORE_PERMANENTLY
        if self.store_permanently:
            self.path_buffer_permanent = self.path_main + "buffer_permanent/B-{}".format(time.time())
            os.mkdir(self.path_buffer_permanent)

    def clear_buffer(self, path_buffer):
        buffer = os.listdir(path_buffer)
        for filename in buffer:
            path_file = os.path.join(path_buffer, filename)
            os.remove(path_file)
        print("Cleared all {} items from buffer <{}>.".format(len(buffer), path_buffer))

    def onUnload(self):
        pass

    def p(self, string):
        print(" @@@ ------------------> " + string + " <------------------ @@@ ")

    def subTopCam(self):

        # Use the top camera (0)
        AL_kTopCamera = 0
        self.cameraModule.setActiveCamera(AL_kTopCamera)
        self.onReady()

        AL_kQVGA = 1  # resolution <1> = 320x240
        self.width = 320
        self.height = 240

        self.subscriberID = SUBSCRIBER_ID  # Will need to be changed sometimes to avoid some strange error
        AL_kBGRColorSpace = 13  # color space <13> = BGR

        if False:
            self.cameraModule.unsubscribe(self.subscriberID)
            self.p("Unsubscribed the camera")

        # Parameters: subscribeCamera(Name, CameraIndex, Resolution, ColorSpace, FPS)
        self.captureDevice = self.cameraModule.subscribeCamera(
            self.subscriberID, AL_kTopCamera, AL_kQVGA, AL_kBGRColorSpace, FPS)

    def trim_buffer(self, path_buffer, buffer_limit=BUFFER_LIMIT):
        buffer = sorted(os.listdir(path_buffer))
        if len(buffer) > buffer_limit:
            path_oldest_file = os.path.join(path_buffer, buffer[0])
            if self.store_permanently:
                shutil.move(path_oldest_file, self.path_buffer_permanent)
                print("Moved file <{}> to permanent storage.".format(path_oldest_file))
            else:
                os.remove(path_oldest_file)
                print("Deleted file <{}>.".format(path_oldest_file))

    def get_path_log(self, prefix, path_dir):
        nth_log = 0
        for fn in os.listdir(path_dir):
            if fn[:len(prefix)] == prefix:
                nth_log += 1
        log_name = prefix + "{:03d}.pkl".format(nth_log)
        path_log = path_dir + log_name
        return path_log

    def onInput_onUseTopCamera(self):
        # Subscribe the camera
        self.subTopCam()

        # Keep a log of the times at which images were captured with the camera
        log_imcapt = []  # (log_time_start, log_time_end); image index same as list index; index stored in file name

        time_start = time.time()  # Not to be confused with <log_time_start>
        i = 0
        while time.time() - time_start < TIME_LIMIT:

            # Mark the start time of a subsequent section of code
            log_time_start = time.time()

            # Receive image data captured by the NAO camera
            result = self.cameraModule.getImageRemote(self.captureDevice)

            # The image is initially in the form of a binary array
            image_binary = result[6]

            if not image_binary == None:  # We want to transform the image into a numpy array
                image = np.frombuffer(image_binary, dtype=np.uint8)
                image = np.reshape(image, (self.height, self.width, 3))
                filename = self.fnt_image.format(i)
                np.save(self.path_buffer_images + filename, image)

                self.trim_buffer(self.path_buffer_images)

                # Add an item to the image capture log
                log_imcapt.append((i, log_time_start, time.time()))

                i += 1
            else:
                self.p("<image_binary == None>")
            # time.sleep(1/FPS) # Not sure whether necessary or even harmful

        # Store the image capture log as a numpy array
        path_log_imcapt = self.get_path_log("log_imcapt_", self.path_main + "logs/")
        dump(path_log_imcapt, log_imcapt)

        if CLEAR_IMAGES:
            self.clear_buffer(self.path_buffer_images)

    def onInput_onUseBottomCamera(self):
        self.cameraModule.setActiveCamera(1)
        self.onReady()