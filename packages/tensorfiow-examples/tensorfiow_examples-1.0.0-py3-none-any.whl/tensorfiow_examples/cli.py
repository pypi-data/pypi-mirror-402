from pathlib import Path

PROGRAMS = [
    ("1", "1.txt"),
    ("2", "2.txt"),
    ("3", "3.txt"),
    ("4", "4.txt"),
    ("5(a)", "5a.txt"),
    ("5(b)", "5b.txt"),
]

def main():
    print("\n====== TENSORFIOW EXAMPLES : RAW AI / ML CODES ======\n")

    base_dir = Path(__file__).parent / "raw"

    for title, filename in PROGRAMS:
        print(f"\n----- PROGRAM {title} -----\n")

        file_path = base_dir / filename

        if not file_path.exists():
            print(f"[ERROR] File not found: {filename}")
            continue

        print(file_path.read_text(encoding="utf-8"))

if __name__ == "__main__":
    main()
