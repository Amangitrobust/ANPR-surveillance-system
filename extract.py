# import easyocr as ocr
import cv2
# import numpy as np
# for character detection
import pytesseract

# convert image to grayscale
def grayscale(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# image thresholding
def thres_image(gray_img):
    res, thres = cv2.threshold(gray_img, 140, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thres

# remove extra border from image
def remove_borders(image):
    contours, heirarchy =  cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cntSorted = sorted(contours, key=lambda x:cv2.contourArea(x))
    cnt = cntSorted[-1]
    x,y,w,h = cv2.boundingRect(cnt)
    crop = image[y:y+h, x:x+w]
    return crop

# denoising image
def denoise(image):
    denoise_img = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 15)
    return denoise_img

# preprocessing image before applying tesseract
def preprocess_image(image):
    image = denoise(image)
    image = grayscale(image)
    image = thres_image(image)
    image = remove_borders(image)
    return image

# function to extract characters from plate
def extract_license_no(img , coordinates):
    license_no = ''
    # [x_min, y_min, x_max, y_max] . x_min and y_min are coordinates of the top-left corner of the bounding box. x_max and y_max are coordinates of bottom-right corner of the bounding box.
    x, y, w, h = int(coordinates[0,0]), int(coordinates[0,1]), int(coordinates[0,2]), int(coordinates[0,3])
    img = img[y:h, x:w]     # cropping image [start_row:end_row, start_column:end_column]

    img = preprocess_image(img)

    #PYTESSERACT
    custom_configuration = r'--psm 10 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -c tessedit_min_conf=80'
    license_no = pytesseract.image_to_string(img,lang='eng', config=custom_configuration)

    return license_no