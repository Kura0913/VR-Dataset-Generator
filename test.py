import cv2
import numpy as np

# 讀取圖片
image = cv2.imread('20240108014241096923.png')

# 指定的色碼，這裡以RGB格式表示，你可以根據需要修改
target_color = np.array([205,72,54])

# 找到與目標色碼接近的像素點
mask = np.all(image == np.array([target_color]), axis=-1)

# 將符合條件的像素點調整為白色，其餘調整為黑色
image[mask] = [255, 255, 255]
image[~mask] = [0, 0, 0]

# 顯示處理後的圖片
cv2.imshow('Processed Image', image)
cv2.waitKey(0)
cv2.destroyAllWindows()
