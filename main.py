import os
import urllib.request
from app import app
from flask import Flask, request, redirect, jsonify
from werkzeug.utils import secure_filename
from keras_ocr import pipeline
import docx


ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif','docx'])

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class ParsingClass:
    def __init__(self):
        #self.pipeline = pipeline.Pipeline()
        self.ocr_pipeline = pipeline.Pipeline()

	
    def parse_image(self, image_path):
        image = pipeline.tools.read(image_path)
        result = self.ocr_pipeline.recognize([image])
        # Sort the words based on their coordinates from left to right
        sorted_words = sorted(result[0], key=lambda w: w[1][0][0])
		
		# Group words into rows based on their Y-coordinates proximity to
        rows = []
        current_row = [sorted_words[0]]
        for word in sorted_words[1:]:
            if any(abs(x - y) < 30 for x, y in zip(word[1][1], current_row[-1][1][1])):
#            if abs(word[1][1] - current_row[-1][1][1]) < 30:  # Adjust the proximity threshold as needed
                current_row.append(word)
            else:
                rows.append(current_row)
                current_row = [word]
        rows.append(current_row)
            
        # Extract the text row by row and join the words into human readable
        parsed_text = ""
        for row in rows:
            sentence = " ".join(word[0] for word in row)
            parsed_text += sentence + "\n"
        
        print("Parsed Text:")
        print(parsed_text)
        return parsed_text
        # image = pipeline.tools.read(image_path)
        # result = self.ocr_pipeline.recognize([image])
        # text = [word[0] for word in result[0]]
        # #return ' '.join(text)
        # parsed_text = ' '.join(text)
        # print("Parsed Text:")
        # print(parsed_text)
        # return parsed_text
    
    def parse_word_document(self, docx_path):
        document = docx.Document(docx_path)
        paragraphs = [p.text for p in document.paragraphs]
        parsed_text = ' '.join(paragraphs)
        print("Parsed Text:")
        print(parsed_text)
        return parsed_text
        #return ' '.join(paragraphs)
    # def parse_image(self, image_path):
    #     image = pipeline.tools.read(image_path)
    #     result = self.pipeline.recognize([image])
    #     return result[0][0][0]

parsing_instance = ParsingClass()

@app.route('/file-upload', methods=['POST'])
def upload_file():
	# check if the post request has the file part
	if 'file' not in request.files:
		resp = jsonify({'message' : 'No file part in the request'})
		resp.status_code = 400
		return resp
	file = request.files['file']
	if file.filename == '':
		resp = jsonify({'message' : 'No file selected for uploading'})
		resp.status_code = 400
		return resp
	if file and allowed_file(file.filename):
		filename = secure_filename(file.filename)
		file_path =os.path.join(app.config['UPLOAD_FOLDER'], filename)
		file.save(file_path)
		#resp = jsonify({'message' : 'File successfully uploaded'})
		#resp.status_code = 201
		#return resp
		if file_path.endswith('.docx'):
			parsed_text = parsing_instance.parse_word_document(file_path)
		else:
			parsed_text = parsing_instance.parse_image(file_path)
		#parsed_text = parsing_instance.parse_image(file_path)

		# Prepare the response as a json object
		response={
			'message': 'File successfully uploaded',
			'file_name': filename,
			'text': parsed_text
			
		}

		resp = jsonify(response)
		resp.status_code = 201
		return resp
  
	else:
		resp = jsonify({'message' : 'Allowed file types are txt, pdf, png, jpg, jpeg, gif'})
		resp.status_code = 400
		return resp

if __name__ == "__main__":
    app.run()