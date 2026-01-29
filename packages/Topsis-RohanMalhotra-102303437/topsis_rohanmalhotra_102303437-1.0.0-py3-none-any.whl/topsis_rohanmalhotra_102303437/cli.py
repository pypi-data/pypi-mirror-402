import sys

from .core import TopsisError, topsis_from_file


def main() -> None:
    # expected: topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>
    argv = sys.argv
    if len(argv) != 5:
        print(
            "Error: Correct number of parameters required.\n"
            "Usage: topsis <InputDataFile> <Weights> <Impacts> <OutputResultFileName>"
        )
        raise SystemExit(1)

    _, input_path, weights_s, impacts_s, output_path = argv

    try:
        result = topsis_from_file(input_path, weights_s, impacts_s)
        result.to_csv(output_path, index=False)
        print(f"Success: Result written to {output_path}")
    except TopsisError as e:
        print(f"Error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
