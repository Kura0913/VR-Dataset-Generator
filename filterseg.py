import os

# folders' path
bbox_folder = '.\BBox\\'
seg_folder = '.\mask\\'
original_folder = '.\original\\'
label_folder = '.\label\\'

# get file list
bbox_files = set(os.listdir(bbox_folder))
seg_files = set(os.listdir(seg_folder))
original_files = set(os.listdir(original_folder))
label_files = set(os.listdir(label_folder))

# file files to delete
files_to_delete = (bbox_files | original_files) - seg_files

# start delete
for file in files_to_delete:
    bbox_path = os.path.join(bbox_folder, file)
    seg_path = os.path.join(seg_folder, file)
    original_path = os.path.join(original_folder, file)
    label_path = os.path.join(label_folder, os.path.splitext(file)[0] + ".txt")

    # remove the file
    if os.path.exists(bbox_path):
        os.remove(bbox_path)
    if os.path.exists(seg_path):
        os.remove(seg_path)
    if os.path.exists(original_path):
        os.remove(original_path)
    if os.path.exists(label_path):
        os.remove(label_path)

print("Files deleted successfully.")