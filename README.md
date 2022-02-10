tilegen.py
==========

Splits big image into smaller tiles, checks MD5 signature for repeated images, and delete them if found. After the purge, a new smaller tileset is created. **Requires ImageMagick to work.** Usage is best explained by example:

``` 
./tilegen.py ./sample/maniac.png 16x16 result/tile 256x192
```

will create `result` directory and, inside it, tiles from `tile0000.png` to `tilennnn.png` where `nnnn` is the number of times a 16x16 tile fits inside `sample/maniac.png`. Identical tiles are removed if found, so the actual number of tiles may be smaller than that. A list of removed tiles called `removed.txt` will be created inside `result` along with a *Tiled*-compatible `map.json` and a new tileset image called `tileset256x192.png`.
