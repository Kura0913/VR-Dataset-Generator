import os

def clear_folder(folder_path):
    try:
        # 確認資料夾存在
        if os.path.exists(folder_path):
            # 取得資料夾中的所有檔案
            files = os.listdir(folder_path)
            
            # 迭代檔案，刪除每個檔案
            for file in files:
                file_path = os.path.join(folder_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            
            print(f"已清除 {folder_path} 中的所有檔案。")
        else:
            print(f"資料夾 {folder_path} 不存在。")
    except Exception as e:
        print(f"發生錯誤：{e}")

# 指定要清除的資料夾路徑
folder_list = ['.\original\\', '.\mask\\', '.\BBox\\', '.\label\\']
# 呼叫清除資料夾的函式

for folder in folder_list:
    clear_folder(folder)
