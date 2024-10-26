from flask import render_template
from flask_mail import Message

def send_email(data):
	from app import mail
	mail = mail
	msg_title = data['title']
	msg_body = data['body']
	TempData = {
		'title' : msg_title,
		'body' : msg_body,
		'code' : data['code'],
		'url' : data['url']
	}
	print("Email data",data)
	msg = Message(msg_title,recipients=[data['email']])
	msg.html = render_template(data['template'],data=TempData)

	try:
		mail.send(msg)
		return True
	except Exception as e:
		print(e)
		return f"the email was not sent {e}"
    
def send_email_warranty(data):
	from app import mail
	mail = mail
	msg_title = data['title']
	print("Email data",data)
	msg = Message(msg_title,recipients=[data['email']])
	msg.html = render_template(data['template'],email_data=data)

	try:
		mail.send(msg)
		return True
	except Exception as e:
		print(e)
		return f"the email was not sent {e}"
    