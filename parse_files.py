import os
from PIL import Image
import cv2
import yaml
import pathlib
import numpy as np
import sys
import glob
import csv
import time
import pcap
import os
import glob
import dpkt
import math

def read_8(data, idx):
    return data[idx]

def read_16(data, idx):
    return data[idx]+data[idx+1]*256

def read_32(data, idx):
    return data[idx]+ data[idx+1]*256 + data[idx+2]*(256**2) + data[idx+3]*(256**3)





def parse_series():
    pass

def parse_pcap(filename, config):
    print(f"parsing pcap file {filename} \n")

    in_file = filename
    num_blocks = 12
    num_channels = 16
    counter = 0
    cur_azimuth = 0
    to_kill = False
    timestamp_previous = None
    angle_range = np.linspace(-30.67, 10.67, 32)
    points = []
    timestamp_wrhs = []
    start_time = time.clock()

    # pointcloud_dict = {}
    frame_index = 0

    start_time = time.clock()

    lidar_config = [shot["vlp16"]["lidarData"]["pacTimeStamps"] for shot in config["shots"] if "vlp16" in shot]

    with open(in_file, 'rb') as f:
        reader = dpkt.pcap.Reader(f)
        timestamp_shot = []
        points_shot = []

        for ts, buf in reader:
            points_raw_one_cycle = []
            counter += 1
            eth = dpkt.ethernet.Ethernet(buf)
            data = eth.data.data.data
            for i in range(0, num_blocks, 2):
                idx = 0
                data_block = data[i * 100:(i + 1) * 100]
                flag = read_16(data_block, idx)
                idx += 2
                azim = read_16(data_block, idx)/100
                idx += 2
                for j in range(num_channels):
                    dis = read_16(data_block, idx) / 100
                    idx += 2
                    refl = read_8(data_block, idx)
                    idx += 1
                    if dis != 0:
                        points_raw_one_cycle.append((dis, azim, j, refl))
            timestamp = read_32(data[1200:1204], 0)

            if timestamp in lidar_config[frame_index]:
                points_shot.extend(points_raw_one_cycle)
                timestamp_shot.append(timestamp)
            else:
                points.append(points_shot)
                points_shot = []
                print(f"всего было циклов {counter}, ожидалось {len(lidar_config[frame_index])}")
                counter = 0
                frame_index += 1

        points.append(points_shot)
        print(f"всего было циклов {counter}, ожидалось {len(lidar_config[frame_index])}")

    print("Итого:", len(points))
    print(f"Должно было быть шотов: {len(lidar_config)}")

    pointcoords = [process_frame(point) for point in points]

    print("Всего потрачено времени:", time.clock() - start_time)

    return pointcoords


def process_frame(frame):  # dis, azim - [0,36000], elevation_index - [0,31], refl
    elevation_idxs = [item[2] for item in frame]
    frame = np.array(frame, np.float32)
    #     angle_range = np.linspace(-30.67,10.67,32) #for velodyne 32
    angle_range = np.linspace(-15, 15, 16)
    channel_angle = np.zeros_like(angle_range)
    channel_angle[::2] = angle_range[:int(len(angle_range) / 2)]
    channel_angle[1::2] = angle_range[int(len(angle_range) / 2):]

    frame[:, 2] = channel_angle[elevation_idxs]
    frame[:, 1] = frame[:, 1]

    frame[:, 1] = frame[:, 1] / 180 * np.pi
    frame[:, 2] = frame[:, 2] / 180 * np.pi
    frame[:, 3] = (frame[:, 3] - np.min(frame[:, 3])) / (np.max(frame[:, 3]) - np.min(frame[:, 3]))

    x = frame[:, 0] * np.cos(frame[:, 1]) * np.cos(frame[:, 2])
    y = frame[:, 0] * np.sin(frame[:, 1]) * np.cos(frame[:, 2])
    z = frame[:, 0] * np.sin(frame[:, 2])

    point_coords = np.vstack((x, y, z, frame[:, 3]))

    return point_coords.T


# pc = process_frame(points[0])

def parse_video(filename):
    print("video parsing of: ", filename)

    start_time = time.clock()

    images = []

    cap = cv2.VideoCapture(filename)

    while (cap.isOpened()):
        try:
            ret, frame = cap.read()
            if not(ret):
                break
            images.append(frame)
        except:
            print("ошибка")

    cap.release()

    print(f"потрачено времени {time.clock() - start_time}")
    print(f"длина ролика {len(images)} кадров \n")

def parse_config(filename):
    print("parsing config ", filename)

    start_time = time.clock()

    if filename.endswith(".yml"):

        with open(filename, "r+") as fp:
            file_inside = fp.read()
            if file_inside[:file_inside.index("\n")] == "%YAML:1.0":
                file_inside = file_inside[:file_inside.index("\n")].replace(":", " ") + file_inside[
                                                                                        file_inside.index('\n'):]
            data = yaml.load(file_inside, Loader = yaml.FullLoader)

    if filename.endswith(".tsv"):
        pass

    print(type(data))
    # print(data["header"])
    print(data.keys())
    print(len(data['shots']))
    print(data['shots'][0].keys())
    print("времени потрачено: ", time.clock() - start_time)

    return data

def check_config(config):

    num_shots = 0
    num_shots_lidar = 0
    for shot in config["shots"]:
        if "central60" in shot:
            num_shots += 1
        if "vlp16" in shot:
            num_shots_lidar += 1*len(shot['vlp16']["lidarData"]["pacTimeStamps"])
            # print(len(shot['vlp16']["lidarData"]["pacTimeStamps"]))
            # print(shot['vlp16']["lidarData"]["pacTimeStamps"][-1] - shot['vlp16']["lidarData"]["pacTimeStamps"][0])
    print(f"итого шотов с камеры {num_shots}")
    print(f"итого шотов с лидара {num_shots_lidar} \n")


def main(directory, mode, series, episode):
    print(os.path.join(directory,mode,series,episode)+"*")

    episode_fullname = os.path.join(directory,(mode+"."+ series+ "." + episode))
    episode_files = glob.glob( episode_fullname+"*")
    print(episode_files)

    files_to_check = ["central60.avi", "info.yml", "info.yml.gz",
                      "leftSide.avi", "rightSide.avi", "t25.det.tsv",
                      "t25.trg.tsv", "vlp16.pcap"]

    # file_to_check_dict = {"central60.avi":parse_video(), "info.yml":parse_config(), "info.yml.gz":parse_config(),
    #                   "leftSide.avi":parse_video(), "rightSide.avi":parse_video(), "t25.det.tsv":parse_config(),
    #                   "t25.trg.tsv":parse_config(), "vlp16.pcap":parse_pcap()}

    for str_end in files_to_check:
        file_to_check = episode_fullname + '.' + str_end
        print(file_to_check,  "exist: ", os.path.exists(file_to_check))
        assert os.path.exists(file_to_check), "Check all files please"

    info_config = parse_config(episode_fullname + '.' + 'info.yml')

    check_config(info_config)

    # det_config = parse_config(episode_fullname + '.' + 't25.det.tsv')
    # trg_config = parse_config(episode_fullname + '.' + 't25.trg.yml')

    # central_video = parse_video(episode_fullname+'.'+ "central60.avi")
    # leftside_video = parse_video(episode_fullname + '.' + "leftSide.avi")
    # rightside_video = parse_video(episode_fullname + "." + "rightSide.avi")

    lidar_data = parse_pcap(episode_fullname + '.' + 'vlp16.pcap', info_config)






if __name__ == "__main__":
    mode = "trm"
    num_series = "205"
    episode = "001"
    print("парсим ", os.listdir('./data/testdata'))
    main('./data/testdata', mode, num_series, episode)





