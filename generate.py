import airsim
import cv2
import time
from datetime import datetime
import argparse
import numpy as np


# set save path
SAVE_PATH_ORIGIN = '.\original\\'
SAVE_PATH_MASK = '.\mask\\'
SAVE_PATH_BBOX = '.\BBox\\'
SAVE_PATH_JSON = '.\label\\'
# controller
is_generate = True

# airsim image type
ori_image = airsim.ImageType.Scene
seg_image = airsim.ImageType.Segmentation

# object list
object_name_list = ['cone', 'fence', 'curvemirror', 'jerseybarrier', 'transformerbox']
# Set the minimum Bounding Box area, which can be used to filter out objects that are too small.
min_area = 100
# counter
mask_color_cnt = 0
bbox_color_cnt = 0
objects_cnt_list = []
# set camera name
camera_name = 0
# connected to arisim client
client = airsim.VehicleClient()
# save the color info
color_dict = {}
# img resize info
img_target_size = [960, 540]
# delay time
delay_time = 1

def getColorList():
    global color_dict
    with open("seg_rgbs.txt", "r") as file:
        for line in file:
            # Split data, get key and RGB color values
            parts = line.strip().split('\t')
            index = int(parts[0])
            color_rgb = list(map(int, parts[1][1:-1].split(',')))
            
            # add key and color to the dict
            color_dict[index] = color_rgb


def check_image_count(value):
    if len(value) != 2:
        if len(value) <= 1:
            raise argparse.ArgumentTypeError("Exactly 2 nums are required.")
        else:
            nums = [value[0], value[1]]
    return nums

def main():
    parser = argparse.ArgumentParser(description='Description of your script')
    # define image size
    parser.add_argument('-i', '--img', nargs='+',  type = int, default = [1920, 1080],  help = 'Image new size')
    # define minimize area of mask
    parser.add_argument('-a', '--area', type = int, default = 3000, help = 'minimize area of mask')
    #define classes
    parser.add_argument('-c', '--classes', nargs='+', type = str, default = [], help = 'all classes')
    # define delay time
    parser.add_argument('-d', '--delay', type = int, default = 1, help = 'delay time')

    args = parser.parse_args()
    object_name_list = args.classes
    min_area = args.area
    delay_time = args.delay
    img_target_size = args.img
    print('classes list:', object_name_list)
    print('resize:',img_target_size)
    # set all objects' segmentation mask to block
    print(client.simSetSegmentationObjectID("[\w]*",0,True))

    # get color list
    getColorList()
    # start the program
    while True:
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
                client.simSetSegmentationObjectID(mesh_name, mask_color_cnt + 1, True)
                mask_color_cnt += 1
                # record each object's num
                bbox_color_cnt += 1
            # save object's num to list
            objects_cnt_list.append(bbox_color_cnt)
        # print the nums of each object
        
        # get original image from airsim
        oriRawImage = client.simGetImage(camera_name, ori_image)
        # get segmentation image from airsim
        segRawImage = client.simGetImage(camera_name, seg_image)
        # trans to uint_8 array form
        bbox_image = cv2.imdecode(airsim.string_to_uint8_array(oriRawImage), cv2.IMREAD_COLOR)
        ori_png_ary = cv2.imdecode(airsim.string_to_uint8_array(oriRawImage), cv2.IMREAD_COLOR)
        seg_png_ary = cv2.imdecode(airsim.string_to_uint8_array(segRawImage), cv2.IMREAD_COLOR)

        # resize the image
        bbox_image = cv2.resize(bbox_image, img_target_size)
        ori_png_ary = cv2.resize(ori_png_ary, img_target_size)
        seg_png_ary = cv2.resize(seg_png_ary, img_target_size)



        datetime_str = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
        seg_fname = SAVE_PATH_MASK + datetime_str
        ori_fname = SAVE_PATH_ORIGIN + datetime_str
        # save the original and segamentation image
        cv2.imwrite(seg_fname + '.png', seg_png_ary)
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
                mask_color_cnt += 1
                with open(SAVE_PATH_JSON + datetime_str + ".txt", "a") as file:
                    for contour in contours:
                        # Calculate area
                        area = cv2.contourArea(contour)
                        # If the area is too small, no action will be taken.
                        if area > min_area:
                            # Get boundary coordinates
                            x, y, w, h = cv2.boundingRect(contour)

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

        time.sleep(delay_time)

if __name__ == "__main__":
    main()