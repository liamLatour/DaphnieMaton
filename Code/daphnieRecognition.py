import numpy
import cv2

# Load an color image in grayscale
img = cv2.imread('falseSample.png', 1)

gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
ret,thresh1 = cv2.threshold(gray_image, 20, 255, cv2.THRESH_BINARY)
edges = cv2.Canny(thresh1, 254, 255)

im2, contours, hierarchy = cv2.findContours(thresh1, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

cv2.drawContours(img, contours, -1, (0,255,0), 3)

cv2.imshow('image', img)
cv2.waitKey(0)
cv2.destroyAllWindows()