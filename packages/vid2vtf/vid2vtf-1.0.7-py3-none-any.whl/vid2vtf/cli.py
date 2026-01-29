import argparse
import sys
import os
from importlib.metadata import version
try:
    __version__ = version("vid2vtf")
except Exception:
    __version__ = "ORD_CRY"
from vid2vtf import video_to_vtf
def main():
    if len(sys.argv) > 1:
        parser = argparse.ArgumentParser()
        parser.add_argument("--video")
        parser.add_argument("--fps", default=3)
        parser.add_argument("--width", default=256)
        parser.add_argument("--height", default=128)
        parser.add_argument("--output_filename", default=None)
        parser.add_argument("--output_dir", default=os.getcwd())


        args = parser.parse_args()
    
        video_to_vtf(args.video, fps=int(args.fps), width=int(args.width), height=int(args.height), output_filename=args.output_filename, output_dir=args.output_dir)
    else:
        print(f"vid2vtf : {__version__}. Please Use -h for help [vid2vtf -h]")

if __name__ == '__main__':
    main()   