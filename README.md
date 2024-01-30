# VR-Dataset-Generator
## Directions
This tool can generate VR object detection and segmentation training dataset for yolov7.

You can use this tool in any VR environment developed by [Unreal Engine](https://www.unrealengine.com/en-US), and the environment must have the AirSim plugin installed.

Unreal Engine recommends using 4.25, 4.27, 5.1, 5.2.

Read this [page](https://microsoft.github.io/AirSim) to install AirSim plugin for Unreal Engine.

### Detection example
<div style="display:inline-block">
<center class='half'>
<image src="https://github.com/Kura0913/VR-Dataset-Generator/blob/master/detection/original/bbox_example.jpg" alt="image1" width="350"><image src="https://github.com/Kura0913/VR-Dataset-Generator/blob/master/detection/bbox/bbox_example.jpg" alt="image2" width="350">
</center>
</div>

### Segmentation example
<div style="display:inline-block">
<center class='half'>
<image src="https://github.com/Kura0913/VR-Dataset-Generator/blob/master/segmentation/original/seg_example.jpg" alt="image1" width="350"><image src="https://github.com/Kura0913/VR-Dataset-Generator/blob/master/segmentation/segphoto/seg_example.jpg" alt="image2" width="350">
</center>
</div>

## Environment
* Python 3.9
* numpy 1.21.6
* AirSim API : Please read this [page](https://microsoft.github.io/AirSim/apis/) to install AirSim API.
* wheel 0.42.0
* opencv-python
## Useage
### Installation
* Clone this repo

```cmd
git clone https://github.com/Kura0913/VR-Dataset-generator.git
```

* file tree
```
VR-Dataset-generator
|   cleanfile.py
|   config_setting.json
|   filter.py
|   generatedet.py
|   generateseg.py
|   ouput.txt
|   README.md
|   run.py
|   seg_rgbs.txt
|   
+---detection
|   +---bbox
|   |       bbox_example.jpg
|   |       
|   +---label
|   |       bbox_example.txt
|   |       classes.txt
|   |       
|   +---mask
|   |       bbox_example.jpg
|   |       
|   \---original
|           bbox_example.jpg
|           
\---segmentation
    +---label
    |       seg_example.txt
    |       classes.txt
    |       
    +---mask
    |       seg_example.jpg
    |       
    +---original
    |       seg_example.jpg
    |       
    \---segphoto
            seg_example.jpg
```


### config_Setting.json

* mode:'detection' or 'segmentation'
* image_size:Set output image size
* area: Set the minimum area of mask, if mask's area is smaller than minimum area, tool will not generate bounding box or segmentation for the object.
* classes: Set the class to generate dataset for, making sure the class name starts with the name of the mesh in the VR environment.
* delay: Set how often to generate images.

### Notice:
The number of objects generated at a time cannot exceed 253 (including objects outside the field of view).
### run.py
Start generating the dataset, please make sure to execute the VR environment before executing the command.
```cmd
python run.py
```

The generated file will be placed in the folder in the corresponding mode.
detection:bbox, mask, original, label will have file with the same file name in them, you can delete bad cases in bbox and then filter files in other folders via filter.py

segmentation:segphoto, mask, original, label will have file with the same file name in them, you can delete bad cases in segphoto and then filter files in other folders via filter.py

### cleanfile.py
Remove all files in the corresponding folder in the specified mode.
```cmd
python cleanfile.py
```

### filter.py
detection:Compare files in **bbox** and delete redundant files in mask, original, and label.
segmentation:Compare files in **segphoto** and delete redundant files in mask, original, and label.

```cmd
python filter.py
```

deteection:The filtering basis is the files in the **bbox**.
segmentation:The filtering basis is the files in the **segphoto**.

## VR Environment
### TaiwanTrafficObjectDetect.zip
[**Download Link**](https://1drv.ms/f/s!Amw-cef48mmfmkmK3i96dVAVeLpm?e=dtsOZu)

Unzip and use directly, please check whether the path : **.\TaiwanTrafficObjectDetect\Windows\\** contains settings.json.

If not, please add it yourself.

**settings.json** is also on github.

Click **GenerateDataset.exe** to start the environment.

In this VR environment, there are the following objects : **cone delineator jerseybarrier curvemirror transformerbox fence**.
