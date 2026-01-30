import pdfplumber
import json
import fitz  # PyMuPDF
from pathlib import Path
from threading import Thread
from .utils import (
    parse_s3_path,
    read_s3_object,
    save_as_json_to_s3,
    save_img_to_s3,
    is_path_s3,
)
import logging

logging.basicConfig(level=logging.INFO)

# use a class structure to encapsulate the functionality

'''
PDFTextImageExtractor class to extract text, tables, and images from PDF files,
supporting both local files and S3 paths.
'''

class PDFTextImageExtractor:
    def __init__(self, pdf_file: str):
        self.pdf_file = pdf_file
        self.data = []
        self.image_data = []

    def extract_text_and_tables(self) -> None:
        '''
        Extract text and tables from the PDF.        
        '''
        logging.info("Extracting text and tables...")

        with pdfplumber.open(self.pdf_file) if not is_path_s3(self.pdf_file) else pdfplumber.open(read_s3_object(*parse_s3_path(self.pdf_file), raw_bytes=False)) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                self.data.append(
                    {
                        "page": page_num,
                        "text": page.extract_text(),
                        "tables": page.extract_tables(),
                    }
                )

    def extract_images(self) -> None:
        '''
         Extract images from the PDF.        
        
        '''
        logging.info("Extracting images from pdf..")
        doc = fitz.open(self.pdf_file) if not is_path_s3(self.pdf_file) else fitz.open(stream=read_s3_object(*parse_s3_path(self.pdf_file)))

        for page_index in range(len(doc)):
            page = doc[page_index]
            images = page.get_images(full=True)
            page_images_data = []
            for _, img in enumerate(images):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                page_images_data.append(image_bytes)
            self.image_data.append({"page": page_index + 1, "images": page_images_data})

    def process(self):
        '''
         Processes the PDF to extract text, tables, and images.
        
        '''
        # process text and images in parallel
        text_thread = Thread(target=self.extract_text_and_tables)
        image_thread = Thread(target=self.extract_images)
        text_thread.start()
        image_thread.start()
        text_thread.join()
        image_thread.join()
        logging.info("Extraction of images, texts and tables has completed")
        return self.data, self.image_data
    def change_pdf_file(self, pdf_file: str) -> None:
        '''
        Change the PDF file to be processed.
    
        :param pdf_file: pdf file path
        :type pdf_file: str
        '''
        self.pdf_file = pdf_file
    def save_text_data_to_json(self, output_file: str) -> None:
        '''
        Save the extracted text and tables as JSON file to disk.
        
        :param output_file: Output file path
        :type output_file: str
        '''
        path = Path(output_file)
        path.parent.mkdir(parents=True, exist_ok=True) # create directories if not exist
        with path.open("w") as f:
            json.dump(self.data, f, indent=2)
        logging.info(f"Text data saved to {output_file}")

    def save_images_to_disk(self, output_dir: str) -> None:
        '''
         Save extracted images to disk.

        :param output_dir: Output directory
        :type output_dir: str
        '''

        for page_data in self.image_data:
            page_index = page_data["page"]
            for img_index, image_bytes in enumerate(page_data["images"]):
                path = Path(f"{output_dir}/page{page_index}_img/{img_index}.png")
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("wb") as f:
                    f.write(image_bytes)
        logging.info(f"Images saved to {output_dir}")

    def save_text_data_to_json_s3(self, bucket_name: str, object_key: str, aws_region: str = None) -> None:
        '''
         Save the extracted text and tables as JSON file on S3.
        
        :param bucket_name: Bucket name
        :type bucket_name: str
        :param object_key: 
        :type object_key: str
        :param aws_region: Description
        :type aws_region: str
        '''
        try:
            save_as_json_to_s3(self.data, bucket_name, object_key, aws_region)
            return True
        except Exception as e:
            logging.error(f"Error saving text data to S3: {e}")
            return False

    def save_images_to_s3(self, bucket_name: str, folder: str, aws_region: str = None) -> None:
        """
        Saves the extracted images to an S3 bucket

        :param bucket_name: name of the S3 bucket
        :type bucket_name: str
        :param folder: folder path in the S3 bucket to save images
        :type folder: str
        :param aws_region: AWS region
        :type aws_region: str
        :return: True if successful, else False
        :rtype: bool
        """
        try:
            for page_data in self.image_data:
             page_index = page_data["page"]
             for img_index, image_bytes in enumerate(page_data["images"]):
                save_img_to_s3(
                    image_bytes,
                    bucket_name,
                    f"{folder}/page{page_index}_img/{img_index}.png",
                    aws_region,
                )
            return True
        except Exception as e:
            logging.error(f"Error saving images to S3: {e}")
            return False