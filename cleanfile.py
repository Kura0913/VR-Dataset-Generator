import os
import json

def clear_folder(folder_path):
    try:
        # check path exist
        if os.path.exists(folder_path):
            # get all file in the path
            files = os.listdir(folder_path)
            
            # delete all files
            for file in files:
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            
            print(f"All files in {folder_path} have been cleared.")
        else:
            print(f"Folder {folder_path} does not exist.")
    except Exception as e:
        print(f"Error：{e}")


def main():
    folder_list = []
    # load json
    with open("config_setting.json", encoding="utf-8") as json_file:
        config_setting = json.load(json_file)
    # load paths you want to clear
    if config_setting['config']['mode']:
        if config_setting['config']['mode'] == 'detection':
            folder_list = config_setting['file_path']['detection'].values()
        elif config_setting['config']['mode'] == 'segmentation':
            folder_list = config_setting['file_path']['segmentation'].values()
        else:
            print('config_setting error!!!')

    if len(folder_list) > 0:
        for folder in folder_list:
            clear_folder(folder)
    else:
        print('config_setting error!!!')

if __name__ == "__main__":
    main()