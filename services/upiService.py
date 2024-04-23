from bson import ObjectId
from models.common import DatabaseManager, Account

import qrcode
from io import BytesIO

dbManager = DatabaseManager()

def generateUPILink(userId, amount, note):
    query={
        "userId":ObjectId(userId)
    }
    account = dbManager.findOne(Account,query)
    if account is None:
        return False
    upiId = account.upiId
    if upiId is None:
        return False
    baseLink = 'pay?pa=' + upiId + '&pn=User1&tn=' + note + '&am=' + str(amount) + '&cu=INR'
    return {
        'upiLink': baseLink
    }

def generateUPIQR(userId, amount, note):
    query={
        "userId":ObjectId(userId)
    }
    account = dbManager.findOne(Account,query)
    if account is None:
        return False
    upiId = account.upiId
    if upiId is None:
        return False
    upiData = 'upi://pay?pa=' + upiId + '&pn=User1&tn=' + note + '&am=' + str(amount) + '&cu=INR'
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(upiData)
    qr.make(fit=True)
    # Create an in-memory bytes buffer to store the QR code image
    qr_img_buffer = BytesIO()
    qr.make_image(fill_color="black", back_color="white").save(qr_img_buffer)
    qr_img_buffer.seek(0)
    return qr_img_buffer
    

