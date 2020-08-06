import re
import os
import glob
import cv2
import numpy as np
from operator import add

from django.shortcuts import render, redirect
from django.conf import settings

from .models import UploadFileForm, CapImage


THE_BEST_NUMBER = 5


def clear_database(request):
    for obj in CapImage.objects.all():
        obj.delete()

    files = glob.glob(os.path.join(settings.MEDIA_ROOT, 'images/*.jpg'))

    for f in files:
        try:
            os.remove(f)
        except OSError as e:
            print("File could not been deleted")

    return redirect(check)


def check(request, template_name='check.html'):
    objs_scored = None
    score = 0

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            cap_image = CapImage(photo=request.FILES['file'])
            objs = None
            try:
                cap_image.save()
                path = re.sub(' ', '_', cap_image.photo.path)
                cropped_img = get_cropped_img(path)
                cv2.imwrite(path, cropped_img)
                cap_image.save()

                objs = list(CapImage.objects.all())
                feature_scores = get_feature_match_scores(path, objs)
                color_scores = get_color_scores(path, objs)
                objs_scored = zip(objs, list(map(combine_score, feature_scores, color_scores)))
                objs_scored = sorted(objs_scored, key=lambda obj: obj[1], reverse=True)

                objs_scored = objs_scored[:THE_BEST_NUMBER]  # only few the best matches

                if len(objs_scored) > 1:
                    score = objs_scored[1][1]

            except Exception as e:
                print(e)

    else:
        form = UploadFileForm()

    return render(request, template_name, {'form': form, 'exists': check_if_exists(score),
                                           'photos': CapImage.objects.all(), 'similar_photos': objs_scored})


def get_cropped_img(path):
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    width, height, channels = img.shape

    # Convert to grayscale.
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply Hough transform on the blurred image.
    detected_circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1.2, int(width / 10))

    if detected_circles is not None:
        detected_circles = np.uint16(np.around(detected_circles))

        a, b, r = 0, 0, 0
        for pt in detected_circles[0, :]:
            if pt[2] > r:
                a, b, r = pt[0], pt[1], pt[2]

        mask = np.zeros((width, height), dtype=np.uint8)
        cv2.circle(mask, (a, b), r, (255, 255, 255), -1, 8, 0)
        res = cv2.bitwise_and(img, img, mask=mask)
        cropped_res = res[b - r:b + r, a - r:a + r]
        return cropped_res

    print("Cap not found")
    return img


def get_feature_match_scores(path, objs):
    # Initiate ORB detector
    orb = cv2.ORB_create()
    img1 = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    kp1, des1 = orb.detectAndCompute(img1, None)
    lowe_ratio = 50

    scores = []
    for obj in objs:
        if re.sub(' ', '_', obj.photo.path) == path:
            scores.append(1000)
            break

        img2 = cv2.imread(re.sub(' ', '_', obj.photo.path), cv2.IMREAD_GRAYSCALE)
        kp2, des2 = orb.detectAndCompute(img2, None)

        # create BFMatcher object
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        # Match descriptors.
        matches = bf.match(des1, des2)
        # Sort them in the order of their distance.
        good = []
        for m in matches:
            if m.distance < lowe_ratio:
                good.append([m])

        scores.append(len(good))

    return scores


def get_color_scores(path, objs):
    scores = []

    hsv_base = cv2.imread(path, cv2.COLOR_BGR2HSV)

    h_bins = 50
    s_bins = 60
    histSize = [h_bins, s_bins]
    h_ranges = [0, 180]
    s_ranges = [0, 256]
    ranges = h_ranges + s_ranges
    channels = [0, 1]

    hist_base = cv2.calcHist([hsv_base], channels, None, histSize, ranges, accumulate=False)

    for obj in objs:
        if re.sub(' ', '_', obj.photo.path) == path:
            scores.append(1)
            break

        hsv_test = cv2.imread(re.sub(' ', '_', obj.photo.path), cv2.COLOR_BGR2HSV)
        hist_test = cv2.calcHist([hsv_test], channels, None, histSize, ranges, accumulate=False)
        score = cv2.compareHist(hist_base, hist_test, cv2.HISTCMP_INTERSECT)

        scores.append(score)

    return scores


def check_if_exists(score):
    THRESHOLD = 200
    SURE_THRESHOLD = 300

    if score > SURE_THRESHOLD:
        return 'found'
    elif score > THRESHOLD:
        return 'possibly found'
    else:
        return 'not found'


def combine_score(feature, color):
    return feature + color * 0.04
