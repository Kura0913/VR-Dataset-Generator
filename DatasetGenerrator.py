import json
import airsim
import time
import cv2
import numpy as np
from datetime import datetime

class DatasetGenerator:
    def __init__(self):
        self.config = self.load_config()
        self.color_dict = self.load_color_dict()
        # controller
        self.get_log = False
        # connected to arisim client
        self.client = airsim.VehicleClient()
        # object list
        self.object_name_list = self.config['config']['classes'].split(' ')
        # Set the minimum Bounding Box area, which can be used to filter out objects that are too small.
        self.min_area = self.config['config']['area']
        # img resize info
        self.img_target_size = [self.config['config']['image_size']['width'], self.config['config']['image_size']['height']]
        # delay time
        self.delay_time = self.config['config']['delay']
        # set camera name
        self.camera_name = 0

    def load_config(self):
        with open("config_setting.json", encoding="utf-8") as json_file:
            config = json.load(json_file)

        return config
    
    # get color list for mask
    def load_color_dict(self):
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
    def save_classes_list(self, path, object_name_list):
        with open(path + "classes.txt", "w") as file:
            for class_name in object_name_list:
                file.write(f'{class_name}\n')


    def check_pose(self, prev_pose : airsim.Pose, curr_pose : airsim.Pose):
        prev_ori = prev_pose.orientation
        prev_loc = prev_pose.position
        curr_ori = curr_pose.orientation
        curr_loc = curr_pose.position

        if self.check_position(prev_loc, curr_loc) and self.check_orientation(prev_ori, curr_ori):
            return True
        else:
            return False
    
    def check_position(self, prev_loc_, curr_loc_):
            if(prev_loc_.x_val == curr_loc_.x_val and prev_loc_.y_val == curr_loc_.y_val and prev_loc_.z_val == curr_loc_.z_val):
                return True
            else:
                return False
            
    def check_orientation(self, prev_ori_, curr_ori_):
        if(prev_ori_.w_val == curr_ori_.w_val and prev_ori_.x_val == curr_ori_.x_val and prev_ori_.y_val == curr_ori_.y_val and prev_ori_.z_val == curr_ori_.z_val):
            return True
        else:
            return False
    
    def get_bbox_color_list(self):
        mask_color_cnt = 0
        bbox_color_cnt = 0
        objects_cnt_list = []
        # set objects' mask
        for object_name in self.object_name_list:
            objects = self.client.simListSceneObjects(f'{object_name}[\w]*')
            bbox_color_cnt = 0
            # set mask color for each object
            for mesh_name in objects:
                if mask_color_cnt + 1 < 255:
                    self.client.simSetSegmentationObjectID(mesh_name, mask_color_cnt + 1, True)
                    mask_color_cnt += 1
                    # record each object's num
                    bbox_color_cnt += 1
            # save object's num to list
            objects_cnt_list.append(bbox_color_cnt)

        return objects_cnt_list

    def get_image_data(self):
        # get images response
        ori_response, seg_response,  = self.client.simGetImages(
            [airsim.ImageRequest(self.camera_name, airsim.ImageType.Scene), airsim.ImageRequest(self.camera_name, airsim.ImageType.Segmentation)]
        )

        # get original image from airsim
        ori_raw_image = ori_response.image_data_uint8
        # get segmentation image from airsim
        seg_raw_image = seg_response.image_data_uint8

        # trans to uint_8 array form
        combine_img_ary = cv2.imdecode(airsim.string_to_uint8_array(ori_raw_image), cv2.IMREAD_COLOR)
        ori_img_ary = cv2.imdecode(airsim.string_to_uint8_array(ori_raw_image), cv2.IMREAD_COLOR)
        seg_img_ary = cv2.imdecode(airsim.string_to_uint8_array(seg_raw_image), cv2.IMREAD_COLOR)

        # resize the image
        combine_img_ary = cv2.resize(combine_img_ary, self.img_target_size)
        ori_img_ary = cv2.resize(ori_img_ary, self.img_target_size)
        seg_img_ary = cv2.resize(seg_img_ary, self.img_target_size)

        return combine_img_ary, ori_img_ary, seg_img_ary

    def save_photo(self, filename, ori_img_ary, seg_img_ary, original_path, mask_path):
        seg_fname = mask_path + filename
        ori_fname = original_path + filename
        # save the original and segamentation image
        cv2.imwrite(seg_fname + '.jpg', seg_img_ary)
        cv2.imwrite(ori_fname + '.jpg', ori_img_ary)

    def draw_boundingbox(self, filename, save_path_label, objects_cnt_list, seg_img_ary, combine_img_ary):
        # reset mask_color_cnt
        mask_color_cnt = 0

        for idx, objects_num in enumerate(objects_cnt_list):
            # Initialize the bounding box list of the object
            bounding_boxes = []
            for i in range(objects_num):                
                target_color = np.array(self.color_dict[mask_color_cnt+1])
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
                with open(save_path_label + filename + ".txt", "a") as file:
                    for contour in contours:
                        # Calculate area
                        area = cv2.contourArea(contour)
                        # If the area is too small, no action will be taken.
                        if area > self.min_area:
                            # Get boundary coordinates
                            x, y, w, h = cv2.boundingRect(contour)

                            bounding_boxes.append((x, y, x+w, y+h))
                            # Calculate the relative coordinates of the center of the bounding box (normalized coordinates)
                            center_x = (x + w / 2) / seg_img_ary.shape[1]
                            center_y = (y + h / 2) / seg_img_ary.shape[0]
                            relative_width = w / seg_img_ary.shape[1]
                            relative_height = h / seg_img_ary.shape[0]

                            # write the info into the txt file
                            file.write(f"{idx} {center_x} {center_y} {relative_width} {relative_height}\n")
            for bbox in bounding_boxes:
                x1, y1, x2, y2 = bbox
                cv2.rectangle(combine_img_ary, (x1, y1), (x2, y2), tuple(self.color_dict[mask_color_cnt+1]), 2)
                cv2.putText(combine_img_ary, self.object_name_list[idx], (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, tuple(self.color_dict[mask_color_cnt+1]), 2)
        
        return combine_img_ary
    
    def draw_polygon(self, filename, save_path_label, objects_cnt_list, seg_img_ary, combine_img_ary):
        # reset mask_color_cnt
        mask_color_cnt = 0

        for idx, objects_num in enumerate(objects_cnt_list):
            # Initialize the bounding box list of the object
            polygon_data = []
            for i in range(objects_num):
                target_color = np.array(self.color_dict[mask_color_cnt+1])
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
                with open(save_path_label + filename + ".txt", "a") as file:
                    for contour in contours:
                        polygon_data = []
                        flattened_points = []
                        # Calculate area
                        area = cv2.contourArea(contour)
                        # If the area is too small, no action will be taken.
                        if area > self.min_area:
                            # Simplify polygons
                            polygon_data.append((contour.reshape(-1)))
                            # convert polygon_data to yolov7 format(x1 y1 x2 y2...)
                            for idx_point_data, val in enumerate(polygon_data[0]):
                                if (idx_point_data % 2) == 0:
                                    flattened_points.append((val / self.img_target_size[0]))
                                else:
                                    flattened_points.append((val / self.img_target_size[1]))
                            # convert to string without brackets
                            flattened_string = ' '.join(map(str, flattened_points))
                            file.write(f'{idx} {flattened_string}\n')

                            points = contour.astype(np.int32)
                            for point in points:
                                cv2.circle(combine_img_ary, tuple(point[0]), 1, (255, 0, 0), -1)
                            cv2.polylines(combine_img_ary, [points], isClosed=True, color=(255, 0, 0), thickness=1)

        return combine_img_ary
    
    def detect_generator(self):
        save_path_original = self.config['file_path']['detection']['original']
        save_path_mask = self.config['file_path']['detection']['mask']
        save_path_combine = self.config['file_path']['detection']['bbox']
        save_path_label = self.config['file_path']['detection']['label']

        print('---------------------------------------connect succesed!!------------------------------------')
        print('classes list:', self.object_name_list)
        print('resize:', self.img_target_size)
        # set all objects' segmentation mask to block
        self.client.simSetSegmentationObjectID("[\w]*", 0, True)

        self.save_classes_list(save_path_label, self.object_name_list)
        vehicle_prev_pose = self.client.simGetVehiclePose()

        while True:
            vehicle_curr_pose = self.client.simGetVehiclePose()
            if (not self.check_pose(vehicle_prev_pose, vehicle_curr_pose)):
                print(f'Please stop moving to start generate VR dataset.')
                self.get_log = False
                vehicle_prev_pose = vehicle_curr_pose
                time.sleep(1)
                continue
            else:
                if (not self.get_log):
                    print('Start generate dataset...')
                    self.get_log = True
            vehicle_prev_pose = vehicle_curr_pose

            objects_cnt_list = self.get_bbox_color_list()
            
            # if there are no objects
            if all(num == 0 for num in objects_cnt_list):
                time.sleep(0.5)
                continue

            combine_img_ary, ori_img_ary, seg_img_ary = self.get_image_data()

            # check wheather get masks
            is_black = np.all(seg_img_ary == 0)
            if is_black:
                continue

            filename = datetime.now().strftime('%Y%m%d%H%M%S%f')
            self.save_photo(filename, ori_img_ary, seg_img_ary, save_path_original, save_path_mask)

            combine_img_ary = self.draw_boundingbox(filename, save_path_label, objects_cnt_list, seg_img_ary, combine_img_ary)

            bbox_fname = save_path_combine + filename
            cv2.imwrite(bbox_fname + '.jpg', combine_img_ary)
        
            print(f'Generate success, {filename} is saved to folders under segmentation.')

            time.sleep(self.delay_time)

    def segmentation_generator(self):
        save_path_original = self.config['file_path']['segmentation']['original']
        save_path_mask = self.config['file_path']['segmentation']['mask']
        save_path_combine = self.config['file_path']['segmentation']['segphoto']
        save_path_label = self.config['file_path']['segmentation']['label']
        print('---------------------------------------connect succesed!!------------------------------------')
        print('classes list:', self.object_name_list)
        print('resize:', self.img_target_size)
        # set all objects' segmentation mask to block
        self.client.simSetSegmentationObjectID("[\w]*", 0, True)

        self.save_classes_list(save_path_label, self.object_name_list)
        vehicle_prev_pose = self.client.simGetVehiclePose()

        while True:
            vehicle_curr_pose = self.client.simGetVehiclePose()
            if (not self.check_pose(vehicle_prev_pose, vehicle_curr_pose)):
                print(f'Please stop moving to start generate VR dataset.')
                self.get_log = False
                vehicle_prev_pose = vehicle_curr_pose
                time.sleep(1)
                continue
            else:
                if (not self.get_log):
                    print('Start generate dataset...')
                    self.get_log = True
            vehicle_prev_pose = vehicle_curr_pose

            objects_cnt_list = self.get_bbox_color_list()
            
            # if there are no objects
            if all(num == 0 for num in objects_cnt_list):
                time.sleep(0.5)
                continue

            combine_img_ary, ori_img_ary, seg_img_ary = self.get_image_data()

            # check wheather get masks
            is_black = np.all(seg_img_ary == 0)
            if is_black:
                continue

            filename = datetime.now().strftime('%Y%m%d%H%M%S%f')
            self.save_photo(filename, ori_img_ary, seg_img_ary, save_path_original, save_path_mask)

            combine_img_ary = self.draw_polygon(filename, save_path_label, objects_cnt_list, seg_img_ary, combine_img_ary)

            seg_fname = save_path_combine + filename
            cv2.imwrite(seg_fname + '.jpg', combine_img_ary)

            print(f'Generate success, {filename} is saved to folders under segmentation.')

            time.sleep(self.delay_time)