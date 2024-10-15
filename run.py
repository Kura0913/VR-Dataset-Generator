import os
import json
from DatasetGenerrator import DatasetGenerator

def main():
    with open("config_setting.json", encoding="utf-8") as json_file:
        config_setting = json.load(json_file)

    generator_class = DatasetGenerator()

    if config_setting['config']['mode']:
        if config_setting['config']['mode'] == 'detection':            
            print(f'Current mode:detection. Try to start generating detection dataset...')
            generator_class.detect_generator()
        elif config_setting['config']['mode'] == 'segmentation':
            print(f'Current mode:segmentation. Try to start generating segmentation dataset...')
            generator_class.segmentation_generator()
    

if __name__ == "__main__":
    main()