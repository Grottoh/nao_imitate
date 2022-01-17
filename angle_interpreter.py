import os
import numpy as np
import almath
import math
import time
from naoqi import ALProxy
import shutil
import re
import pickle

"""
The function <use_angles> still has to be fixed

Create new buffer folders on the nao and on Tommie's laptop (and remove the old one):
    - buffer_images
    - buffer_angles
    - buffer_permanent
Make sure we have the right robot (with the right password and directories)
"""

CLEAR_ANGLES = True  # If true clear the angles stored in the buffer before starting
STORE_PERMANENTLY = False  # If True move buffer items to permanent storage instead of deleting them
TIME_LIMIT = 30  # Run for the specified amount of seconds
BUFFER_LIMIT = 10  # The maximum number of items allowed in the angles buffer
NTH_LAST = 2


def dump(path, l):
    with open(path, "wb") as f:
        pickle.dump(l, f)


class MyClass(GeneratedClass):
    def _init_(self):
        GeneratedClass._init_(self)

    def onLoad(self):
        # put initialization code here

        self.path_main = "/home/nao/imitate/"
        self.path_buffer_angles = self.path_main + "buffer_angles/"
        self.fnt_angles = "angles_{:06d}.npy"  # The file name template for angles

        if CLEAR_ANGLES:
            self.clear_buffer(self.path_buffer_angles)

        self.store_permanently = STORE_PERMANENTLY
        if self.store_permanently:
            self.path_buffer_permanent = self.path_main + "buffer_permanent/B-{}".format(time.time())
            os.mkdir(self.path_buffer_permanent)

    def onUnload(self):
        # put clean-up code here
        pass

    def p(self, string):
        print(" @@@ ------------------> " + string + " <------------------ @@@ ")

    def onInput_onStart(self):

        # Retrieve angles from local storage, and use them to move
        self.retrieve_angles()

    def clear_buffer(self, path_buffer):
        buffer = os.listdir(path_buffer)
        for filename in buffer:
            path_file = os.path.join(path_buffer, filename)
            os.remove(path_file)
        print("Cleared all {} items from buffer <{}>.".format(len(buffer), path_buffer))

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

    def get_nth_last_file(self, path_buffer, internal=True, n=NTH_LAST):
        """
        Find the filename of the file that was added to the buffer
        nth-to-last. Taking the last file often results in taking a file
        that is still being saved, causing errors.

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

    def use_angles(self, angles):

        # names = ["RShoulderRoll", "RElbowRoll", "LShoulderRoll", "LElbowRoll"]
        names = ["LShoulderRoll", "LElbowRoll", "RShoulderRoll", "RElbowRoll"]
        # names_pitch = ["RShoulderPitch", "RShoulderPitch", "LShoulderPitch", "LShoulderPitch"]
        names_pitch = ["RShoulderPitch", "LShoulderPitch", "LShoulderPitch", "RShoulderPitch"]

        motionProxy = ALProxy("ALMotion")
        fractionMaxSpeed = 0.5
        # ranges = [[-76, 18],[2, 88.5],[-18, 76],[-88.5, -2]]
        ranges = [[-18, 76], [-88.5, -2], [-76, 18], [2, 88.5]]

        joint_angles = ['nan', 'nan', 'nan', 'nan']
        for index, an in enumerate(angles):
            if not np.isnan(an):
                # print(index, an)
                if index == 1:
                    if an > 180:
                        angle1 = math.radians(90)
                        an = an - 180
                    else:
                        angle1 = math.radians(-90)
                        an = 180 - an
                        print("angle1", angle1)
                    motionProxy.setAngles(names_pitch[index], angle1, fractionMaxSpeed)
                if index == 3:
                    if an > 180:
                        angle2 = math.radians(90)
                        an = -(an - 180)
                    else:
                        angle2 = math.radians(-90)
                        an = -(180 - an)
                        print("angle2", angle2)
                    motionProxy.setAngles(names_pitch[index], angle2, fractionMaxSpeed)

                if index == 2:
                    an = an - 90
                if index == 0:
                    an = -(an - 90)
                ranged_an = max(ranges[index][0], min(ranges[index][1], -an))
                # print(names[index], ranged_an)
                radians = math.radians(ranged_an)
                joint_angles[index] = radians
                motionProxy.setAngles(names[index], radians, fractionMaxSpeed)
        return tuple(joint_angles)

    def retrieve_angles(self):

        """
        Angles computed from the images are sent back to the NAO buffer,
        retrieve them and use them to imitate the pose they describe.
        """

        def get_angles(path_file):
            try:
                angles = np.load(path_file)
                print("Retrieved angles <{}>.".format(path_file))
                return angles
            except Exception:
                return None

        # Keep a log of angle loading data, angle to joint-angle conversion, and joint movement data
        log_angload = []  # (index, log_time_start, log_time_end, angles); index is derived from the file name
        log_movejoints = []  # (index, log_time_start, log_time_end, joint-angles); index is derived from the file name

        time_start = time.time()
        filename_previous = ""
        while time.time() - time_start < TIME_LIMIT:

            # Mark the start time of a subsequent section of code
            log_time_start = time.time()

            self.trim_buffer(self.path_buffer_angles)

            # Retrieve the nth-to-last stored angles from the NAO's buffer
            filename, file_index = self.get_nth_last_file(self.path_buffer_angles)
            if not filename == "" and not filename_previous == filename:
                angles = get_angles(self.path_buffer_angles + filename)
                if not isinstance(angles, type(None)):
                    # print("angles", angles)

                    # Add an item to the angle loading log
                    log_angload.append((file_index, log_time_start, time.time(), angles))

                    # Mark the start time of a subsequent section of code
                    log_time_start = time.time()

                    # Move the NAO's joints according to the retrieved angles
                    joint_angles = self.use_angles(angles)

                    # Add an item to the joint moving log
                    log_movejoints.append((file_index, log_time_start, time.time(), joint_angles))

                filename_previous = filename

        # Store the image capture log as a numpy array
        path_log_angload = self.get_path_log("log_angload_", self.path_main + "logs/")
        path_log_movejoints = self.get_path_log("log_movejoints_", self.path_main + "logs/")
        dump(path_log_angload, log_angload)
        dump(path_log_movejoints, log_movejoints)

        if CLEAR_ANGLES:
            self.clear_buffer(self.path_buffer_angles)

        self.onStopped()

    def onInput_onStop(self):
        self.onUnload()  # it is recommended to reuse the clean-up as the box is stopped
        self.onStopped()  # activate the output of the box