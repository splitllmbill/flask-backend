import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def sendMail(to_address, verification_code):
    mail_server = os.getenv('MAIL_SERVER')
    mail_port = os.getenv('MAIL_PORT')
    mail_username = os.getenv('MAIL_USERNAME')
    mail_password = os.getenv('MAIL_PASSWORD')
    app_title = os.getenv('APP_TITLE')

    # HTML template as a string
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verification Email</title>
    </head>
    <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f2f2f2;">
        <center>
            <table width="100%" border="0" cellspacing="0" cellpadding="0" style="max-width: 600px;">
                <tr>
                    <td align="center" bgcolor="#333333" style="padding: 40px 0; color: #ffffff;">
                        <h1 style="font-size: 24px; margin: 0;">Verification Email</h1>
                    </td>
                </tr>
                <tr>
                    <td align="center" bgcolor="#ffffff" style="padding: 40px 20px;">
                        <p style="font-size: 16px; line-height: 24px; margin: 0; color: #666666;">
                            Your verification code is: <strong>{verification_code}</strong>.
                        </p>
                    </td>
                </tr>
                <tr>
                    <td align="center" bgcolor="#333333" style="padding: 20px 0; color: #ffffff;">
                        <p style="font-size: 12px; line-height: 18px; margin: 0;">
                            This email was sent by {app_title} team. Please reply to this mail in case of any queries.
                        </p>
                    </td>
                </tr>
            </table>
        </center>
    </body>
    </html>
    """

    message = MIMEMultipart('alternative')
    message['Subject'] = f'{app_title} Verification Email'
    message['From'] = mail_username
    message['To'] = to_address

    html_part = MIMEText(html_content, 'html')
    message.attach(html_part)

    mail = smtplib.SMTP(mail_server, mail_port)
    mail.ehlo()
    mail.starttls()
    mail.login(mail_username, mail_password)
    mail.sendmail(mail_username, to_address, message.as_string())
    mail.close()
