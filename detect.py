# for performing detection using model trained to detect number plates
from ultralytics import YOLO
# for handling images/video 
import cv2
# for performing mathematical operation
import math
# for handling database
import mysql.connector
# for accessing date and time
from datetime import date, datetime
# for performing multi-threading
import threading
# for extracting license number from detected plates
from extract import extract_license_no
# for sending alert for on required plate detection
from alert import send_alert_mail


#   GLOBALS
suspected_plates = {}
database = mysql.connector.connect(
    host='localhost',
    user='root',
    password='',
    database='anpr_project'
)

def insert_to_db(license_no):   # function to insert license plate details into database
    mycursor = database.cursor()
    search_query = 'SELECT * FROM plates_detected WHERE license_no = %s AND date = %s AND time = %s'
    val = (license_no, date.today(), datetime.now().strftime('%H:0:0)'))
    mycursor.execute(search_query, val)
    result = mycursor.fetchall()
    if result == []:
        query = 'INSERT INTO plates_detected VALUES (%s, %s, %s)'
        mycursor.execute(query, val)
        database.commit()

def pull_suspect_pates():
    mycursor = database.cursor()
    search_query = 'SELECT * FROM suspect_plates'
    mycursor.execute(search_query,None)
    plates = mycursor.fetchall()
    for plate in plates:
        suspected_plates[plate[0]] = 1

# print("Database: ",database,"\n")

def validate_plate(plate_no):
    if len(plate_no) >= 10:
        return True
    else:
        return False

def detect_plate(path, search_video_flag = False):            # function to detect number plates using YOLOv8
    pull_suspect_pates()
    # print(suspected_plates)
    if path != None:
        #creating a webcam object
        video = cv2.VideoCapture(path)

        # frame_width = int(video.get(3))
        # frame_height = int(video.get(4))


        model = YOLO("./static/YOLO_Weight/best.pt")        # loading trained model

        while True:
            _ , image = video.read()

            results = model(image, stream=True, verbose=False)
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    topLeft_x, topLeft_y, bottomRight_x, bottomRight_y = box.xyxy[0]
                    topLeft_x, topLeft_y, bottomRight_x, bottomRight_y = int(topLeft_x), int(topLeft_y), int(bottomRight_x), int(bottomRight_y)

                    confidence = math.ceil((box.conf[0]*100))/100

                    if confidence > 0.5:      # if the confidence score is more than 0.5 consider it as a license plate
                        label = extract_license_no(img=image, coordinates=box.xyxy)
                        label = label.strip()
                        label_valid = True
                        if search_video_flag:
                            put_box = False
                            label_valid = False
                        else:
                            put_box = True

                        box_color = (0,165,255)
                        text_color = (0,0,0)
                        tr_coords = (topLeft_x,topLeft_y)       # top right coordinates for detected text to put 
                        send_alert = False
                        if label != "" and validate_plate(label):
                            insert_to_db(label)
                            t_size = cv2.getTextSize(text=label,fontFace= 0, fontScale=1, thickness=2)[0]
                            print("Detected Plate : ",label)
                            tr_coords = (topLeft_x + t_size[0] , topLeft_y - t_size[1] - 4)

                            if search_video_flag:
                                if suspected_plates.get(label) == 1:
                                    print("************************************* FOUND NUMBER PLATE ************************************\n")
                                    print("Matched Plate : ",label)
                                    box_color = (0,0,255)
                                    text_color = (255,255,255)
                                    send_alert = True
                                    put_box = True
                                    label_valid = True
                        else:
                            label_valid = False

                        if put_box:
                            cv2.rectangle(img=image, pt1=(topLeft_x,topLeft_y), pt2=(bottomRight_x,bottomRight_y), color=box_color, thickness=3)
                            cv2.rectangle(img=image, pt1=(topLeft_x,topLeft_y), pt2=tr_coords, color=box_color, thickness= -1)
                        if label_valid:
                            cv2.putText(img=image, text=label, org=(topLeft_x,topLeft_y-2), fontFace=cv2.FONT_HERSHEY_TRIPLEX, fontScale=1, color=text_color, thickness=1)

                        if send_alert:
                            send_email_async(img=image, plate_no=label)
            yield image

cv2.destroyAllWindows()

def send_email_async(img, plate_no):            # will start a new thread for sending mail
    thread = threading.Thread(target=send_alert_mail, args=(img, plate_no))
    thread.start()
    return thread