from flask import Flask, render_template, request, redirect, send_file, url_for, session, jsonify
import os
from PyPDF2 import PdfMerger

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MERGED_FOLDER'] = 'merged'
app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
app.secret_key = 'your_secret_key'  # 세션 사용을 위한 비밀 키 설정

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
if not os.path.exists(app.config['MERGED_FOLDER']):
    os.makedirs(app.config['MERGED_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def unique_filename(directory, filename):
    base, extension = os.path.splitext(filename)
    counter = 1
    unique_filename = filename
    while os.path.exists(os.path.join(directory, unique_filename)):
        unique_filename = f"{base}_{counter}{extension}"
        counter += 1
    return unique_filename

@app.route('/')
def index():
    files = session.get('files', [])
    return render_template('index.html', files=files)

@app.route('/upload', methods=['POST'])
def upload_file():
    files = request.files.getlist('file')
    uploaded_files = session.get('files', [])
    for file in files:
        if file and allowed_file(file.filename):
            filename = file.filename
            if filename not in uploaded_files:
                filename = unique_filename(app.config['UPLOAD_FOLDER'], filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                uploaded_files.append(filename)
    session['files'] = uploaded_files
    return jsonify(uploaded_files)

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    files = session.get('files', [])
    files.remove(filename)
    session['files'] = files
    return redirect(url_for('index'))

@app.route('/merge', methods=['POST'])
def merge_files():
    files = request.form.getlist('files')
    output_filename = request.form.get('output_filename')
    if not output_filename:
        output_filename = 'merged.pdf'
    else:
        if not output_filename.endswith('.pdf'):
            output_filename += '.pdf'

    if not files:
        return redirect(url_for('index'))
    
    output_filepath = os.path.join(app.config['MERGED_FOLDER'], output_filename)
    
    # Check if the output file already exists and remove it
    if os.path.exists(output_filepath):
        os.remove(output_filepath)

    merger = PdfMerger()
    for filename in files:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        merger.append(filepath)
    
    merger.write(output_filepath)
    merger.close()
    
    session.pop('files', None)  # 병합 후 세션에서 파일 목록 제거
    return render_template('complete.html', filename=os.path.basename(output_filepath))

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['MERGED_FOLDER'], filename), as_attachment=True)

@app.route('/reset', methods=['POST'])
def reset():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    for file in files:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))
    session.pop('files', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=True)
