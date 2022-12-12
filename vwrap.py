#!/usr/bin/env python3


import sys, math
from PIL import Image


if '--help' in sys.argv or len(sys.argv) < 4:
    print("usage: vwrap input_images -- output_image width step");
    sys.exit()

# get parameters even if the '--' separator is not specified.
if '--' in sys.argv:
    inputs = sys.argv[1:sys.argv.index('--')]
    output, new_width, step = sys.argv[sys.argv.index('--') + 1:]
else:
    inputs = sys.argv[1:2]
    output, new_width, step = sys.argv[2:4]

new_width = int(new_width)
step = int(step)

if new_width == 0:
    print('width should be a number greater than zero.')
    sys.exit()

if new_width % 8:
    print('width should be divisible by 8.')
    sys.exit()

if not step in [1, 2, 4]:
    print('step should be 1, 2 or 4.')
    sys.exit()

tiles = 0
new_images = []

# Open the original images
for file in inputs:
    im = Image.open(file)

    # Get the width and height of the image
    width, height = im.size

    for y_ in range(0, height, 8):
        for x_ in range(0, width, 8):
            tmp = im.crop((x_, y_, x_ + 8, y_ + 8));
            new_images.append(tmp)
            tiles += 1

            # Iterate over the number of new images to create
            for i in range(8 // step - 1):
                # Create an empty image with the same size as the original
                new_im = Image.new("RGB", (8, 8))

                # Iterate over the width and height of the image
                for x in range(8):
                    for y in range(8):
                        # Calculate the new y position for the pixel
                        new_y = (y - 1 - i) % height
    
                        # Get the pixel at the current position
                        #print('x,y = %i, %i' % (x, y), tmp.size)
                        pixel = tmp.getpixel((x, y))

                        # Set the pixel at the new position in the new image
                        #print(x, new_y, new_im.size)
                        new_im.putpixel((x, new_y), pixel)

                # Add original and new tile to the list of new images
                new_images.append(new_im)
    im.close()

new_height = math.ceil(len(new_images) / int(new_width)) * 8

# Create a new image to store the resulting tiles
result_im = Image.new("RGB", (new_width, new_height))

# Paste each new image into the result image
x = y = 0

for new_im in new_images:
    if x == new_width:
        x = 0
        y += 8
    result_im.paste(new_im, (x, y))
    x += 8

# Save the result image
result_im.save(output)
print('New image "%s" created from %i original tiles, resulting in a total of %i tiles.' % (output, tiles, len(new_images)))
