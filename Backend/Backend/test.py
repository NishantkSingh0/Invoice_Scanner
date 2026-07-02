# from sheet import fill_sheet

# json_data = {
#     "Name": "John Doe",
#     "RollNum": "12345",
#     "Course": "Computer Science",
#     "Collage": "XYZ University"
# }
# fill_sheet(json_data)

# from llm import llama4Test
# print("Testing llm with hello text")
# llama4Test()


# from utils import generate_job_card_pdf
# import base64

# with open("./a.png", "rb") as image_file:
#     base64_string = base64.b64encode(image_file.read()).decode("utf-8")

# generated_pdf_path = generate_job_card_pdf({
#     "client_name": "ABC Interior",
#     "po_number": "PO-123",
#     "item_name": "C Shape Side Table",
#     "quantity": 5,
#     "card_date": "11-Jun-2026",
#     "Specifications": "C shape side table with veneer finish.",
#     "ref_image": base64_string
# })