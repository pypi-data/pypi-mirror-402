import subprocess
import sys


def main() -> None:
    subprocess.run(["cargo", "test"], check=True)
    subprocess.run([sys.executable, "-m", "pytest", "tests/python"], check=True)


if __name__ == "__main__":
    main()
