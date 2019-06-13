# -*- coding: utf-8 -*-

"""Test integration of Grad-CAM explanation and image formatter for Keras"""

import pytest

keras = pytest.importorskip('keras')
PIL = pytest.importorskip('PIL')

import numpy as np
from PIL import Image
from keras.applications import (
    mobilenet_v2
)

import eli5
from eli5.keras import image_from_path
from eli5 import format_as_image


# TODO: time these tests

imagenet_cat_idx = 282


@pytest.fixture(scope='module')
def keras_clf():
    # TODO: load weights from a file
    return mobilenet_v2.MobileNetV2(alpha=1.0, include_top=True, weights='imagenet', classes=1000)


@pytest.fixture(scope='module')
def cat_dog_image():
    # TODO: consider a .png example
    doc = image_from_path('tests/images/cat_dog.jpg', image_shape=(224, 224))
    doc = mobilenet_v2.preprocess_input(doc) # FIXME: this preprocessing is hardcoded for mobilenet_v2
    return doc


def assert_attention_over_area(expl, area):
    """
    Explanation 'expl' over 'area', 
    a tuple of (x1, x2, y1, y2), starting and ending points of the bounding rectangle.
    We make two assumptions in this test:
    1. The model can classify the example image correctly.
    2. The area specified by the tester over the example image covers the predicted class correctly.
    """
    image = expl.image
    heatmap = expl.heatmap
    # fit heatmap over image
    # FIXME: could we use image.py/resize_over function?
    heatmap = heatmap.resize((image.width, image.height), resample=Image.LANCZOS)
    heatmap = np.array(heatmap)
    x1, x2, y1, y2 = area
    crop = heatmap[y1:y2, x1:x2] # row-first ordering

    # TODO: show image, heatmap, and overlay if test fails
    # https://stackoverflow.com/questions/13364868/in-pytest-how-can-i-figure-out-if-a-test-failed-from-request
    # https://docs.pytest.org/en/latest/example/simple.html#making-test-result-information-available-in-fixtures
    # https://stackoverflow.com/questions/35703122/how-to-detect-when-pytest-test-case-failed/36219273

    total_intensity = np.sum(heatmap)
    crop_intensity = np.sum(crop)
    p = total_intensity / 100 # -> 1% of total_intensity
    intensity = crop_intensity / p # -> intensity %
    assert 50 < intensity # at least 50% (need to experiment with this number)
    # Alternative:
    # remaining_intensity = total_intensity - intensity
    # assert remaining_intensity < total_intensity


# area = (x1, x2, y1, y2)
@pytest.mark.parametrize('area, targets', [
    ((54, 170, 2, 100), None), # focus on the dog (pick top prediction)
    ((44, 180, 130, 212), [imagenet_cat_idx]), # focus on the cat (supply prediction)
])
def test_image_classification(keras_clf, cat_dog_image, area, targets):
    # check explanation
    res = eli5.explain_prediction(keras_clf, cat_dog_image, targets=targets)
    assert_attention_over_area(res, area)
    
    # check formatting
    overlay = format_as_image(res)
    # import matplotlib.pyplot as plt; plt.imshow(overlay); plt.show()
    original = res.image
    # check external properties
    assert isinstance(overlay, Image.Image)
    assert overlay.width == original.width
    assert overlay.height == original.height
    assert overlay.mode == 'RGBA'


# TODO: test invalid argument to targets

# TODO: test invalid prediction ID

# TODO: test format_as_image with alpha_limit set to 0 -> should show no heatmap over the image.