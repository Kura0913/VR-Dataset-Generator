import os
import json


def main():
    # folders' path
    reference_folder = ''
    mask_folder = ''
    original_folder = ''
    label_folder = ''

    # load json
    with open("config_setting.json", encoding="utf-8") as json_file:
        config_setting = json.load(json_file)


    if config_setting['config']['mode']:
        if config_setting['config']['mode'] == 'detection':
            reference_folder = config_setting['file_path']['detection']['bbox']
            mask_folder = config_setting['file_path']['detection']['mask']
            original_folder = config_setting['file_path']['detection']['original']
            label_folder = config_setting['file_path']['detection']['label']
        elif config_setting['config']['mode'] == 'segmentation':
            reference_folder = config_setting['file_path']['segmentation']['segphoto']
            mask_folder = config_setting['file_path']['segmentation']['mask']
            original_folder = config_setting['file_path']['segmentation']['original']
            label_folder = config_setting['file_path']['segmentation']['label']

    # get file list
    bbox_files = set(os.path.splitext(filename)[0] for filename in os.listdir(reference_folder))
    seg_files = set(os.path.splitext(filename)[0] for filename in os.listdir(mask_folder))
    original_files = set(os.path.splitext(filename)[0] for filename in os.listdir(original_folder))
    label_files = set(os.path.splitext(filename)[0] for filename in os.listdir(label_folder))

    # file files to delete
    files_to_delete = (seg_files | original_files | label_files) - bbox_files

    # start delete
    for file in files_to_delete:
        reference_path = os.path.join(reference_folder, file + ".jpg")
        mask_path = os.path.join(mask_folder, file + ".jpg")
        original_path = os.path.join(original_folder, file + ".jpg")
        if file != "classes":
            label_path = os.path.join(label_folder, file + ".txt")

        # remove the file
        if os.path.exists(reference_path):
            os.remove(reference_path)
        if os.path.exists(mask_path):
            os.remove(mask_path)
        if os.path.exists(original_path):
            os.remove(original_path)
        if os.path.exists(label_path):
            os.remove(label_path)

    print("Files deleted successfully.")

if __name__ == "__main__":
    main()