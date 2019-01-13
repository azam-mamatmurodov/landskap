import re


def validate_phone_number(phone_number):
    valid_phone = False
    match = re.match('^\d{9}$', phone_number)
    if match:
        valid_phone = True

    return valid_phone
