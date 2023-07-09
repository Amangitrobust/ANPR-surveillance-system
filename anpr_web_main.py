# for setting up flask application
from flask import Flask, render_template, Response, session, request  
# for setting up flask wtforms
from flask_wtf import FlaskForm, csrf        
# for taking input using flask form
from wtforms import FileField,  SubmitField, StringField, HiddenField
# to make a secure version of the file
from werkzeug.utils import secure_filename
# for validating user input in flask form
from wtforms.validators import InputRequired, Regexp
# for performing os level task
import os
# fro handling images/videos 
import cv2


app = Flask(__name__)


# configuration for flask application
app.config['SECRET_KEY'] = 'anurag@123'
app.config['UPLOAD_FOLDER'] = './static/uploads'
app.config['WTF_CSRF_ENABLED'] = True


# flask Form to accept video for detection 
class VideoInputForm(FlaskForm):
    video = FileField("Video ", validators=[InputRequired()])    # to store video path and to validate format is correct
    submit = SubmitField("Submit")

# for maitaining same csrf token(It's a secret, user-specific token in all form submissions to prevent Cross-Site Request Forgeries) on all the page operating the form
@app.before_request          
def csrf_protection():
    if request.method == 'POST':
        csrf_token_no = session.pop('_csrf_token', None)
        if not csrf_token_no or csrf_token_no != request.form.get('csrf_token'):
            print("Csrf token doesn't match")

@app.before_request
def generate_csrf_token_no():
    if '_csrf_token_no' not in session:
        session['_csrf_token_no'] = csrf.generate_csrf()


@app.route('/', methods=['GET','POST'])
def home():         # function to render home page
    #session.clear()
    return render_template('index.html', current_endpoint='home')

@app.route('/video', methods=['GET','POST'])
def video():            # function to render page to accept input video to detect and recognize number plates
    # flushing session's stored "video_path"
    session['video_path'] = None   
    # upload video form by creating instance of VideoInputForm class
    form = VideoInputForm()
    if form.validate_on_submit():
        # save uploaded video file path
        video = form.video.data
        # save video file
        video.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], secure_filename(video.filename))) 
        # use session storage to save video path
        session['video_path'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], secure_filename(video.filename))
    else:
        print(form.errors)    # print errors if error occur during submission    
    return render_template('index.html', current_endpoint='video', form = form)
    # pass

@app.route('/video_frames')
def video_frames():         # function to show final detection on video page
    return Response(generate_frame(path= session.get('video_path'), search_video_flag=False), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/search_video', methods=['GET','POST'])
def search_video():             # function to render page to accept input video and number plate to search
    session['video_path'] = None
    form = VideoInputForm()
    if form.validate_on_submit():
        # save uploaded video file path
        video = form.video.data
        video.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], secure_filename(video.filename))) # save file
        # use session storage to save video path
        session['video_path'] = os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'], secure_filename(video.filename))
        # session['search_plate_no'] = form.plate_no.data
    else:
        print(form.errors)
    return render_template('index.html', current_endpoint='search_video', form = form)
    # pass

@app.route('/search_video_frames')
def search_video_frames():      # function to show final detection on search_video page
    return Response(generate_frame(path= session.get('video_path'), search_video_flag=True), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/external')
def external():                 # function to perform detection on video from external source
    session.clear()
    return render_template('index.html', current_endpoint='external')

@app.route('/external_frames')
def external_frames():          # function to show final detection of external source video 
    return Response(generate_frame(path= 1, search_video_flag=True), mimetype='multipart/x-mixed-replace; boundary=frame')

# function to pass video to yolo for detection and generate frames to display final output on browser
def generate_frame(path='', search_video_flag=False):
    from detect import detect_plate   
    yolo_output = detect_plate(path, search_video_flag)
    for detection in yolo_output:
        ref, buffer_frame = cv2.imencode('.jpg', detection)
        frame = buffer_frame.tobytes()
        yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    
if __name__ == '__main__':              # to start the app
    app.run(debug= True)

