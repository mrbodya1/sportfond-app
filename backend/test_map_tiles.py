import gzip
import unittest
from unittest.mock import patch
import map_tiles

class Response:
    status=206
    def __init__(self,data,start,total):
        self.data=data;self.headers={"Content-Range":f"bytes {start}-{start+len(data)-1}/{total}"}
    def read(self,*args):return self.data
    def __enter__(self):return self
    def __exit__(self,*args):pass

class TileTests(unittest.TestCase):
    def setUp(self):
        map_tiles._cache.clear();map_tiles._size=0
    def test_ranges_are_joined_before_gzip_decode_and_cached(self):
        plain=bytes(range(256))*300
        packed=gzip.compress(plain,compresslevel=0)
        calls=[]
        def open_resource(req,timeout):
            calls.append(req.full_url)
            start=int(req.get_header("Range").split("=")[1].split("-")[0])
            return Response(packed[start:start+16384],start,len(packed))
        with patch("map_tiles.urllib.request.urlopen",side_effect=open_resource):
            path="/planet/20261101_080013_pt/13/5666/2332.pbf"
            self.assertEqual(map_tiles.resource(path)[0],plain)
            count=len(calls);map_tiles.resource(path)
            self.assertEqual(len(calls),count)
            self.assertGreater(count,1)
    def test_rejects_arbitrary_urls_and_invalid_coordinates(self):
        with patch("map_tiles.urllib.request.urlopen") as request:
            for path in ["https://example.com","/planet/20261101_080013_pt/2/9/1.pbf","/fonts/../../secret/0-255.pbf","/planet/20261101_080013_pt/99/0/0.pbf"]:
                with self.assertRaises(ValueError):map_tiles.resource(path)
            request.assert_not_called()
    def test_rejects_mismatched_range(self):
        with patch("map_tiles.urllib.request.urlopen",return_value=Response(b"bad",1,10)):
            with self.assertRaises(RuntimeError):map_tiles.resource("/planet/20261101_080013_pt/1/1/1.pbf")
    def test_fonts_use_fixed_github_source(self):
        with patch("map_tiles.urllib.request.urlopen",return_value=Response(b"font",0,4)) as request:
            self.assertEqual(map_tiles.resource("/fonts/Noto%20Sans%20Regular/0-255.pbf")[0],b"font")
            self.assertTrue(request.call_args[0][0].full_url.startswith("https://raw.githubusercontent.com/maplibre/demotiles/gh-pages/font/"))

if __name__=="__main__":unittest.main()
