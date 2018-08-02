import matplotlib.pyplot as plt
import pydicom
import numpy as np
import cv2
import sys
import os

# 构建一个接口函数，使得对任何输入的图像都能做局部处理
# foo(img_origin, start_point, high, width, retinex_perement)

def method_clahe(img):
    clahe = cv2.createCLAHE(clipLimit=600.0, tileGridSize=(1, 1))
    img_clahe = clahe.apply(img)
    cv2.normalize(img_clahe, img_clahe, 0, 255, cv2.NORM_MINMAX)
    img_en = cv2.convertScaleAbs(img_clahe)
    return img_en

## single scale retinex
def ssr(img, sigma):
    temp = cv2.GaussianBlur(img, (0, 0), sigma)
    gaussian = np.where(temp == 0, 0.01, temp)
    img_ssr = np.log10(img + 0.01) - np.log10(gaussian)

    return img_ssr

def msrcr(origin, sigma, dynamic):
    img_rev = np.zeros((origin.shape[0], origin.shape[1]), dtype=origin.dtype)
    for i in range(0, origin.shape[0]):
        for j in range(0, origin.shape[1]):
            img_rev[i][j] = 4094 - origin[i][j]

    img_msrcr = np.zeros_like(img_rev * 1.0)
    img = ssr(img_rev, sigma)
    ## log[R(x,y)]

    img_arr = img
    mean = np.mean(img_arr)
    sum1 = img_arr.sum()
    img_arr2 = img_arr * img_arr
    sum2 = img_arr2.sum()
    var_squ = sum2 - 2 * mean * sum1 + 1024 * 1024 * mean * mean
    var = np.sqrt(var_squ)

    Min = mean - dynamic * var
    Max = mean + dynamic * var

    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            img_msrcr[i][j] = (img[i][j] - Min) / \
                              (Max - Min) * 255
            ## 溢出判断
            if img_msrcr[i][j] > 255:
                img_msrcr[i][j] = 255
            if img_msrcr[i][j] < 0:
                img_msrcr[i][j] = 0

    cv2.normalize(img_msrcr, img_msrcr, 0, 255, cv2.NORM_MINMAX)
    img_a = cv2.convertScaleAbs(img_msrcr)
    fgamma = 1.4
    img_tmp = np.power((img_a / 255.0), fgamma) * 255.0

    return img_tmp

def img_enhance(origin, start_x, start_y, high, width, method):
    if method == 1:
        sigma = 30 ## 指定尺度（模糊的半径）
        dy = 2  # Dynamic取值越小，图像的对比度越强
        img_en = msrcr(img, sigma, dy)
    elif method == 0:
        img_en = method_clahe(img)
    else:
        print("error")
        return -1
    return img_en


if __name__ == "__main__":
    #输入文件名
    ds = []
    flag = True
    img_path = input('Image path: ')
    data = pydicom.read_file(img_path)
    ds.append(data.pixel_array)

    #默认图片左上角是(0,0)
    while flag == True:
        x, y = input('please enter the point: ').split()
        x = int(x)
        y = int(y)
        if x>1024 or y>1024:
            print("out of range")
        else:
            flag = False
    flag = True

    while flag == True:
        high, width = input('please enter height and width: ').split()
        high = int(high)
        width = int(width)
        if x+high>1024 or y+width > 1024:
            print('out of range')
        else:
            flag = False
    flag = True

    method = input('choose one method(clahe-0 / redinex-1): ')
    method = int(method)

    origin = ds[0]
    img = np.zeros((high, width), dtype=origin.dtype)
    for i in range(x, x + high):
        k = i - x
        for j in range(y, y + width):
            t = j - y
            if origin[i][j] < 700:
                img[k][t] = 4094  # 对黑色边角的处理，直接设置最亮
            else:
                img[k][t] = origin[i][j]
    img_res = img_enhance(img, x, y, high, width, method)

    tmp = np.zeros((origin.shape[0], origin.shape[1]), dtype=origin.dtype)
    tmp[:, :] = origin[:, :]
    cv2.normalize(tmp, tmp, 0, 255, cv2.NORM_MINMAX)
    res = cv2.convertScaleAbs(stmp)

    for i in range(x, x+high):
        k = i - x
        for j in range(y, y+width):
            t = j - y
            if origin[i][j] >= 700:
                res[i][j] = img_res[k][t]

    plt.imshow(res, cmap="gray")
    plt.axis("off")
    plt.show()