import os
import fitz 
import docx
from openai import OpenAI
from django.shortcuts import render, redirect
from .forms import DocumentForm
from .models import Document
# import statements

# retrieves API key from API key variable in environment, creates openAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_text_from_file(file_path):

    # gets file extension from file name, in this case it only accepts PDF or docx files
    ext = os.path.splitext(file_path)[1].lower()

    # if file is a pdf. Using PyMuPDF it extracts all text from document and turns it into one string. Does a very similar process for docx files using python-docx
    if ext == ".pdf":
        doc = fitz.open(file_path)
        return " ".join(page.get_text() for page in doc)
    elif ext == ".docx":
        doc = docx.Document(file_path)
        return " ".join([para.text for para in doc.paragraphs])
    return "Submit a PDF or docx file"



def summarize_text(text):

    # prompt that GPT will read that describes task 
    prompt = f"Summarize the following legal document in plain English that is easy to understand:\n\n{text}"

    # sends prompt to OpenAI, using GPT model 3.5 from the user role. 
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ],
        # limits tokens that response can use, limiting the detail and word count of response
        max_tokens=500
    )

    # returns response, removes whitespace
    return response.choices[0].message.content.strip()


def upload_document(request):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            # create a document object, not saved yet
            doc = form.save(commit=False)

            if doc.uploaded_file:
                uploaded_file = request.FILES['uploaded_file']

                # Save uploaded file to a temp location
                temp_path = os.path.join('media', uploaded_file.name)
                # reads and writes the file to temp path
                with open(temp_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)

                # Extract and assign raw text
                extracted = extract_text_from_file(temp_path)
                doc.raw_text = extracted

                # remove file after reading
                os.remove(temp_path)

            # if text is extracted, generate a summary and save it
            if doc.raw_text:
                doc.summary = summarize_text(doc.raw_text)

            # save document object and return to detail view
            doc.save()
            return redirect('document_detail', pk=doc.pk)
    else:
        form = DocumentForm()
    # render upload.html form template. This will load an empty form.
    return render(request, 'core/upload.html', {'form': form})


# detail page made for document, find document by key and render it
def document_detail(request, pk):
    doc = Document.objects.get(pk=pk)
    return render(request, 'core/detail.html', {'doc': doc})
