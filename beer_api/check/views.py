import re
import cv2
import numpy as np
import imagehash

from PIL import Image

from django.shortcuts import render, redirect

from .models import UploadFileForm, CapImage


def clear_database(request):
    for obj in CapImage.objects.all():
        obj.delete()

    return redirect(check)


def check(request, template_name='check.html'):
    # for obj in CapImage.objects.all():
    #     obj.delete()
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            cap_image = CapImage(photo=request.FILES['file'])
            objs = None
            try:
                cap_image.save()

                img = cv2.imread(re.sub(' ', '_', cap_image.photo.path), cv2.IMREAD_COLOR)
                width, height, channels = img.shape
                # Convert to grayscale.
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

                # Apply Hough transform on the blurred image.
                detected_circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, 1.2, int(width/10))

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
                    cv2.imwrite(re.sub(' ', '_', cap_image.photo.path), cropped_res)

                hash = imagehash.colorhash(Image.open(re.sub(' ', '_', cap_image.photo.path)), binbits=3)
                cap_image.hash_data = str(hash) if hash else ''
                cap_image.save()

                objs = sorted(CapImage.objects.all(),
                              key=lambda img:
                              imagehash.hex_to_hash(cap_image.hash_data) - imagehash.hex_to_hash(img.hash_data))

            except Exception as e:
                print(e)

            return render(request, template_name,
                          {'form': form,
                           'exists': check_if_exists(request.FILES['file']),
                           'photos': objs})
    else:
        form = UploadFileForm()

    return render(request, template_name, {'form': form, 'exists': None, 'photos': CapImage.objects.all()})


def check_if_exists(file):
    return True
