import numpy
import cv2
from matplotlib import pyplot as plt
import json

# Save as json with form:
# <Heure>:
#   <TubeNb>:
#       <Num>
#       <Num>
#       ...
#   <TubeNb>:
#       ...
# <Heure>:
#   ...

jsonHeure = {
  "Heure": 
    {
        "TubeNb": [0, 1, 2, 3, 4, 5],
        "TubeNb2": [0, 1, 2, 3, 4, 5]
    }
}

jsonOut = {}

for i in range(3):
  jsonOut["Heure" + str(i)] = {
        "TubeNb": [0, 1, 2, 3, 4, 5],
        "TubeNb2": [0, 1, 2, 3, 4, 5]
    }

print(jsonOut)

'''
# Load an color image in grayscale
img = cv2.imread('C:\\Users\\Administrateur\\Desktop\\DaphniMaton\\Images\\falseSample.png', 1)

gray_image = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
ret,thresh1 = cv2.threshold(gray_image, 20, 255, cv2.THRESH_BINARY)
edges = cv2.Canny(thresh1, 254, 255)

im2, contours, hierarchy = cv2.findContours(thresh1, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

cv2.drawContours(img, contours, -1, (0,255,0), 3)

titles = ['Original Image','GRAY','BINARY','Edges']
images = [img, gray_image, thresh1, edges]
for i in range(len(titles)):
    plt.subplot(2,3,i+1),plt.imshow(images[i],'gray')
    plt.title(titles[i])
    plt.xticks([]),plt.yticks([])

plt.show()

cv2.waitKey(0)
cv2.destroyAllWindows()
'''