from flask import Flask, request, render_template
import os
import docx2txt
import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Set the upload folder
app.config['UPLOAD_FOLDER'] = 'upload/'


# Helper functions
def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)  # Updated to PyPDF2.PdfReader
        for page in reader.pages:       # Fixed loop to iterate over pages
            text += page.extract_text()
    return text


def extract_text_from_docx(file_path):
    return docx2txt.process(file_path)


def extract_text_from_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def extract_text(file_path):
    if file_path.endswith('.pdf'):
        return extract_text_from_pdf(file_path)
    elif file_path.endswith('.docx'):
        return extract_text_from_docx(file_path)
    elif file_path.endswith('.txt'):
        return extract_text_from_txt(file_path)
    else:
        return ""


# Flask routes
@app.route("/", methods=["GET", "POST"])
def matcher():
    if request.method == "POST":
        job_description = request.form['job_description']
        resume_files = request.files.getlist('resume')  # Fixed 'getlist'

        resumes = []
        for resume_file in resume_files:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], resume_file.filename)
            resume_file.save(file_path)
            resumes.append(extract_text(file_path))

        if not resumes or not job_description:
            return render_template('index.html', message="Please upload resumes and enter the job description.")

        vectorizer = TfidfVectorizer().fit_transform([job_description] + resumes)
        vectors = vectorizer.toarray()

        job_vector = vectors[0]
        resume_vectors = vectors[1:]
        similarities = cosine_similarity([job_vector], resume_vectors)[0]

        top_indices = similarities.argsort()[-5:][::-1]
        top_resumes = [resume_files[i].filename for i in top_indices]
        similarity_scores = [round(similarities[i], 2) for i in top_indices]

        return render_template('index.html',
                               message="Top Matching Resumes:",
                               top_resumes=top_resumes,
                               similarity_scores=similarity_scores)
    return render_template('index.html')


if __name__ == "__main__":
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)
