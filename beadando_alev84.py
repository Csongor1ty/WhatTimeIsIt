#!/usr/bin/python
# -*- coding: utf-8 -*-
import math
import cv2
import numpy as np
from skimage.morphology import skeletonize
from skimage import morphology, filters

# inputPic -> kep az orarol
clockPic = cv2.imread('faliora.jpg')
#tesztképek
#clockPic = cv2.imread('faliora1.jpg')
#clockPic = cv2.imread('faliora2.jpg')
#clockPic = cv2.imread('faliora3.jpg')
#clockPic = cv2.imread('faliora4.jpg')
cv2.imshow('Input', clockPic)
greyscale = cv2.cvtColor(clockPic, cv2.COLOR_BGR2GRAY)
greyscale = 255 - greyscale
rows = greyscale.shape[0]
focusOnBack = True
p2 = 500

# ------------------------------- oralap

while focusOnBack:
    hCircles = cv2.HoughCircles(
        greyscale,
        cv2.HOUGH_GRADIENT,
        1,
        rows / 16,
        param1=200,
        param2=p2,
        minRadius=10,
    )
    if hCircles is None:
        p2 -= 1
        if p2 == 20:
            exit('Hiba az oralap beolvasasaban.')
    else:
        focusOnBack = False

if hCircles is not None:
    hCircles = np.uint16(np.around(hCircles))
    if len(hCircles[0, :]) != 1:
        exit('Az oralap nem egyertelmuen meghatarozhato.')
    for i in hCircles[0, :]:
        kp = (i[0], i[1])
        radius = i[2]
        realRad = int(int(radius) / 1.3)

# ------------------------------- mask

maskOut = np.zeros(clockPic.shape[:2], dtype='uint8')
cv2.circle(maskOut, kp, realRad, (255, 0, 0), -1)
masked = cv2.bitwise_or(greyscale, greyscale, mask=maskOut)
cv2.imshow("Oralap", masked)

# ------------------------------- Gauss

blur = cv2.GaussianBlur(masked, (5, 5), 2.0)
blur = cv2.threshold(blur, 130, 255, cv2.THRESH_BINARY)[1]
bn = blur > filters.threshold_otsu(blur)
cv2.imshow("Mutatok", blur)
# ------------------------------- skeletonize

skeleton = morphology.skeletonize(bn)
szukitett = skeletonize(bn)
szukitett = (255 * szukitett).clip(0, 255).astype(np.uint8)

dreg = cv2.HoughLinesP(
    szukitett,
    1,
    np.pi / 180,
    5,
    None,
    0,
    realRad / 3,
)
mutatok = []
if dreg is not None:
    for i in range(0, len(dreg)):
        if mutatok != 2:
            j = dreg[i][0]
            hossz = math.sqrt((j[0] - j[2]) ** 2 + (j[1] - j[3]) ** 2)
            mutatok.append([hossz, j])
mutatokTomb = []
if len(mutatok) < 2:
    exit('A mutatok nem jol elkulonithetoek.')


# ------------------------------- mutatok hosszv. + berajzolas


def leghosszabb_mutatok():
    mutatokTomb.append(mutatok[0])
    for (q, w) in enumerate(mutatok):
        if mutatokTomb[0][0] < w[0]:
            mutatokTomb[0] = w
    m = mutatokTomb[len(mutatokTomb) - 1]
    mutatok.remove(m)
    m = m[1]
    cv2.line(clockPic,
             (m[0],
              m[1]),
             (m[2],
              m[3]),
             (130, 222, 0),
             2)


# ------------------------------- nagymutato
leghosszabb_mutatok()
large_temp = mutatokTomb[0][1]
nagymutato_k = []
nagymutato_t = []
if math.sqrt((kp[0] - large_temp[0]) ** 2 + (kp[1] - large_temp[1])
             ** 2) < math.sqrt((kp[0] - large_temp[2]) ** 2 + (kp[1]
                                                               - large_temp[3]) ** 2):
    nagymutato_k = [large_temp[0], large_temp[1]]
    nagymutato_t = [large_temp[2], large_temp[3]]
else:
    nagymutato_k = [large_temp[2], large_temp[3]]
    nagymutato_t = [large_temp[0], large_temp[1]]

# ------------------------------- kismutato
leghosszabb_mutatok()
small_temp = mutatokTomb[1][1]
kismutato_k = []
kismutato_t = []
if math.sqrt((kp[0] - small_temp[0]) ** 2 + (kp[1] - small_temp[1])
             ** 2) < math.sqrt((kp[0] - small_temp[2]) ** 2 + (kp[1]
                                                               - small_temp[3]) ** 2):
    kismutato_k = [small_temp[0], small_temp[1]]
    kismutato_t = [small_temp[2], small_temp[3]]
else:
    kismutato_k = [small_temp[2], small_temp[3]]
    kismutato_t = [small_temp[0], small_temp[1]]

# ------------------------------- iranyvektorok

bv = [nagymutato_t[0] - nagymutato_k[0], nagymutato_t[1]
      - nagymutato_k[1]]
lv = [kismutato_t[0] - kismutato_k[0], kismutato_t[1] - kismutato_k[1]]
pivot_v = [0, -1]
pivot_length = 1


# ------------------------------- convert


def digitalize(pivot_v, arm):
    et = 1
    if arm[0] < 0:
        et = -1
    ido = et * math.degrees(math.acos((arm[0] * pivot_v[0] + arm[1]
                                       * pivot_v[1]) / (math.sqrt(arm[0] ** 2
                                                                  + arm[1] ** 2) * math.sqrt(pivot_v[0]
                                                                                             ** 2 + pivot_v[
                                                                                                 1] ** 2)))) / 30
    if ido < 0:
        ido = 12 + ido
    return ido


whattime = str(int(digitalize(pivot_v, lv) // 1)) + ':' \
           + str(int(round(digitalize(pivot_v, bv) * 5)))
print(whattime)

# ------------------------------- eredmeny + digit

cv2.putText(
    clockPic,
    "Az ido: "+whattime,
    (0, 30),
    cv2.FONT_HERSHEY_COMPLEX_SMALL,
    1.0,
    2,
)
cv2.imshow('Eredmeny', clockPic)
cv2.waitKey(0)
