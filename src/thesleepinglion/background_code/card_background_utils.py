# Utility functions to create the card background
import gi
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import GLib, GdkPixbuf

import numpy as np

def pixbuf_to_array(p):
    """Convert a GdkPixbuf to numpy array"""
    w,h,c,r=(p.get_width(), p.get_height(), p.get_n_channels(), p.get_rowstride())
    assert p.get_colorspace() == GdkPixbuf.Colorspace.RGB
    assert p.get_bits_per_sample() == 8
    if  p.get_has_alpha():
        assert c == 4
    else:
        assert c == 3
    assert r >= w * c
    a=np.frombuffer(p.get_pixels(),dtype=np.uint8)
    if a.shape[0] == w*c*h:
        return a.reshape( (h, w, c) )
    else:
        b=np.zeros((h,w*c),'uint8')
        for j in range(h):
            b[j,:]=a[r*j:r*j+w*c]
        return b.reshape( (h, w, c) )


def array_to_pixbuf(d:np.ndarray):
    """
    Convert numpy array to GdkPixbuf
    """
    image = GdkPixbuf.Pixbuf.new_from_bytes(GLib.Bytes(d.flatten().tobytes()),
                                            GdkPixbuf.Colorspace.RGB,
                                            True,
                                            8,
                                            d.shape[1],
                                            d.shape[0],
                                            4 * d.shape[1])
    return image

def rgb_to_lch(img: np.ndarray):
    '''
    Convert an array representing an image from RGB space to Lch space
    '''
    lab_array = np.array([[0.4124564, 0.3575761, 0.1804375],
                          [0.2126729, 0.7151522, 0.0721750],
                          [0.0193339, 0.1191920, 0.9503041]])
    output = np.copy(img).astype(np.float64)

    # Rescale in [0, 1] range
    output /= 255

    # sRGB to linear RGB
    mask = output <= 0.04045
    output[mask] /= 12.92
    output[~mask] = ((output[~mask] + 0.055) / 1.055)**2.4
    output[:, :, 3] = img[:, :, 3]

    # lRGB to CIEXYZ
    # Black magic !
    output[:, :, :3] = np.einsum('zr,mnr', lab_array, output[:, :, :3]) * 100
    output[:, :, 3] = img[:, :, 3]

    # CIEXYZ to CIELAB
    delta = 6 / 29
    Xn = 95.0489
    Yn = 100.0
    Zn = 108.8840

    lab = np.copy(output)
    lab[:, :, 0] /= Xn
    lab[:, :, 1] /= Yn
    lab[:, :, 2] /= Zn

    def f(a):
        mask = a > delta**3
        a[mask] = a[mask]**(1/3)
        a[~mask] = a[~mask] / 3 / delta**2 + 4/29
        return a
    for i in range(3):
        mask = lab[:, :, i] > delta**3
        lab[:, :, i][mask] = lab[:, :, i][mask]**(1/3)
        lab[:, :, i][~mask] = lab[:, :, i][~mask] / 3 / delta**2 + 4/29

    output[:, :, 0] = 116 * lab[:, :, 1] - 16
    output[:, :, 1] = 500 * (lab[:, :, 0] - lab[:, :, 1])
    output[:, :, 2] = 200 * (lab[:, :, 1] - lab[:, :, 2])

    # Lab to Lch
    r = np.sqrt(output[:, :, 1]**2 + output[:, :, 2]**2)
    theta = np.arctan2(output[:, :, 2], output[:, :, 1])

    output[:, :, 1] = r
    output[:, :, 2] = theta


    output[:, :, 3] = img[:, :, 3]
    return output

def lch_to_rgb(img: np.ndarray):
    '''
    Convert an array representing an image from Lch space to RGB space
    '''
    lab_array = np.array([[3.2404542, -1.5371385, -0.4985314],
                          [-0.9692660, 1.8760108, 0.0415560],
                          [0.0556434, -0.2040259, 1.0572252]])

    output = np.copy(img)

    # Lch to Lab
    r = output[:, :, 1]
    theta = output[:, :, 2]
    output[:, :, 1], output[:, :, 2] = r * np.cos(theta), r * np.sin(theta)

    # CIELAB to CIEXYZ
    delta = 6 / 29
    Xn = 95.0489
    Yn = 100.0
    Zn = 108.8840
    def f(a):
        b = np.copy(a)
        mask = a > delta
        b[mask] = a[mask]**3
        b[~mask] = 3 * delta**2 * (a[~mask] - 4/29)
        return b

    lab = np.copy(output)
    lab[:, :, 0] = (lab[:, :, 0] + 16) / 116

    output[:, :, 0] = Xn * f(lab[:, :, 0] + lab[:, :, 1] / 500)
    output[:, :, 1] = Yn * f(lab[:, :, 0])
    output[:, :, 2] = Zn * f(lab[:, :, 0] - lab[:, :, 2] / 200)

    # CIEXYZ to lRGB
    output[:, :, :3] = np.einsum('zr,mnr', lab_array, output[:, :, :3] / 100)

    # lRGB to RGB
    mask = output <= 0.0031308049535603713
    output[mask] *= 12.92
    output[~mask] = 1.055 * output[~mask]**(1/2.4) - 0.055
    output *= 255
    output = np.minimum(255, np.maximum(output, 0))
    output[:, :, 3] = img[:, :, 3]
    output = output.astype(np.uint8)

    return output
