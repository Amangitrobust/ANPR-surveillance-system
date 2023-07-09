# to establish smtp connection
import smtplib
# for handling email messages
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
# to operate on date time
from datetime import datetime, timedelta
import cv2
# for changing image encoding to MIME acceptable format
import base64


# global variables
detected_plate = ""
location = "#"   # fixed by default (location of camera)
current_time = None

last_detected_plate = ""
last_detected_on = None


# Defining the email parameters
sender = '#'        # sender mail ID
receiver = '#'      # reciever mail ID
subject = 'License Plate Detected'



def send_alert_mail(image, plate_no):       # to send alert mails
    global detected_plate, location, current_time, last_detected_on, last_detected_plate, temp
    send_mail = True
    detected_plate = plate_no
    current_time = datetime.now()
    print(last_detected_plate,"  :   ", last_detected_on,"\n")
    if detected_plate == last_detected_plate:               # to avoid multiple emails for same plate 
        if last_detected_on != None:
            time_difference = current_time - last_detected_on
            print("Time Difference : ", time_difference,"\n")
            ten_minutes = timedelta(minutes=10)
            if time_difference < ten_minutes:
                send_mail = False
    else:
        last_detected_plate = detected_plate
        last_detected_on = current_time

    print(send_mail)

    if send_mail:
        # Creating a MIME message
        alert_message = MIMEMultipart()
        alert_message['From'] = sender
        alert_message['To'] = receiver
        alert_message['Subject'] = subject

        print("Sending Mail Alert .....")
        # Encode image as base64 string

        _, buffer_image = cv2.imencode('.jpg', image)
        image_bytes = base64.b64encode(buffer_image).decode('utf-8')
        
        # Add the HTML body to the message
        html_body = f"""
        <html>
        <body>
        <h2>ALERT....!!!</h2>
        <h4>Detected Plate Number : {detected_plate}</h4>
        <h4>Detected At : {location}</h4>
        <h4>Detected On : {current_time}</h4>
        <img src='cid:detected_image' alt='Detected Plate Image'>
        </body>
        </html>
        """
        alert_message.attach(MIMEText(html_body, 'html'))

        image = MIMEImage(base64.b64decode(image_bytes))
        image.add_header('Content-ID', '<detected_image>')
        
        #print("\nImage Encodings : ", image,"\n")

        alert_message.attach(image)

        # Create a SMTP connection and send the email
        smtp_server = 'smtp.gmail.com'
        smtp_port = 587
        smtp_username = '#'        # host mail id for sending mail 
        smtp_password = '#'        # host mail app password
        smtp_conn = smtplib.SMTP(smtp_server, smtp_port)
        smtp_conn.starttls()
        smtp_conn.login(smtp_username, smtp_password)
        smtp_conn.sendmail(sender, receiver, alert_message.as_string())
        smtp_conn.quit()
    else:
        print("Mail Alert already sent.\n")
    pass

