import airsim
import cv2
import time
from datetime import datetime
import numpy as np
import json

# get color list for mask
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
# save classes list to classes.txt
def save_classes_list(path, object_name_list):
    with open(path + "classes.txt", "a") as file:
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
    SAVE_PATH_ORIGINAL = config_setting['file_path']['detection']['original']
    SAVE_PATH_MASK = config_setting['file_path']['detection']['mask']
    SAVE_PATH_BBOX = config_setting['file_path']['detection']['bbox']
    SAVE_PATH_LABEL = config_setting['file_path']['detection']['label']
    # controller
    get_log = False
    # airsim image type
    ori_image = airsim.ImageType.Scene
    seg_image = airsim.ImageType.Segmentation

    # object list
    object_name_list = config_setting['config']['classes'].split(' ')
    # Set the minimum Bounding Box area, which can be used to filter out objects that are too small.
    min_area = config_setting['config']['area']
    # img resize info
    img_target_size = [config_setting['config']['image_size']['width'], config_setting['config']['image_size']['height']]
    # delay time
    delay_time = config_setting['config']['delay']
    # counter
    mask_color_cnt = 0
    bbox_color_cnt = 0
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
    client.simSetSegmentationObjectID("[\w]*",0,True)

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
        bbox_color_cnt = 0
        objects_cnt_list = []
        # set objects' mask
        for object_name in object_name_list:
            objects = client.simListSceneObjects(f'{object_name}[\w]*')
            bbox_color_cnt = 0
            # set mask color for each object
            for mesh_name in objects:
                if mask_color_cnt + 1 < 255:
                    client.simSetSegmentationObjectID(mesh_name, mask_color_cnt + 1, True)
                    mask_color_cnt += 1
                    # record each object's num
                    bbox_color_cnt += 1
            # save object's num to list
            objects_cnt_list.append(bbox_color_cnt)
        # if there are no objects
        if all(num == 0 for num in objects_cnt_list):
            time.sleep(0.5)
            continue
        # get original image from airsim
        oriRawImage = client.simGetImage(camera_name, ori_image)
        # get segmentation image from airsim
        segRawImage = client.simGetImage(camera_name, seg_image)
        # trans to uint_8 array form
        bbox_image = cv2.imdecode(airsim.string_to_uint8_array(oriRawImage), cv2.IMREAD_COLOR)
        ori_png_ary = cv2.imdecode(airsim.string_to_uint8_array(oriRawImage), cv2.IMREAD_COLOR)
        seg_png_ary = cv2.imdecode(airsim.string_to_uint8_array(segRawImage), cv2.IMREAD_COLOR)
        # check wheather get masks
        is_black = np.all(seg_png_ary == 0)
        if ~is_black:
            # resize the image
            bbox_image = cv2.resize(bbox_image, img_target_size)
            ori_png_ary = cv2.resize(ori_png_ary, img_target_size)
            seg_png_ary = cv2.resize(seg_png_ary, img_target_size)



            datetime_str = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
            seg_fname = SAVE_PATH_MASK + datetime_str
            ori_fname = SAVE_PATH_ORIGINAL + datetime_str
            # save the original and segamentation image
            cv2.imwrite(seg_fname + '.jpg', seg_png_ary)
            cv2.imwrite(ori_fname + '.jpg', ori_png_ary)
            
            # reset mask_color_cnt
            mask_color_cnt = 0

            for idx, objects_num in enumerate(objects_cnt_list):
                # Initialize the bounding box list of the object
                bounding_boxes = []
                for i in range(objects_num):                
                    target_color = np.array(color_dict[mask_color_cnt+1])
                    target_color[0], target_color[2] = target_color[2], target_color[0]
                    # Get target color's infomation
                    mask_area = np.all(seg_png_ary == target_color, axis=-1)
                    # Set target color to white, others to block
                    mask = np.zeros_like(seg_png_ary)
                    mask[mask_area] = [255, 255, 255]
                    mask[~mask_area] = [0, 0, 0]
                    mask = cv2.cvtColor(mask, cv2.COLOR_RGB2GRAY)
                    # get area in the mask                
                    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    # Combine all white areas into a convex polygon
                    if len(contours) <= 0:
                        mask_color_cnt += 1
                        continue
                    all_contours = np.concatenate(contours)
                    # Calculate the convex polygon of all white areas
                    hull = cv2.convexHull(all_contours)
                    mask_color_cnt += 1
                    with open(SAVE_PATH_LABEL + datetime_str + ".txt", "a") as file:                    
                        # Calculate area
                        area = cv2.contourArea(hull)
                        # If the area is too small, no action will be taken.
                        if area > min_area:
                            # Get boundary coordinates
                            x, y, w, h = cv2.boundingRect(hull)
                            bounding_boxes.append((x, y, x+w, y+h))
                            # Calculate the relative coordinates of the center of the bounding box (normalized coordinates)
                            center_x = (x + w / 2) / seg_png_ary.shape[1]
                            center_y = (y + h / 2) / seg_png_ary.shape[0]
                            relative_width = w / seg_png_ary.shape[1]
                            relative_height = h / seg_png_ary.shape[0]

                            # write the info into the txt file
                            file.write(f"{idx} {center_x} {center_y} {relative_width} {relative_height}\n")
                for bbox in bounding_boxes:
                    x1, y1, x2, y2 = bbox
                    cv2.rectangle(bbox_image, (x1, y1), (x2, y2), tuple(color_dict[mask_color_cnt+1]), 2)
                    cv2.putText(bbox_image, object_name_list[idx], (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, tuple(color_dict[mask_color_cnt+1]), 2)


            bbox_fname = SAVE_PATH_BBOX + datetime_str
            cv2.imwrite(bbox_fname + '.jpg', bbox_image)

        print(f'Generate success, {datetime_str} is saved to folders under detection.')

        time.sleep(delay_time)

if __name__ == "__main__":
    main()