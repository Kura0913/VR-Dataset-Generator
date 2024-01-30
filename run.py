import os
import json

def main():
    cmd_line = 'python '

    with open("config_setting.json", encoding="utf-8") as json_file:
        config_setting = json.load(json_file)

    print(config_setting['config']['mode'])

    if config_setting['config']['mode']:
        if config_setting['config']['mode'] == 'detection':
            cmd_line += f'generatedet.py'
            print(f'Current mode:detection. Try to start generating detection dataset...')
        elif config_setting['config']['mode'] == 'segmentation':
            cmd_line += f'generateseg.py'
            print(f'Current mode:segmentation. Try to start generating segmentation dataset...')

        os.system(cmd_line)

if __name__ == "__main__":
    main()