# PDF Text & Image Extractor

A robust Python-based utility designed to extract text, tables, and images from PDF documents. This tool supports both **local file systems** and **Amazon S3**, utilizing multi-threading to speed up the extraction process.

## 🚀 Features

* **Hybrid Storage Support:** Seamlessly process PDFs from local paths or S3 buckets (`s3://...`).
* **Comprehensive Extraction:**
    * **Text:** Full-page text extraction.
    * **Tables:** Structured table data.
    * **Images:** High-fidelity image extraction.
* **Multi-threaded Performance:** Extracts text and images in parallel to significantly reduce processing time.
* **Cloud Ready:** Built-in methods to save results directly back to S3 as JSON and PNG files.

---

## 🛠 Installation

### 1. Clone the repository
```bash
pip install pdf_text_image_xtract
```
## Basic Example Usage

```python

from pdf_text_image_xtract import PDFTextImageExtractor

# Initialize the extractor with a local path
extractor = PDFTextImageExtractor("documents/report.pdf")

# Process the PDF (runs text and image extraction in parallel)
extractor.process()

# Save results to local disk
extractor.save_text_data_to_json("output/data.json")
extractor.save_images_to_disk("output/extracted_images")

```

## Cloud Example (AWS S3)

```python
from pdf_text_image_xtract import PDFTextImageExtractor

# Initialize with an S3 path
s3_path = "s3://my-bucket/input/document.pdf"
extractor = PDFTextImageExtractor(s3_path)

# Extract data
extractor.process()

# Upload results directly back to S3
extractor.save_text_data_to_json_s3(
    bucket_name="my-bucket",
    object_key="results/text_data.json",
)

extractor.save_images_to_s3(
    bucket_name="my-bucket",
    folder="results/images",
)

```