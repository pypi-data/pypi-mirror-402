import sys
from .topsis import validate_and_load, run_topsis, TopsisError


def main():
    if len(sys.argv) != 5:
        print("Usage:")
        print("  topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        print("Example:")
        print('  topsis data.csv "1,1,1,2" "+,+,-,+" output-result.csv')
        sys.exit(1)

    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]

    try:
        df, criteria_cols, w, im = validate_and_load(input_file, weights, impacts)
        out = run_topsis(df, criteria_cols, w, im)
        out.to_csv(output_file, index=False)
        print(f"Success: result stored in {output_file}")
    except TopsisError as e:
        print(f"Error: {e}")
        sys.exit(1)
