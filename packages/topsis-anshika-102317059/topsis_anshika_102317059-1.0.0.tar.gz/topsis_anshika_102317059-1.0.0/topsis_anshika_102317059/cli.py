import sys
from .topsis_logic import run_topsis, TopsisError

def main():
    if len(sys.argv) != 5:
        print("Usage:")
        print("topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        print('Example: topsis data.csv "1,1,1,2" "+,+,-,+" output-result.csv')
        sys.exit(1)

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    try:
        run_topsis(input_file, weights_str, impacts_str, output_file)
        print(f"TOPSIS completed ✅ Output saved to: {output_file}")
    except TopsisError as e:
        print("Error:", str(e))
        sys.exit(1)
