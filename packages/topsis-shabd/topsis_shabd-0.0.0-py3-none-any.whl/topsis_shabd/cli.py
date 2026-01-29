import sys
from .core import topsis, error_exit

def main():
    if len(sys.argv) != 5:
        error_exit(
            "Usage: topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>"
        )

    _, input_file, weights, impacts, output_file = sys.argv
    topsis(input_file, weights, impacts, output_file)
