from pathlib import Path
import pymupdf

pdfs = list(Path("data").glob("*Zovara*.pdf"))
print("found:", pdfs)

doc = pymupdf.open(pdfs[0])
page = doc[8]  # page 9 (0-based)

for t in page.find_tables():
    for row in t.extract()[:4]:
        print(row)