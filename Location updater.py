
from flask import Flask,render_template,jsonify,request,redirect,url_for,session
import pymysql
import time
import email
import smtplib
import threading
from datetime import datetime, timedelta , timezone
import random
import os
import binascii
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

conn = pymysql.connect(host='localhost', user='root', password='', database='bus_tracking')
cursor = conn.cursor()



secret_key = binascii.hexlify(os.urandom(24)).decode('utf-8')
app.secret_key = secret_key

@app.route(rule='/',methods=['GET'])
def admin_check():
    return render_template(template_name_or_list='admin_login.html')


@app.route(rule='/check_user', methods=['POST','GET'])
def check_user():
    mesage = ''
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        password = request.form['password']
        cursor.execute('SELECT * FROM users WHERE email = % s AND password = % s', (email, password, ))
        user = cursor.fetchone()
        if user:
            session['loggedin'] = True
            session['email'] = email
            mesage = 'Logged in successfully !'
            return  redirect(url_for('bus'))
        else:
            mesage = 'Please enter correct email / password !'
            return render_template('admin_login.html', mesage = mesage)


@app.route(rule='/forgot_password',methods=['GET'])
def forgot_password():
    return render_template(template_name_or_list='forgot_password.html')

@app.route(rule='/change_password', methods=['POST'])
def change_password():
    try:

        data = request.json
        email= data.get('email')
        cursor.execute( f"SELECT * FROM `users` WHERE `email` = '{email}'")
        count = cursor.fetchone()
        if count:
            otp = generate_otp()
            session['otp_data'] = {'otp': otp, 'timestamp': datetime.now()}
            session['email'] = email
            session['forget_email'] = email
            email_thread = threading.Thread(target=send_otp_email, args=(email, otp))
            email_thread.start()
            return jsonify({'message': 'success'})


        else:
            return jsonify({ 'message': 'Account was not Found!'})
    except Exception as e:
        return jsonify({'message': 'error', 'error': str(e)})


@app.route(rule='/otp_verification',methods=['GET'])
def otp_verification():
    return render_template(template_name_or_list='otp_verification.html')


@app.route(rule='/verify_otp', methods=['POST'])
def verify_otp():
    print("control Here")
    entered_otp = request.json.get('otp')
    print("Entered OTP",entered_otp)
    print ('otp_data' in session )
    if 'otp_data' in session and 'email' in session:
        print("otp data")
        if not is_otp_session_expired(session['otp_data']['timestamp']):
            stored_otp = session['otp_data']['otp']
            if entered_otp == stored_otp:
                return jsonify({'message': 'success'})
            else:
                return jsonify({'message': 'error'})
    else:
        return jsonify({'message':'timeout'})

    # Add a default return statement in case the conditions are not met


@app.route(rule='/timeout',methods=['GET'])
def timeout():
    return render_template(template_name_or_list='session_closed.html')


@app.route(rule='/update_password',methods=['GET'])
def update_password():
    return render_template(template_name_or_list='change_password.html')


@app.route(rule='/update_password_data', methods=['POST'])
def update_password_data():
    try:
        data = request.json
        email=session['forget_email']
        new_password = data.get('confirmpassword')
        print("UPDATE_PASSWORD_DATA() EMAIL---->",email)
        # Check if the email exists in the database
        cursor.execute(f"SELECT COUNT(*) FROM users WHERE email = '{email}'")
        count = cursor.fetchone()[0]

        if count > 0:
            # Update the password for the given email
            cursor.execute(f"UPDATE users SET password = '{new_password}' WHERE email = '{email}'")
            conn.commit()
            confirmation_email_thread = threading.Thread(target=confirmation_email, args=(email,))
            confirmation_email_thread.start()
            return jsonify({'message': 'success'})

        else:

            return  jsonify({'message': 'error', 'error': 'Email not found in the database'})


    except Exception as e:
        print("UPDATE_PASSWORD_DATA()---->ERROR:", e)
        return jsonify({'message': 'error', 'error': str(e)})


def confirmation_email(email):
    try:
        # Fetch email id from the database based on the provided email
        cursor.execute(f"SELECT email FROM users WHERE email = '{email}'")
        recipient_email = cursor.fetchone()[0]

        # Email configuration (update with your SMTP server details)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = ""  #your smtp username
        smtp_password = "" #your smtp password

        # Sender and recipient email addresses
        sender_email = "" # your sender address 

        # Create a MIME object to represent the email
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = "Password Change Confirmation"

        # Construct the email body
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        email_body = f"Dear User,\n\nYour password for the account {email} was changed at {current_time}.\n\nThis change is confirmed.\n\nBest regards,\nYour App Team"

        # Attach the email body to the MIME object
        message.attach(MIMEText(email_body, 'plain'))

        # Connect to the SMTP server and send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, message.as_string())

        print("Confirmation Email sent successfully.")

    except Exception as e:
        print(f"Error sending email: {e}")


def generate_otp():
    return str(random.randint(100000, 999999))


def is_otp_session_expired(timestamp):
    # Make the current time offset-aware
    current_time = datetime.now(timezone.utc)
    # Ensure that the timestamp is offset-aware
    if timestamp.tzinfo is None or timestamp.tzinfo.utcoffset(timestamp) is None:
        timestamp = timestamp.replace(tzinfo=timezone.utc)
    return current_time > timestamp + timedelta(minutes=10)


def send_otp_email(email,otp):
    try:
        # Fetch email id from the database based on the provided rfid_tag
        cursor.execute(f"SELECT email FROM users WHERE email = '{email}'")
        recipient_email = cursor.fetchone()[0]
        # Email configuration (update with your SMTP server details)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        smtp_username = "" #your SMTP Username
        smtp_password = "" # your SMTP Password

        # Sender and recipient email addresses
        sender_email = "" #your Sender address

        # Create a MIME object to represent the email
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = "One Time Password for Account Recovery"

        # Construct the email body
        email_body = f"Dear User,\n\nYour One Time Password for the account {email} is: {otp}\n\nThis OTP is valid for 10 Minutes\nYour App Team"

        # Attach the email body to the MIME object
        message.attach(MIMEText(email_body, 'plain'))

        # Connect to the SMTP server and send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, recipient_email, message.as_string())
        print("Email Sent Successfully")
        return 1

    except Exception as e:
        print(f"Error sending email: {e}")


@app.route(rule='/logout',methods=['GET'])
def logout():
    session['loggedin'] = False
    session['email'] = ""
    print("Successfully Looged Outx`")
    return render_template(template_name_or_list='admin_login.html')




################################################################################

@app.route('/location_update', methods=['POST'])
def location_update():
    try:
        data = request.form
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        bus_no = data.get('bun_no')

        cursor.execute("SELECT `bus_no` FROM `bus_location` WHERE `bus_no`= %s", (bus_no,))
        detected = cursor.fetchone()


        if  not detected:
            cursor.execute("INSERT INTO `bus_location`(`bus_no`, `latitude`, `longitude`) VALUES (%s, %s, %s)",
                           (bus_no, latitude, longitude))
        else:
            cursor.execute("UPDATE `bus_location` SET `latitude`=%s, `longitude`=%s WHERE `bus_no`=%s",
                           (latitude, longitude, bus_no))
        conn.commit()
        return 'Location updated successfully', 200

    except Exception as e:
        print("ERROR:", e)
        import pymysql
        conn = pymysql.connect(host='localhost', user='root', password='', database='bus_tracking')
        cursor = conn.cursor()
        # Return an error response
        return 'Error processing the request', 500

def bus_details():
    try:
        cursor.execute("SELECT `bus_no`, `latitude`, `longitude` FROM `bus_location` ")
        temp=cursor.fetchall()
        details=({'bus_no':row[0],'latitude':row[1],'longitude':row[2]} for row in temp)
        return details
    except Exception as e:
        print("ERROR:",e)


@app.route('/bus',methods=['GET'])
def bus():
    details=bus_details()
    return render_template(template_name_or_list='bus.html',details= details)

@app.route('/bus_json', methods=['GET'])
def bus_json():
    details = list(bus_details())
    return jsonify(details)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
