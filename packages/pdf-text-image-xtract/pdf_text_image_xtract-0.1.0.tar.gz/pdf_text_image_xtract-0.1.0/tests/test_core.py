from pdf_text_image_xtract import PDFTextImageExtractor
import time


def test_process():
    extractor = PDFTextImageExtractor("test_pdfs/policy_schedule.pdf")
    start_time = time.time()
    text_data, image_data = extractor.process()
    end_time = time.time()
    print(f"Processing time: {end_time - start_time} seconds")
    assert len(text_data) > 0
    assert len(image_data) > 0


def test_proess_s3():
    s3_extractor = PDFTextImageExtractor(
        "s3://pdf-test-bucket-123123132dsf/policy_schedule.pdf"
    )
    start_time = time.time()
    text_data, image_data = s3_extractor.process()
    end_time = time.time()
    print(f"Processing time (from s3): {end_time - start_time} seconds")
    assert len(text_data) > 0
    assert len(image_data) > 0


# def test_change_pdf_file():
#     extractor = PDFTextImageExtractor("test_pdfs/policy_schedule.pdf")
#     text_data1, image_data1 = extractor.process()
#     extractor.change_pdf_file("test_pdfs/discovery-insure-plan-guide.pdf")
#     text_data2, image_data2 = extractor.process()
#     assert len(text_data1) != len(text_data2) or len(image_data1) != len(
#         image_data2
#     )


def test_save_to_s3():
    extractor = PDFTextImageExtractor("test_pdfs/policy_schedule.pdf")
    text_data, image_data = extractor.process()
    # Test saving to S3 (this would require mocking or actual S3 access)
    # For now, just ensure the methods can be called without error
    responses1 = extractor.save_text_data_to_json_s3(
        "pdf-test-bucket-123123132dsf", "output/policy_schedule.json"
    )
    responses2 = extractor.save_images_to_s3("pdf-test-bucket-123123132dsf", "output/images")

    assert responses1
    assert responses2


def test_save_local():
    extractor = PDFTextImageExtractor("test_pdfs/policy_schedule.pdf")
    text_data, image_data = extractor.process()
    extractor.save_text_data_to_json("output/policy_schedule.json")
    extractor.save_images_to_disk("output/images/")
    assert True  # If no exceptions, the test passes
