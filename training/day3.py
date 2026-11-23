import pymupdf
from pathlib import Path

# doc = pymupdf.open("training/report.pdf")
# print(doc.page_count)        # kul pages

# page = doc[0]                # pehla page (index 0 se shuru)
# text = page.get_text()       # page ka saara text, ek string mein
# print(text[:500])       # sirf pehle 500 characters


# found = page.find_tables()
# if found is not None:
#     print(len(found.tables))

#     for t in found.tables:
#         rows = t.extract()
#         print(rows[:3])


# extract images and chart

doc = pymupdf.open("training/pdfs/executive_report.pdf")
out = Path("training/images")
out.mkdir(exist_ok=True)

for page_index in range(doc.page_count):
    page = doc[page_index]
    images = page.get_images(full = True)
    print(f"Page {page_index + 1}: {len(images)} images")
    
    for n, img in enumerate(images):
        xref = img[0]
        info = doc.extract_image(xref)
        file_name= f"page{page_index + 1}_img.{info["ext"]}"
        (out / file_name).write_bytes(info["image"])
        print(f"saved {file_name}")
    


# mkdir(exist_ok=True): folder bana deta hai, aur pehle se ho to error nahi deta.
# get_images page ki embedded images ki list deta hai. len(...) se ginti pata chalti hai.
# get_pixmap(dpi=150) page ko picture bana deta hai. DPI jitna zyada, picture utni saaf, par file bhi bhaari.
# out / "page1.png": Path mein / se folder aur file jud jaate hain.