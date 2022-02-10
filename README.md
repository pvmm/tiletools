tilegen.py
==========

Splits big image into smaller tiles and checks MD5 signature for repeated images and delete them if found. **Requires ImageMagick to work.** Usage is best explained by example:

``` 
./tilegen.py big_image.png 16x16 directory/tile
```

will create `directory` and, inside it, tiles from `tile0000.png` to `tilennnn.png` where `nnnn` is the number of times a 16x16 tile fits inside `big_image.png`. A list of removed files called `removed.txt` will be created inside `directory` if any file was removed.

TODO
----

A different script that joins the tiles together into a tileset, but the repeated tiles are removed.
