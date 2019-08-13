import math
from scipy.spatial import distance
import requests
import os


def lineToPictures(b, a, c):
    """Transforms a line in a multitude of points where a picture has to be taken.

    a tuple: first point of the line (in cm).
    b tuple: second point of the line (in cm).

    returns: an array of the NEW points.
    """
    thisDist = max(distance.euclidean(a, b), 0.0001)
    newPoints = []

    nb = math.floor(thisDist/float(c))
    top = (thisDist-nb*float(c))/(2*thisDist)

    ax = top * (a[0] - b[0])
    ay = top * (a[1] - b[1])
    for p in range(nb+1):
        newPoints.append((round((b[0] + ax + ((float(c)/thisDist)*(a[0] - b[0]))*p)*100)/100,
                          round((b[1] + ay + ((float(c)/thisDist)*(a[1] - b[1]))*p)*100)/100))

    return newPoints


def getPorts():
    """Used to gather every connected devices on usb.

    returns: list of found devices on COM ports.
    """
    arduinoPorts = os.popen("python -m serial.tools.list_ports").read().strip().replace(' ', '').split('\n')
    if arduinoPorts == ['']:
        return []
    return arduinoPorts


def urlOpen(instance, url):
    """Opens a browser window with specified url.

    url string: the website to go to.
    """
    import webbrowser
    webbrowser.open(url, new=2)


def hitLine(lineA, lineB, point, lineWidth):
    """Checks whether the point is in line or out.

    lineA tuple: a point of the line.
    lineB tuple: another point of the line.
    point tuple: point we want to check.
    lineWidth float: width of the line.

    returns: True if in and False if out.
    """
    if lineWidth < 0:
        raise ValueError('Line width less than zero')
    numerator = abs((lineB[1]-lineA[1])*point[0]-(lineB[0]-lineA[0])*point[1]+lineB[0]*lineA[1]-lineB[1]*lineA[0])
    denominator = max(math.sqrt(pow(lineB[1]-lineA[1], 2)+pow(lineB[0]-lineA[0], 2)), 0.00001)
    if numerator/denominator <= lineWidth+0.001:
        if distance.euclidean(lineA, point) <= distance.euclidean(lineA, lineB) and distance.euclidean(lineB, point) <= distance.euclidean(lineA, lineB):
            return True
    return False


def checkUpdates(versionFile):
    """Checks if a new version exists and updates the current one.

    versionFile string: User's file holding current version

    returns: the new version tag if one exists
    """
    url = 'https://raw.githubusercontent.com/liamLatour/DaphnieMaton/master/version'
    req = requests.get(url).text.strip()

    if os.path.isfile(versionFile):
        # Store configuration file values
        f = open(versionFile, "r")
        contents = f.read().strip()
        f.close()
        if req != contents:
            return req
    else:
        return req
    return False
