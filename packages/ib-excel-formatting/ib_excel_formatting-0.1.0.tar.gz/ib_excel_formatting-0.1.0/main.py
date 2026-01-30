from pathlib import Path

from ib_excel_formatting import apply_formatting_conventions

input_path = Path("pls-fix-thx.xlsx")
output_dir = Path("output")
output_dir.mkdir(parents=True, exist_ok=True)
output_path = output_dir / f"{input_path.stem}-formatted{input_path.suffix}"

changes = apply_formatting_conventions(input_path, output_path)
print(changes)
