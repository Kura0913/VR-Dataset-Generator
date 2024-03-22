import airsim
import cv2
import time
from datetime import datetime
import numpy as np
import json

def getColorList():
    color_dict = {}
    with open("seg_rgbs.txt", "r") as file:
        for line in file:
            # Split data, get key and RGB color values
            parts = line.strip().split('\t')
            index = int(parts[0])
            color_rgb = list(map(int, parts[1][1:-1].split(',')))
            
            # add key and color to the dict
            color_dict[index] = color_rgb
    return color_dict

def save_classes_list(path, object_name_list):
    with open(path + "classes.txt", "w") as file:
        for class_name in object_name_list:        
            file.write(f'{class_name}\n')

def checkPose(prev_pose : airsim.Pose, curr_pose : airsim.Pose):
    def checkPosition(prev_loc_, curr_loc_):
        if(prev_loc_.x_val == curr_loc_.x_val and prev_loc_.y_val == curr_loc_.y_val and prev_loc_.z_val == curr_loc_.z_val):
            return True
        else:
            return False
    def checkOrientation(prev_ori_, curr_ori_):
        if(prev_ori_.w_val == curr_ori_.w_val and prev_ori_.x_val == curr_ori_.x_val and prev_ori_.y_val == curr_ori_.y_val and prev_ori_.z_val == curr_ori_.z_val):
            return True
        else:
            return False

    prev_ori = prev_pose.orientation
    prev_loc = prev_pose.position
    curr_ori = curr_pose.orientation
    curr_loc = curr_pose.position

    if checkPosition(prev_loc, curr_loc) and checkOrientation(prev_ori, curr_ori):
        return True
    else:
        return False
    
def main():
    # load json
    with open("config_setting.json", encoding="utf-8") as json_file:
        config_setting = json.load(json_file)
    # set save path
    SAVE_PATH_ORIGINAL = config_setting['file_path']['segmentation']['original']
    SAVE_PATH_MASK = config_setting['file_path']['segmentation']['mask']
    SAVE_PATH_SEGPHOTO = config_setting['file_path']['segmentation']['segphoto']
    SAVE_PATH_LABEL = config_setting['file_path']['segmentation']['label']
    # object list
    object_name_list = config_setting['config']['classes'].split(' ')
    # Set the minimum Bounding Box area, which can be used to filter out objects that are too small.
    min_area = config_setting['config']['area']
    # img resize info
    img_target_size = [config_setting['config']['image_size']['width'], config_setting['config']['image_size']['height']]
    # delay time
    delay_time = config_setting['config']['delay']
    # controller
    get_log = False
    
    # counter
    mask_color_cnt = 0
    seg_color_cnt = 0
    objects_cnt_list = []
    # set camera name
    camera_name = 0
    # save the color info
    color_dict = {}
    # connected to arisim client
    client = airsim.VehicleClient()
    print('---------------------------------------connect succesed!!------------------------------------')
    print('classes list:', object_name_list)
    print('resize:',img_target_size)
    # set all objects' segmentation mask to block
    print(client.simSetSegmentationObjectID("[\w]*",0,True))

    # get color list
    color_dict = getColorList()
    # save classes.txt
    save_classes_list(SAVE_PATH_LABEL, object_name_list)

    vehicle_prev_pose = client.simGetVehiclePose()
    # start the program
    while True:
        vehicle_curr_pose = client.simGetVehiclePose()
        if (not checkPose(vehicle_prev_pose, vehicle_curr_pose)):
            print(f'Please stop moving to start generate VR dataset.')
            get_log = False
            vehicle_prev_pose = vehicle_curr_pose
            time.sleep(1)
            continue
        else:
            if (not get_log):
                print('Start generate dataset...')
                get_log = True
        vehicle_prev_pose = vehicle_curr_pose

        # reset the counter
        mask_color_cnt = 0
        seg_color_cnt = 0
        objects_cnt_list = []
        # set objects' mask
        for object_name in object_name_list:
            objects = client.simListSceneObjects(f'{object_name}[\w]*')
            seg_color_cnt = 0
            # set mask color for each object
            for mesh_name in objects:
                if mask_color_cnt + 1 < 255:
                    client.simSetSegmentationObjectID(mesh_name, mask_color_cnt + 1, True)
                    mask_color_cnt += 1
                    # record each object's num
                    seg_color_cnt += 1
            # save object's num to list
            objects_cnt_list.append(seg_color_cnt)

        # get images response
        ori_response, seg_response,  = client.simGetImages(
            [airsim.ImageRequest(camera_name, airsim.ImageType.Scene), airsim.ImageRequest(camera_name, airsim.ImageType.Segmentation)]
        )

        # get original image from airsim
        ori_raw_image = ori_response.image_data_uint8
        # get segmentation image from airsim
        seg_raw_image = seg_response.image_data_uint8

        # trans to uint_8 array form
        bbox_img_ary = cv2.imdecode(airsim.string_to_uint8_array(ori_raw_image), cv2.IMREAD_COLOR)
        ori_img_ary = cv2.imdecode(airsim.string_to_uint8_array(ori_raw_image), cv2.IMREAD_COLOR)
        seg_img_ary = cv2.imdecode(airsim.string_to_uint8_array(seg_raw_image), cv2.IMREAD_COLOR)
        # check wheather get masks
        is_black = np.all(seg_img_ary == 0)
        if ~is_black:
            # resize the image
            seg_output_image = cv2.resize(ori_img_ary, img_target_size)
            ori_img_ary = cv2.resize(ori_img_ary, img_target_size)
            seg_img_ary = cv2.resize(seg_img_ary, img_target_size)



            datetime_str = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
            seg_fname = SAVE_PATH_MASK + datetime_str
            ori_fname = SAVE_PATH_ORIGINAL + datetime_str
            # save the original and segamentation image
            cv2.imwrite(seg_fname + '.jpg', seg_img_ary)
            cv2.imwrite(ori_fname + '.jpg', ori_img_ary)
            
            # reset mask_color_cnt
            mask_color_cnt = 0

            for idx, objects_num in enumerate(objects_cnt_list):
                # Initialize the bounding box list of the object
                polygon_data = []
                for i in range(objects_num):
                    target_color = np.array(color_dict[mask_color_cnt+1])
                    target_color[0], target_color[2] = target_color[2], target_color[0]
                    # Get target color's infomation
                    mask_area = np.all(seg_img_ary == target_color, axis=-1)
                    # Set target color to white, others to block
                    mask = np.zeros_like(seg_img_ary)
                    mask[mask_area] = [255, 255, 255]
                    mask[~mask_area] = [0, 0, 0]
                    mask = cv2.cvtColor(mask, cv2.COLOR_RGB2GRAY)

                    # get area in the mask
                    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    mask_color_cnt += 1
                    with open(SAVE_PATH_LABEL + datetime_str + ".txt", "a") as file:
                        for contour in contours:
                            polygon_data = []
                            flattened_points = []
                            # Calculate area
                            area = cv2.contourArea(contour)
                            # If the area is too small, no action will be taken.
                            if area > min_area:
                                # Simplify polygons
                                polygon_data.append((contour.reshape(-1)))
                                # convert polygon_data to yolov7 format(x1 y1 x2 y2...)
                                for idx_point_data, val in enumerate(polygon_data[0]):
                                    if (idx_point_data % 2) == 0:
                                        flattened_points.append((val / img_target_size[0]))
                                    else:
                                        flattened_points.append((val / img_target_size[1]))
                                # convert to string without brackets
                                flattened_string = ' '.join(map(str, flattened_points))
                                file.write(f'{idx} {flattened_string}\n')

                                points = contour.astype(np.int32)
                                for point in points:
                                    cv2.circle(seg_output_image, tuple(point[0]), 1, (255, 0, 0), -1)
                                cv2.polylines(seg_output_image, [points], isClosed=True, color=(255, 0, 0), thickness=1)

            seg_fname = SAVE_PATH_SEGPHOTO + datetime_str
            cv2.imwrite(seg_fname + '.jpg', seg_output_image)

        print(f'Generate success, {datetime_str} is saved to folders under segmentation.')

        time.sleep(delay_time)

if __name__ == "__main__":
    main()