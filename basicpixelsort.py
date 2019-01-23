from functools import reduce
from PIL import Image

import multiprocessing
from itertools import product

import numpy as np
import random
import time

import sys

start = time.time()


# Sort pixels in a rectangle section of the image with given size.
# im = input image.
# size = pixel dimensions of area to be sorted.
def kernel_sort(im, size):
    # Loop through pixels one rectangle at a time.
    for x in range(int(im.size[0]/size[0])):
        for y in range(int(im.size[1]/size[1])):
            # Extract pixels in rectangle.
            block = im.crop((x*size[0], y*size[1],
                            (x+1)*size[0], (y+1)*size[1]))
            pixels = list(block.getdata())

            # Sort pixels by rgb, order by more red, then more green, then more
            # blue.
            pixels = sorted(pixels, key=lambda rgb:
                                        255*255*rgb[0]+rgb[1]*255+rgb[2])
            
            # Convert pixels to image for pasting.
            block = Image.new(block.mode, block.size)
            block.putdata(pixels)

            # Paste sorted rectangle to current block location.
            im.paste(t, (x*size[0], y*size[1],
                        (x+1)*size[0], (y+1)*size[1]))
    
    return im


# Horizontally sorts image pixels for each row.
def horizontal_sort(im):
    # Loop through each row.
    for y in range(im.size[1]):
        # Extract pixels in row.
        row = im.crop((0, y, im.size[0], y+1))
        pixels = list(row.getdata())

        # Sort pixels by rgb, order by more red, then more green, then more blue.
        pixels = sorted(c, key=lambda rgb:
                               255*255*rgb[0]+rgb[1]*255+rgb[2])

        # Convert pixels to image for pasting.
        row = Image.new(row.mode, row.size)
        row.putdata(pixels)

        # Paste sorted row to current row.
        im.paste(row, (0, y, im.size[0], y+1))
        
    return im


# Sort image pixels for each column.
def vertical_sort(im):
    # Loop through each column.
    for x in range(im.size[0]):
        # Extract pixels in column.
        column = im.crop((x, 0, x+1, im.size[1]))
        pixels = list(column.getdata())

        # Sort pixels by rgb, order by more red, then more green, then more blue.
        pixels = sorted(pixels, key=lambda rgb:
                                    255*255*rgb[0]+rgb[1]*255+rgb[2])

        # Convert pixels to image for pasting.
        column = Image.new(column.mode, column.size)
        column.putdata(pixels)

        im.paste(column, (x, 0, x+1, im.size[1]))

    return im


# Color in each horizontally connected non-filtered,
# color=rgb(255,255,255)), pixels as same color randomly.
def color_filtered(im, filtered):
    # Extract pixels from image and the pixels of the image filter.
    pixels = list(im.getdata())
    filtered_pixels = list(filtered.getdata())

    # Loop through each row of image.
    for y in range(im.size[1]):
        # Generate random rgb color.
        color = (random.randrange(255),
                 random.randrange(255),
                 random.randrange(255))

        for x in range(im.size[0]):
            # Extract the pixel rgb value.
            pixel = filtered_pixels[x+im.size[0]*y]

            # Generate new color if position is on a filtered pixel else fill in
            # the same color.
            if pixel == (0,0,0):
                color = (random.randrange(255),
                         random.randrange(255),
                         random.randrange(255))
            else:
                pixels[x+im.size[0]*y] = color

    # Convert pixels back into image.
    im = Image.new(im.mode, im.size)
    im.putdata(pixels)
    
    return im


# Sort pixels horizontally connected to each other by their rgb value.
def sort_filtered(im, filtered):
    # Extract pixels from image and the pixels of the image filter.
    pixels = list(im.getdata())
    filtered_pixels = list(filtered.getdata())
    
    connected = []

    # Loop through each row of image.
    for y in range(im.size[1]):
        # Sort horizontally connected pixels by their rgb value, order by
        # more red, then more green, then more blue.
        if len(connected) > 0:
            connected = sorted(connected, key=lambda rgb:
                                              255*255*rgb[0]+rgb[1]*255+rgb[2])

            # Replace unsorted pixels in image with sorted pixels.
            for i in range(len(connected)):
                pixels[x+y*im.size[0]-len(connected)-1+i] = connected[i]

            # Empty list of horizontally connected pixels.
            connected = []

        # Loop through each pixel in row.
        for x in range(im.size[0]):
            # Extract the rgb pixel value of the filtered image pixel.
            pixel = filtered_pixels[x+im.size[0]*y]

            # Sort and place the horizontally connected pixels when the
            # current pixel is filtered.
            if pixel == (0,0,0):
                if len(connected) > 0:
                    # Sort pixels by rgb value, order by more red, then more
                    # green, then more blue.
                    connected = sorted(connected, key=lambda rgb: 255*255*rgb[0] + rgb[1]*255 + rgb[2])

                    # Replace the unsorted pixels with sorted pixels.
                    for i in range(len(connected)):
                        pixels[x+y*im.size[0]-len(connected)-1+i] = connected[i]

                    # Empty list of horizontally connected pixels.
                    connected = []
            else:
                # The current pixel is unfiltered, rgb color (255,255,255),
                # so append it to the list of horizontally connected pixels.
                connected.append(pixels[x+im.size[0]*y])

    # Convert pixels back into image.
    img = Image.new(im.mode, im.size)
    img.putdata(pixels)
    
    return img


# Filter pixels into either filtered, rgb value (0,0,0), or unfiltered pixels,
# rgb value (255,255,255), depending on if they are inside or outside the
# specified light intensity range.
def filter_intensity(im, max_intensity):
    # Extract pixels in image.
    pixels = list(im.getdata())

    # Loop through all pixels.
    for i in range(len(pixels)):
        # Measure intensity as the sum of all the rgb values.
        intensity = pixels[i][0] + pixels[i][1] + pixels[i][2]

        # Filter out bright and dark intensity pixels.
        if (intensity < max_intensity or intensity >= (255*3 - max_intensity)):
            # RGB value for filtered pixels.
            pixels[i] = (0, 0, 0)

        else:
            # RGB value for unfiltered pixels.
            pixels[i] = (255, 255, 255)

    # Convert pixels back into image.
    im = Image.new(im.mode, im.size)
    im.putdata(pixels)
    
    return im


# Perform pixelsorting on the image with the given intensity for the filter.
# im - image to sort.
# intensity - what brightness pixels will be filtered out.
# i - thread index.
# returns - the resulting pixelsorted area by this thread.
def pixelsort(im, intensity, i, returns, sort=True):
    im_filter = filter_intensity(im, intensity)
    if sort:
        im = sort_filtered(im, im_filter)
    else:
        im = color_filtered(im, im_filter)
    returns[i] = im
    return im

# Performs multithreaded pixelsorting on given image.
# im - image to sort.
# intensity - what brightness pixels will be filtered out.
# splits - # of processes/how many sections the image should be split up in.
# sort - sort pixels, if false the filtered areas will simply be colored in
# instead.
def multiprocessed_pixelsort(im, intensity, splits, sort=True):
    # Split image into parts, pixelsort each part,
    # pixelsort borders, combine to one image.
    w,h = im.size
    img = []

    # Determine area to sort for each thread.
    for i in range(splits):
        img.append(im.crop((0, int(h/splits)*i, w, int(h/splits)*(i+1))))
   
    manager = multiprocessing.Manager()
    returns = manager.dict()
    jobs = []

    for i in range(len(img)):
        p = multiprocessing.Process(target=pixelsort, args=(img[i], intensity, i, returns, sort))
        p.start()
        jobs.append(p)

    for i in jobs:
        i.join()

    image = Image.new("RGB", (w, h))
    for i in range(splits):
        image.paste(returns[i], (0, int(h/splits)*i, w, int(h/splits)*(i+1)))
    
    return image


# Prints command usage.
def print_help():
    print("Usage: python basicpixelsort.py image.[jpg, png, etc] intensity " +
            "rotation [coloring, pixelsorting] no_of_threads")


if __name__ == '__main__':

    # Determine if the correct number of parameters were given.
    if (len(sys.argv) != 6):
        print_help()
        sys.exit()

    im = Image.open(sys.argv[1])
    im = im.rotate(int(sys.argv[3]), expand=True)
    
    image = multiprocessed_pixelsort(im, int(sys.argv[2]), int(sys.argv[5], False))
    image = image.rotate(-int(sys.argv[3]))
    
    # Print elapsed time.
    print(time.time()-start)
    
    image.show()
