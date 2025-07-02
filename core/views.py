import os
import fitz 
import docx
from openai import OpenAI
from django.shortcuts import render, redirect
from .forms import DocumentForm
from .models import Document
from django.conf import settings
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

            # ensures file was uploaded before proceeding 
            if doc.uploaded_file:
                uploaded_file = request.FILES['uploaded_file']

                 # Validate file extension (eg PDF or docx)
                ext = os.path.splitext(uploaded_file.name)[1].lower()
                if ext not in ['.pdf', '.docx']:
                    return render(request, 'core/upload.html', {
                        'form': form,
                        'error': 'Only .pdf or .docx files are supported.'
                    })


                # Create unique filename and assign it a unique identifier
                import uuid
                filename = f"{uuid.uuid4()}_{uploaded_file.name}"

                uploaded_file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)

                # Ensure media directory exists
                os.makedirs(settings.MEDIA_ROOT, exist_ok=True)

                # Save file in chunks to destination
                with open(uploaded_file_path, 'wb+') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)

                # extract text from file
                try:
                    doc.raw_text = extract_text_from_file(uploaded_file_path)
                    # delete file after processing
                    os.remove(uploaded_file_path)  
                except Exception as e:
                    # if file is invalid type then return error
                    print(f"Error processing file: {e}")
                    os.remove(uploaded_file_path)
                    return render(request, 'core/upload.html', {
                        'form': form,
                        'error': 'There was a problem reading your file. Please upload a valid .pdf or .docx.'
                    })

            # Summarize and save if extraction succeeded
            if doc.raw_text:
                doc.summary = summarize_text(doc.raw_text)

            # go to detail view 
            doc.save()
            return redirect('document_detail', pk=doc.pk)
    else:
        form = DocumentForm()

    return render(request, 'core/upload.html', {'form': form})


# detail page made for document, find document by key and render it
def document_detail(request, pk):
    doc = Document.objects.get(pk=pk)
    return render(request, 'core/detail.html', {'doc': doc})
