import os
import random
import sys
from PIL import Image
from openai import OpenAI
import fitz # PyMuPDF
import base64
import json   

def detect_file_type(inputfile):
    """
    Detect the file type of the input file.
    Args:
        inputfile (str): Path to the input file.
    Returns:                
        str: File type (e.g., 'pdf', 'docx', 'pptx', etc.).
    """
    filetype = None
    if inputfile.endswith('.pdf'):
        filetype = 'pdf'
    elif inputfile.endswith('.pptx') or inputfile.endswith('.ppt'):
        filetype = 'pptx'
    else:
        raise ValueError("Unsupported file type: " + inputfile)
    return filetype


def convert_to_pdf(inputfile,outputdir):
    """
    Convert a file to PDF using LibreOffice.
    Args:
        inputfile (str): Path to the input file.
        outputdir (str): Directory to save the converted PDF file.
    Returns:
        str: Path to the converted PDF file.
    """
    filetype = detect_file_type(inputfile)
    if filetype == 'pdf':
        """ copy input pdf to output directory and return the path"""
        os.system("cp "+inputfile+" "+outputdir+"/"+os.path.basename(inputfile))
        return outputdir + "/" + os.path.basename(inputfile)
    elif filetype == 'pptx' or filetype == 'ppt':
        """ convert pptx to pdf using libreoffice"""
        idx = random.randint(1, 100000)
        #outfilepath = outputdir+"/"+os.path.basename(inputfile).split(".")[0]+".pdf"
        os.system("soffice --headless -env:UserInstallation=file:///tmp/libreoffice-unique-profile-"+str(idx)+" --convert-to pdf "+inputfile+" --outdir "+outputdir)
        os.system("rm -rf /tmp/libreoffice-unique-profile-"+str(idx))
        return outputdir + "/" + os.path.basename(inputfile).split(".")[0] + ".pdf"


def pdf_to_text(inputpdffile,textdir):
    """
    Convert a PDF file to text using pdftotext.
    Args:
        inputfile (str): Path to the input PDF file.
    Returns:
        text file path
    """
    os.system("pdftotext -layout "+inputpdffile+" "+textdir+"/"+os.path.basename(inputpdffile).split(".")[0]+".txt")
    return textdir + "/" + os.path.basename(inputpdffile).split(".")[0] + ".txt"



def categorize_pages(input_file):#, output_dir, chunk_size=2000):
    """
    Categorize pages of a PDF file into chunks of a specified type.
    Args:
        input_file (str): Path to the input PDF file.
    """
    #print(input_file)
    # Split the file into pages and add page numbers  
    page_break = "\f"  # pdftotext uses '\f' to separate pages in the text file  
    with open(input_file, "r") as f:  
        content = f.read()  
  
    pages = content.split(page_break)
    titlepage = pages[0]
    pages = pages[1:]  # Exclude the first page (title page)
    #print(pages[0])
    alltext = ""    
    for idx,pg in enumerate(pages):
        alltext = alltext + "page number: " +str(idx) + "text: "+ pg[:100]+ "\n"
    
    client = OpenAI(api_key='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')
    prompt = """  
    You will be provided with a text string containing content from multiple pages of a slide deck. Each section is separated by page numbers. The slide deck is related to a submission made by a candidate for the SI certification exam on MongoDB. The slide deck includes various sections, and your task is to identify the page numbers containing the "Current Architecture" and "Proposed Architecture" based on the text.  
    
    Instructions:  
    1. Return the page number for "Current Architecture" and "Proposed Architecture" in the following strict format: Current Architecture:<page number>, Proposed Architecture:<page number>.  
    2. If there are multiple pages encountered for "Current Architecture" and "Proposed Architecture", return only the first occurrence for each.
    3. If there is no Current or Proposed Architecture in the text, return NA instead of a page number in this format: Current Architecture:NA, Proposed Architecture:<page number>.  
    4. Ensure your output strictly adheres to the format provided in the example.  
    
    Example output:  
    Current Architecture:5, Proposed Architecture:6

    """  
    final_prompt = prompt + "\n\n Here is the input string- " + alltext
    current_architecture_page_flag = False
    proposed_architecture_page_flag = False
    current_architecture_page_number = "NA"
    proposed_architecture_page_number = "NA"
    try:
        response = client.responses.create(
            model="gpt-4o-mini", # Use a current, cost-effective model
            input=[
                {"role": "user", "content": final_prompt}
            ],
            max_output_tokens=100, # Limit the response length
        )
    
        #print("Model Response:")
        #print(response.output_text)
        final_response = response.output_text
        current_architecture_page_number = final_response.split(",")[0].split(":")[1].strip()
        proposed_architecture_page_number = final_response.split(",")[1].split(":")[1].strip()

        if current_architecture_page_number != "NA":
            print(f"Current Architecture found on page number: {current_architecture_page_number}")
            current_architecture_page_flag=True
            current_architecture_page_number=int(current_architecture_page_number) + 2 # adjusting for title page and 0 indexing
        else:
            print("Current Architecture not found in the document.")  

        if proposed_architecture_page_number != "NA":

            print(f"Proposed Architecture found on page number: {proposed_architecture_page_number}")
            proposed_architecture_page_flag = True
            proposed_architecture_page_number=int(proposed_architecture_page_number) + 2 # adjusting for title page and 0 indexing
        else:
            print("Proposed Architecture not found in the document.")
        return {"current_architecture_page_flag": current_architecture_page_flag,
                "current_architecture_page_number": current_architecture_page_number,
                "proposed_architecture_page_flag": proposed_architecture_page_flag,
                "proposed_architecture_page_number": proposed_architecture_page_number}      
    except Exception as e:
        print(f"An error occurred: {e}")
        return {"current_architecture_page_flag": current_architecture_page_flag,
                "current_architecture_page_number": current_architecture_page_number,
                "proposed_architecture_page_flag": proposed_architecture_page_flag,
                "proposed_architecture_page_number": proposed_architecture_page_number}

def get_architecture_images(pdf_inputfile,pages_to_be_converted_to_inmage,outputdir):
    """
    Convert specified pages of a PDF file to images using PyMuPDF.
    Args:
        pdf_inputfile (str): Path to the input PDF file.
        pages_to_be_converted_to_inmage (list): List of page numbers to be converted to images.
        outputdir (str): Directory to save the converted image files.
    Returns:
        list: List of paths to the converted image files.
    """
    try:
        #get name of pdf file without extension
        pdf_name = os.path.basename(pdf_inputfile).split(".")[0]
        doc = fitz.open(pdf_inputfile)
        image_files = []
        for page_num in pages_to_be_converted_to_inmage:
            page = doc.load_page(page_num)  # Page numbers are zero-based
            pix = page.get_pixmap()
            image_path = os.path.join(outputdir, f"{pdf_name}_page_{page_num + 1}.jpg")
            pix.save(image_path)
            #resize image
            image = Image.open(image_path)
            image = image.resize((224, 180))
            image.save(image_path)
            image_files.append(image_path)
        doc.close()
        return image_files
    except Exception as e:
        print(f"An error occurred while converting pages to images: {e}")
        return []

  
# Encode your local image as Base64  
def image_to_base64(image_path):  
    with open(image_path, "rb") as image_file:  
        # Read the binary data and encode it as base64  
        img_base64 = base64.b64encode(image_file.read()).decode('utf-8')  
        return f"data:image/jpeg;base64,{img_base64}"  # Add the Base64 header for JPEG  



def deck_intelligence_tool(inputtextfile,imagesbase64list):
    """
    Use LLM to analyze the deck and provide intelligence.
    Args:
        inputtextfile (str): Path to the input text file.
        imagesbase64list (list): List of Base64 encoded images.
    Returns:
        str: Intelligence analysis result.
    """
    # Split the file into pages and add page numbers  
    page_break = "\f"  # pdftotext uses '\f' to separate pages in the text file  
    with open(inputtextfile, "r") as f:  
        content = f.read()  
  
    pages = content.split(page_break)
    #titlepage = pages[0]
    text = " ".join(pages[1:])  # Exclude the first page (title page)
      
    client = OpenAI(api_key='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')
    prompt = """  
    You are tasked with reviewing and evaluating a deck presentation submitted by a candidate for the MongoDB SI Architect certification. The submission includes the text extracted from each slide of the candidate's presentation along with optional current and proposed architecture block diagrams. The case study could be based on either an existing project (completed or ongoing) or a new ideation (greenfield application). Your evaluation should assess whether the presentation meets the following basic components:    
    
    1. **Problem Statement**: Does the deck provide a clear and explicit problem statement explaining the use case?    
    2. **3 Whys**: Does the presentation answer the following key questions:    
    - Why is the project worth pursuing?    
    - Why should it be addressed now?    
    - Why is MongoDB the best choice for solving this problem?    
    3. **Current State (For Existing Applications)**:    
    - Does the deck explain the current state of the project, including the visualized current architecture?    
    4. **Future State**:    
    - Does the deck explain the future state of the application using MongoDB and provide a clearly visualized proposed architecture?    
    
    Here are the specific criteria for the evaluation and JSON population:  
    
    - **Recommendation**:  
    - Choose **Approve** if all basic components are sufficiently presented.  
    - Choose **Resubmit** if there are missing components, such as "Why Now" or missing architecture diagrams.  
    - Choose **Human Review** if the submission is too complex to validate or missing substantial information.    
    - **AI Score**: Rate the submission on a scale of 10 based on completeness, clarity, and adherence to MongoDB SI certification guidelines.    
    - **High-Level Summary**: Include short metadata on application type, domain, current database (if applicable), whether the project is ongoing, and a concise summary of the use case in 3–4 lines.    
    - **Details**: If the submission requires resubmission, explicitly list the missing information. Be precise (e.g., "Current architecture block diagram is missing" if it is an existing application).    
    - **Supplementary Response**:    
    - For **Approve**: Provide a congratulatory message for completing the MongoDB SI Architect Certification (e.g., "Congratulations on completing your certification! Your submission demonstrates a strong understanding of MongoDB's capabilities. You can share this achievement publicly.").    
    - For **Resubmit**: Provide a polite resubmission request highlighting the missing information (e.g., "Your submission is valuable, but it requires additional clarity around [insert missing components]. Please revise and resubmit to proceed.").    
    
    Your task is to evaluate the submission based on the above components and generate an output in **JSON format**, must adhering to the following structure:    
    
    {  
    "overview": {  
        "recommendation": "Approve/Resubmit/Human Review",  
        "aiScore": "x/10",  
        "highLevelSummary": {  
        "applicationType": "Existing/New",  
        "domain": "FinancialServices/Insurance/Manufacturing/etc.",  
        "currentDatabase": "Oracle/Postgres/etc. (if modernization use case)",  
        "isOngoingProject": "yes/no",  
        "summary": "(3–4 sentences summarizing the use case and the project details)"  
        }  
    },  
    "details": {  
        "missingInformation": "(If Resubmit) Explicitly list what is missing—e.g., 'Why Now is not explained' or 'Current architecture block diagram is missing')"  
    },  
    "supplementary": {  
        "responseToUser": "(Customized response based on the recommendation—either a congratulatory message for approval on completing MongoDB SI Architect Certification that can be shared publicly, or a request for resubmission highlighting what's missing)"  
    }  
    }  
    
    Use the extracted text and diagrams provided in the submission to form your evaluation and ensure your response is tailored to the candidate’s case study, returns only the json output and nothing else.
    """  
    final_prompt = prompt + "\n\n Here is the presentation text- " + text
    # Prepare messages with text and images  
    messages = [  
        {  
            "role": "user",  
            "content": [  
                {"type": "text", "text": final_prompt},  # Add your text message  
                *[  
                    {"type": "image_url", "image_url": {"url": img_str}}   
                    for img_str in imagesbase64list  # Dynamically add multiple images  
                ]  
            ]  
        }  
    ]
    # Make the API request  
    response = client.chat.completions.create( 
        model="gpt-4o-mini",  # Example model name  
        messages=messages,  
        max_tokens=300,   # Adjust as needed  
    )  
    
    # Print the response (useful for debugging)  
    #output_json_string = response["choices"][0]["message"]["content"]
    #print(response)
    output_json_string = response.choices[0].message.content
    output_json_string = output_json_string.replace("```json", "").replace("```", "").strip()
    # Validate JSON format
    try:  
        # Attempt to parse the JSON string  
        parsed_json = json.loads(output_json_string)  
        print("Valid JSON!")  
        #print(parsed_json)  # You can now work with `parsed_json` as a Python dictionary  
    except json.JSONDecodeError as e:  
        print("Invalid JSON!")  
        #print(f"Error: {e}") 
    return output_json_string


def analyze_inputdeck(inputfile):
    """
    Analyze the input deck file and return relevant information.
    Args:
        inputfile (str): Path to the input deck file.
    Returns:
        dict: Analysis results including architecture page flags and image paths.
    """
    remove_tempdata = False
    # Create temporary directories for intermediate files
    temp_pdf_dir = "data/temp_pdf"
    temp_text_dir = "data/temp_text"
    if not os.path.exists(temp_pdf_dir):
        os.makedirs(temp_pdf_dir, exist_ok=True)
    if not os.path.exists(temp_text_dir):
        os.makedirs(temp_text_dir, exist_ok=True)
    try:
        # Step 1: Convert input file to PDF
        pdf_file = convert_to_pdf(inputfile, temp_pdf_dir)
        
        # Step 2: Convert PDF to text
        text_file = pdf_to_text(pdf_file, temp_text_dir)
        
        # Step 3: Categorize pages to find architecture pages
        categorization_result = categorize_pages(text_file)
        
        # Step 4: Get architecture images if pages are found
        pages_to_convert = []
        if categorization_result["current_architecture_page_flag"]:
            pages_to_convert.append(categorization_result["current_architecture_page_number"] - 1)  # zero-based index
        if categorization_result["proposed_architecture_page_flag"]:
            pages_to_convert.append(categorization_result["proposed_architecture_page_number"] - 1)  # zero-based index
        #print("imagepages: ",pages_to_convert)
        if len(pages_to_convert) == 0:
            image_files = []
        else:
            image_files = get_architecture_images(pdf_file, pages_to_convert, temp_pdf_dir)
        #print("image files: ",image_files)
        # Step 5: Encode images to Base64
        if len(image_files) == 0:
            image_base64_list = []
        else:
            image_base64_list = [image_to_base64(img_path) for img_path in image_files]
        
        # Step 6: Use deck intelligence tool
        intelligence_result = deck_intelligence_tool(text_file, image_base64_list)
        #print(intelligence_result)
        return intelligence_result
    finally:
        # Clean up temporary directories and files
        if remove_tempdata:
            os.system(f"rm -rf {temp_pdf_dir}")
            os.system(f"rm -rf {temp_text_dir}")

#analyze_inputdeck(sys.argv[1])


#print(detect_file_type(sys.argv[1]))
#convert_to_pdf(sys.argv[1],sys.argv[2])
#pdf_to_text(sys.argv[1],sys.argv[2])
#categorize_pages(sys.argv[1])
#get_architecture_images(sys.argv[1],[2,5],sys.argv[2])