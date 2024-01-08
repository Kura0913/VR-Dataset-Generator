# VR Dartaset Generator
## Directions
This toll can generate VR training dataset for yolo.
You can use this tool in any VR environment developed by [Unreal Engine](https://www.unrealengine.com/en-US), and the environment must have the AirSim plugin installed.

Unreal Engine recommends using 4.25, 4.27, 5.1, 5.2.

Read this [page](https://microsoft.github.io/AirSim) to install AirSim plugin for Unreal Engine.

## Requirement
* AirSim API: Please read this [page](https://microsoft.github.io/AirSim/apis/) to install AirSim API.
* wheel 0.42.0
* numpy 1.21.6
* opencv
## How to Use
### Install
All files please install in the same folder.

And make sure that there are four folders original, mask, BBox and label.

* original will save original picture.

* mask will save segmentation mask picture.

* BBox will save the original picture with bounding box.

* label will save .txt file with bounding box information.


### generate.py

**Default parameters:**
| parameter name | parameter |
| :--: |:--:|
| image size | 1920*1080 |
| area | 3000 |
| classes | None |
| delay | 1 |

* --img: Set output image size.
* --area: Set the minimum area of mask, if mask's area is smaller than minimum area, tool will not generate bounding box for the mask.
* --classes: Set the class to generate labels for, making sure the class name starts with the name of the mesh in the VR environment.
* --delay: Set how often to generate images.

**example:** 
```cmd
python generate.py --img 960 540 --area 3000 --classes cone --delay 0
```

### cleanfile.py
Remove all files in the original, mask, BBox and label folders.

### filterbbox.py and filterseg.py
Because sometimes AirSim does not capture the mask and cannot generate the bounding box, you need to manually filter out the images that failed to generate. You can delete the image that does not generate a bounding box in the BBox, and then execute filterbbox.py to delete the corresponding data in the original, BBox, and label; or after deleting all black images in the mask, execute filterseg.py to delete the corresponding data in the original, BBox, and label.

## VR Environment
coming soon.