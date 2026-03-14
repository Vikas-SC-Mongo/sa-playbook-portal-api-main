import pymupdf4llm
import os
from openai import OpenAI
import pathlib
from langchain_text_splitters import MarkdownHeaderTextSplitter
import re
import base64


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def convert_to_md(fname):
    start_num = 0
    imgdir = "output-"+fname[0:fname.rfind(".pdf")]
    md_text = pymupdf4llm.to_markdown(
        fname, write_images=True, image_path=imgdir)
    print(md_text)
    md_file_inter = fname[0:fname.rfind(".pdf")]
    md_file_name = f"output-{md_file_inter}.md"
    pathlib.Path(md_file_name).write_bytes(md_text.encode())
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on, strip_headers=False)
    md_header_splits = markdown_splitter.split_text(md_text)
    print(md_header_splits)
    api_key = os.getenv("OPENAI_API_KEY1")
    openai_client = OpenAI(api_key=api_key)
    SYS_PROMPT_IMAGE = '''
    MongoDB certifies employees from its partner organizations as Architects. As part of the certification process, the participants need to submit a PPT.
    In this PPT there are two architecture component diagrams:
    1. Current Architecture diagram, which is a component diagram, which may or may not have a MongoDB Component
    2. Proposed Architecture diagram, which should have a MongoDB component
    Apart from this there is a diagram showing a graph which compares MongoDB vs any other database
    Now imagine you are a Software Architect. Your goal is to understand the architecture from the images. 
    Then describe your understanding in words. 
    If there are no diagrams, then write no-diagram. 
    If you cannot interpret the image, then say diagram-unreadable.
    '''
    i = 1
    updated_page_content = ""
    for document in md_header_splits:
        print(document.metadata)
        # print(len(document.metadata))
        # if (len(document.metadata)==0) or (document.metadata.get("Header 1")!="MongoDB SI Certification Presentation") :
        if 1 == 2:
            print("-------------------------------------------")
            continue
        else:
            print(document.page_content)
            page_content = document.page_content
            match_results = re.findall(r'!\[\]\((.+)\)', page_content)
            print("Printing regex output")
            print(match_results)
            mongo_image_document = {}
            mongo_text_document = {}
            text_id = start_num + i
            for match_result in match_results:
                image_full_path = os.path.join(imgdir, match_result)
                print(image_full_path)
                base64_image = encode_image(match_result)
                # print(base64_image)
                response = openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": SYS_PROMPT_IMAGE},
                        {"role": "user", "content": [
                            {"type": "text", "text": "Describe the images, dont miss any important information?"},
                            {"type": "image_url", "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"}
                             }
                        ]}
                    ],
                    temperature=0.0
                )
                chunk = response.choices[0].message.content
                print(chunk)
                i += 1
                page_content = page_content.replace(
                    f"![]({match_result})", f"<diagram>{chunk}</diagram>")

            print("========Current Page Content=========")
            print(page_content)
            updated_page_content = updated_page_content + "\n\n" + page_content
            print("-------------------------------------------")
    print("===========Final Content===========")
    print(updated_page_content)
    # Clean up created files and directories
    try:
        # Delete the markdown file
        os.remove(md_file_name)
        print(f"Deleted {md_file_name}")

        # Delete the image directory if it exists
        if os.path.exists(imgdir):
            for filename in os.listdir(imgdir):
                file_path = os.path.join(imgdir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
            os.rmdir(imgdir)
            print(f"Deleted directory {imgdir}")
    except Exception as e:
        print(f"Cleanup failed: {e}")

    return updated_page_content


def evaluate_submission(md_text):
    api_key = os.getenv("OPENAI_API_KEY1")
    openai_client = OpenAI(api_key=api_key)
    SYS_PROMPT_IMAGE = '''
    MongoDB certifies employees from its partner organizations as Architects. As part of the certification process, participants submit a presentation (in markdown format) describing their proposed architecture solutions. A MongoDB Solutions Architect evaluates the markdown to ensure it meets the certification criteria.

    Evaluation Criteria
    1. Required Sections
    The markdown must include the following topics:

    - Customer Overview: A clear description of the customer's business and challenges.
    - Use-case Description: Details about the business problem or opportunity being addressed.
    - Problem Statement: Specific challenges or limitations in the current system.
    - 3 Whys:
     - Why do anything?
     - Why now?
     - Why MongoDB?
    - Current Architecture: Must include:
     - A textual description of the current system enclosed within <diagram></diagram> tags. If the diagram tags are missing, it indicates the participant has only provided a text description without a proper visualization. This should be highlighted as this is not a valid submission. Sometimes there may not be any <diagram></diagram> tags but description of multiple images are present. This is a valid case and you can go ahead.
     - It might also include some extra descriptions of the diagram as well outside of the tags
    Proposed Architecture: Must include:
     - A textual description of the proposed system enclosed within <diagram></diagram> tags. If the diagram tags are missing, it indicates the participant has only provided a text description without a proper visualization. This should be highlighted as this is not a valid submission. Sometimes there may not be any <diagram></diagram> tags but description of multiple images are present. This is a valid case and you can go ahead.
     - - It might also include some extra descriptions of the diagram as well outside of the tags
    - Modernization Scorecard:
     - A comparison table or diagram (in <diagram></diagram> tags) comparing MongoDB to other databases.
     - A radar chart or a description of its representation within <diagram></diagram> tags.
    - Optional Sections (not mandatory for certification):
     - TCO/Pricing Analysis.
     - Competition Comparison.
    
    2. Evaluation Process

    - Step 1: Content Validation
     - Check whether all required sections are present.
     - Confirm that diagrams for Current Architecture and Proposed Architecture are properly enclosed within <diagram></diagram> tags.
    - Step 2: Topic Reorganization
     - If topics are misplaced or scattered due to issues like PDF-to-markdown conversion:
     - Reorganize the content logically under the appropriate headings.
     - Evaluate based on the reorganized structure.
    - Step 3: Summarization
     - Summarize each section in 30 words or less.
    - Step 4: Missing or Incomplete Sections
     - Identify and call out missing or incomplete sections, particularly:
      - 3 Whys.
      - Current Architecture (If this section is present, must include textual description of atleast 2 images or a textual description of the images enclosed within <diagram></diagram> tags).
      - Proposed Architecture (This section must be present and must include textual description of atleast 2 images or a textual description of the images enclosed within <diagram></diagram> tags).
      - Modernization Scorecard.
     - Highlight if diagrams are missing or not enclosed within <diagram></diagram> tags.

    3. Common Issues to Identify
    - Generic or vague content that lacks depth or customer-specific context.
    - Missing current and proposed architecture diagram descriptions not enclosed in atleast 1 <diagram></diagram> tags.

    4. Certification Decision
    - Recommend Certification if:
     - All required sections are present, and sufficiently detailed.
     - Diagrams for Current Architecture and Proposed Architecture are included and enclosed in <diagram></diagram> tags.
    - Reject Submission if:
     - Critical sections are missing or incomplete.
     - Diagram descriptions for Current Architecture or Proposed Architecture are missing or not enclosed in <diagram></diagram> tags.
    '''
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYS_PROMPT_IMAGE},
            {"role": "user", "content": md_text},
        ]
    )
    print("-----------")
    print(response.choices[0].message.content)
    return response.choices[0].message.content
