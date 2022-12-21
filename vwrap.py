#!/usr/bin/env python3


import sys, math
from PIL import Image

from itertools import chain



step = 1


def print_help():
    print('Usage:\n')
    print('    vwrap input_images -- direction output_image width step\n');
    print('          input_images: list of input images')
    print('          direction   : direction of next tiles (up or down)')
    print('          output_image: result of wrapping around')
    print('                 width: width of the output image')
    print('                  step: next tile offset in pixels (1, 2 or 4)\n')
    sys.exit()


# wrap around the model1 tile into model2
def wraparound(model1, model2, new_images):
    tile = model1

    for i in range(8 // step - 1):
        new_im = Image.new('RGB', (8, 8))

        for x in range(8):
            for y in range(8):
                # Calculate the new y position for the pixel
                if direction == 'up':
                    new_y = y - (i + 1) * step
                else:
                    new_y = y + (i + 1) * step

                # wrap around
                if new_y >= height:
                    tile = model2
                    new_y %= height

                # Get the pixel at the current position
                pixel = tile.getpixel((x, y))

                # Set the pixel at the new position in the new image
                new_im.putpixel((x, new_y), pixel)

        # Add new tile to the list of new images
        new_images[i + 1].append(new_im)


if '--help' in sys.argv or len(sys.argv) < 4:
    print_help();

# get parameters even if the '--' separator is not specified.
if '--' in sys.argv:
    inputs = sys.argv[1:sys.argv.index('--')]
    try:
        direction, output, new_width, step = sys.argv[sys.argv.index('--') + 1:]
    except ValueError:
        print('** missing parameter **\n')
        print_help();
else:
    try:
        inputs = sys.argv[1:2]
        direction, output, new_width, step = sys.argv[2:5]
    except ValueError:
        print('** missing parameter **\n')
        print_help();

new_width = int(new_width)
step = int(step)

if not direction in ('up', 'down'):
    print('** direction should be "up" or "down" **\n')
    print_help();

if new_width == 0:
    print('** width should be a number greater than zero **\n')
    print_help();

if new_width % 8:
    print('** width should be divisible by 8 **\n')
    print_help();

if not step in [1, 2, 4]:
    print('** step should be 1, 2 or 4 **\n')
    print_help();

ntiles = 0
new_images = [[] for x in range(8 // step)]

# Open the original images
for file in inputs:
    im = Image.open(file)

    # Get the width and height of the image
    width, height = im.size

    for x_ in range(0, width, 8):
        for y_ in range(0, height, 8):
            tmp = im.crop((x_, y_, x_ + 8, y_ + 8));
            new_images[0].append(tmp)

            if height > 8 and y_ != height - 8:
                # Iterate over the number of new tiles to create
                for i in range(8 // step - 1):
                    new_im = im.crop((x_, y_ + i + step, x_ + 8, y_ + i + step + 8))

                    # Add new tile to the list of new images
                    new_images[i + 1].append(new_im)
            elif y_ == height - 8:
                # wrap around from last to first tile
                new_tile = wraparound(tmp, new_images[0][-1], new_images)
            else:
                # wrap around itself
                new_tile = wraparound(tmp, tmp, new_images)

    im.close()

# flatten the results
flatten = list(chain(*new_images))
new_height = math.ceil(len(flatten) * 8 / int(new_width)) * 8

# Create a new image to store the resulting tiles
result_im = Image.new('RGB', (new_width, new_height))

# Paste each new image into the result image
x = y = 0

for new_im in flatten:
    if x == new_width:
        x = 0
        y += 8
    result_im.paste(new_im, (x, y))
    x += 8

# Save the result image
result_im.save(output)
print('New image "%s" created from %i original tiles, resulting in a total of %i tiles in a %ix%i configuration.'
      % (output, len(new_images[0]), len(flatten), new_width, new_height))
