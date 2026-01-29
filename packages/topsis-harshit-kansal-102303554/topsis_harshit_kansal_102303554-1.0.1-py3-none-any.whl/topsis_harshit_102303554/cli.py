import sys
from .core import run_topsis, TopsisError


def main():
    if len(sys.argv) != 5:
        print("Usage:")
        print("topsis-hk <input_csv> <weights> <impacts> <output_csv>")
        print('Example: topsis-hk data.csv "1,1,1,2" "+,+,-,+" result.csv')
        sys.exit(1)

    _, input_csv, weights, impacts, output_csv = sys.argv

    try:
        run_topsis(input_csv, weights, impacts, output_csv)
        print("TOPSIS completed successfully!")
        print(f" Output file generated: {output_csv}")
    except TopsisError as err:
        print(f" Error: {err}")
        sys.exit(1)
