import math
from scipy.spatial import distance
import requests
import os
import sys

sys.argv = sys.argv if __name__ == '__main__' else [sys.argv[0]]

from .localization import _
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
import webbrowser


def lineToPictures(b, a, c):
    """Transforms a line in a multitude of points where a picture has to be taken

    Arguments:
        b {tuple} -- first point of the line (in cm)
        a {tuple} -- second point of the line (in cm)
        c {float} -- cm between pictures

    Returns:
        array -- the NEW points
    """
    if c == 0:
        return []

    thisDist = round(max(distance.euclidean(a, b), 0.0001)*10)/10
    newPoints = []

    nb = math.floor(thisDist/float(c))
    top = (thisDist-nb*float(c))/(2*thisDist)

    ax = top * (a[0] - b[0])
    ay = top * (a[1] - b[1])
    for p in range(nb+1):
        newPoints.append((round((b[0] + ax + ((float(c)/thisDist)*(a[0] - b[0]))*p)*1000)/1000,
                          round((b[1] + ay + ((float(c)/thisDist)*(a[1] - b[1]))*p)*1000)/1000))

    return newPoints


def getPorts():
    """Used to gather every connected devices on usb.

    returns: list of found devices on COM ports.
    """
    arduinoPorts = os.popen(
        "python -m serial.tools.list_ports").read().strip().replace(' ', '').split('\n')
    if arduinoPorts == ['']:
        return []
    return arduinoPorts


def urlOpen(instance, url):
    """Opens a browser window with specified url.

    url string: the website to go to.
    """
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
    numerator = abs((lineB[1]-lineA[1])*point[0]-(lineB[0]-lineA[0])
                    * point[1]+lineB[0]*lineA[1]-lineB[1]*lineA[0])
    denominator = max(distance.euclidean(lineA, lineB), 0.00001)
    if numerator/denominator <= lineWidth+0.001:
        if distance.euclidean(lineA, point) <= distance.euclidean(lineA, lineB) and distance.euclidean(lineB, point) <= distance.euclidean(lineA, lineB):
            return True
    return False


def checkUpdates(version, popup):
    url = 'https://raw.githubusercontent.com/liamLatour/DaphnieMaton/master/version'
    req = requests.get(url).text.strip()

    if req == version:
        return

    textPopup = "[u]A new version is available ![/u]\n\n \
                    You can download it [ref=https://github.com/liamLatour/DaphnieMaton/releases][color=0083ff][u]here[/u][/color][/ref]"

    popbox = BoxLayout()
    poplb = Label(text=textPopup, markup=True)
    poplb.bind(on_ref_press=urlOpen)
    popbox.add_widget(poplb)

    popup(_('New Version ' + req), popbox)
