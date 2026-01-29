import sys
import os
from topsis_manya_102303254.core import topsis_from_csv, TopsisError

HELP_TEXT = """\
Usage:
  topsis <filename.csv> <weights> <impacts>

Examples:
  topsis sample.csv "1,1,1,1" "+,-,+,+"
  topsis sample.csv 1,1,1,1 +,-,+,+

Notes:
- CSV must have header row and first column as ID/Model.
- All criteria columns must be numeric.
- Output file will be generated as: result.csv in the current directory.
"""

def main():
    # help command
    if len(sys.argv) == 2 and sys.argv[1] in ["/h", "-h", "--help"]:
        print(HELP_TEXT)
        return

    if len(sys.argv) != 4:
        print("Error: Incorrect parameters.\n")
        print(HELP_TEXT)
        sys.exit(1)

    file_path = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]

    if not file_path.lower().endswith(".csv"):
        print("Error: Only .csv file is supported.")
        sys.exit(1)

    if not os.path.isfile(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    try:
        result = topsis_from_csv(file_path, weights, impacts)

        out_name = "result.csv"
        result.to_csv(out_name, index=False)

        print("      TOPSIS RESULTS")
        print("-----------------------------\n")
        print(result.to_string(index=True))
        print(f"\nOutput saved to: {out_name}")

    except TopsisError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Unexpected failure: {e}")
        sys.exit(1)
