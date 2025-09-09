import sys
import os

grandparent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

if grandparent_dir not in sys.path:
    sys.path.insert(0, grandparent_dir)
