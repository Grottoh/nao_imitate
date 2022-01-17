# From Python
# It requires OpenCV installed for Python
import sys
import cv2
import os
from sys import platform
import argparse
import numpy as np
import math
import time
import numpy as np
path_python_release = "C:/Program Files/openpose/build/python/openpose/Release"
path_64_release = "C:/Program Files/openpose/build/x64/Release"
path_bin = "C:/Program Files/openpose/build/bin"
path_images = "C:/Program Files/openpose/examples/media"
path_models = "C:/Program Files/openpose/models"

#edges = {(1,2), (2,3), (3,4), (1,5), (5,6), (6,7)}
#2, 3, 5, 6



def get_angle(edge1,  edge2, points):
    #assert tuple(sorted(edge1)) in edges
    #assert tuple(sorted(edge2)) in edges
    #print(points[edge1[0]-1], points[edge1[1]-1])
    #print(points[edge2[0]-1], points[edge2[1]-1])
    edge1set = set(edge1)
    edge2set = set(edge2)
    mid_point = edge1set.intersection(edge2set).pop()
    a = (edge1set-edge2set).pop()
    b = (edge2set-edge1set).pop()
    v1 = points[mid_point-1]-points[a-1]
    v2 = points[mid_point-1]-points[b-1]
    #print(v1, v2)

    angle = (math.degrees(np.arccos(np.dot(v1,v2)
                                    /(np.linalg.norm(v1)*np.linalg.norm(v2)))))

    p1 = points[np.delete(np.asarray(edge2), np.where(np.asarray(edge2) == mid_point))-1][0][1]
    p0 = points[mid_point-1][1]
    if p1 > p0:
        angle = 360 - angle
    #
    #print(angle)
    return angle





try:
    # Windows Import
    sys.path.append(path_python_release);
    os.environ['PATH'] = os.environ['PATH'] + ';' + path_64_release + ";" + path_bin + ";"
    import pyopenpose as op
except ImportError as e:
    print('Error: OpenPose library could not be found. Did you enable `BUILD_PYTHON` in CMake and have this Python script in the right folder?')
    raise e

# Starting OpenPose

#hoeveel nogig als je opnieuw runned? Eerste try-catch nodig?d
def img_to_angle(img, opWrapper, file_index, log_time_start, log_opcomp, log_convangle):

    # Process Image
    datum = op.Datum()
    datum.cvInputData = img
    opWrapper.emplaceAndPop(op.VectorDatum([datum]))
    pose = datum.poseKeypoints
    
    # Add an item to the openpose computation log
    log_opcomp.append( (file_index, log_time_start, time.time(), pose) )
      
    # Mark the start time of a subsequent section of code
    log_time_start = time.time()
    
    #print()
    #print(pose)
    if not isinstance(pose, type(None)):
        points = pose[0, 1:8, :2]
        angles_2 = get_angle((1, 2), (2, 3), points)
        angles_3 = get_angle((2, 3), (3, 4), points)
        angles_5 = get_angle((1, 5), (5, 6), points)
        angles_6 = get_angle((5, 6), (6, 7), points)
        angles = [angles_2, angles_3, angles_5, angles_6]
    else:
        angles = [0, 0, 0, 0]
        
    # Add an item to the pose-to-angle conversion log
    log_convangle.append( (file_index, log_time_start, time.time(), angles) )
    
    return angles

# params = dict()
# params["model_folder"] = path_models
# #hoeveel nogig als je opnieuw runned? Eerste try-catch nodig?d
# def img_to_angle(img, file_index, log_time_start, log_opcomp, log_convangle):
#         opWrapper = op.WrapperPython()
#         opWrapper.configure(params)
#         opWrapper.start()
#
#         # Process Image
#         datum = op.Datum()
#         datum.cvInputData = img
#         opWrapper.emplaceAndPop(op.VectorDatum([datum]))
#         pose = datum.poseKeypoints
#
#         # Add an item to the openpose computation log
#         log_opcomp.append( (file_index, log_time_start, time.time(), pose) )
#
#         # Mark the start time of a subsequent section of code
#         log_time_start = time.time()
#
#         #print()
#         #print(pose)
#         if not isinstance(pose, type(None)):
#             points = pose[0, 1:8, :2]
#             angles_2 = get_angle((1, 2), (2, 3), points)
#             angles_3 = get_angle((2, 3), (3, 4), points)
#             angles_5 = get_angle((1, 5), (5, 6), points)
#             angles_6 = get_angle((5, 6), (6, 7), points)
#             angles = [angles_2, angles_3, angles_5, angles_6]
#         else:
#             angles = [0, 0, 0, 0]
#
#         # Add an item to the pose-to-angle conversion log
#         log_convangle.append( (file_index, log_time_start, time.time(), angles) )
#
#         return angles

# points = np.array([[0, 0],[1, 0], [0, 1], [1, 1], [-1, 0], [0, -1], [-1, -1], [-1, 1], [1, -1]])
#
#
#
# angles_2 = get_angle((1, 2), (2, 4), points)
# angles_2 = get_angle((1, 2), (2, 9), points)
# angles_3 = get_angle((1, 5), (5, 8), points)
# angles_3 = get_angle((1, 5), (5, 7), points)



