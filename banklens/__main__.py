from .pipeline import run
import sys

run(sys.argv[1:] or None)
