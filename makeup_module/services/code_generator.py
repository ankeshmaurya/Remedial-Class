"""
Code Generator Service
Generates unique remedial codes and QR codes for make-up classes
"""
import secrets
import string
import os
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
from qrcode.image.styles.colormasks import RadialGradiantColorMask
from datetime import datetime


def generate_remedial_code(length=8, prefix='MUP'):
    """
    Generate a unique remedial code for make-up classes
    
    Format: MUP-XXXXXX (e.g., MUP-9K3L2A)
    
    Args:
        length: Length of the random part (default 6)
        prefix: Prefix for the code (default 'MUP')
    
    Returns:
        str: Generated remedial code
    """
    # Characters to use (excluding ambiguous ones like 0, O, 1, I, l)
    characters = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    
    # Generate random part
    random_part = ''.join(secrets.choice(characters) for _ in range(length - len(prefix) - 1))
    
    # Combine with prefix
    code = f"{prefix}-{random_part}"
    
    return code


def generate_short_code(length=6):
    """
    Generate a shorter code without prefix
    
    Args:
        length: Length of the code
    
    Returns:
        str: Generated code
    """
    characters = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(secrets.choice(characters) for _ in range(length))


def generate_numeric_code(length=6):
    """
    Generate a numeric-only code
    
    Args:
        length: Length of the code
    
    Returns:
        str: Generated numeric code
    """
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def validate_code_format(code):
    """
    Validate if a code matches the expected format
    
    Args:
        code: Code to validate
    
    Returns:
        bool: True if valid format
    """
    if not code:
        return False
    
    code = code.upper().strip()
    
    # Check prefix format
    if code.startswith('MUP-'):
        # Check if remaining part is alphanumeric
        remaining = code[4:]
        return len(remaining) >= 4 and remaining.isalnum()
    
    # Check simple alphanumeric format
    return len(code) >= 4 and code.isalnum()


def generate_qr_code(remedial_code, class_id, save_dir='static/qrcodes', base_url=None):
    """
    Generate a QR code for the remedial code
    
    Args:
        remedial_code: The remedial code to encode
        class_id: ID of the makeup class (for filename)
        save_dir: Directory to save QR codes
        base_url: Base URL for QR attendance (optional, enables direct scan)
    
    Returns:
        str: Path to the saved QR code image
    """
    # Create directory if it doesn't exist
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    qr_dir = os.path.join(base_dir, save_dir)
    
    if not os.path.exists(qr_dir):
        os.makedirs(qr_dir)
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    
    # Data to encode - if base_url provided, create a scannable URL
    if base_url:
        qr_data = f"{base_url}/student/qr-attendance/{remedial_code}"
    else:
        qr_data = f"MAKEUP:{remedial_code}"
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    # Create styled image
    try:
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            color_mask=RadialGradiantColorMask(
                back_color=(255, 255, 255),
                center_color=(67, 56, 202),  # Indigo
                edge_color=(16, 185, 129)   # Emerald
            )
        )
    except Exception:
        # Fallback to simple QR if styled fails
        img = qr.make_image(fill_color="indigo", back_color="white")
    
    # Save image
    filename = f"qr_{class_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    filepath = os.path.join(qr_dir, filename)
    img.save(filepath)
    
    # Return relative path with forward slashes (for URL compatibility)
    return f"{save_dir}/{filename}"


def decode_qr_data(qr_data):
    """
    Decode QR code data and extract remedial code
    
    Args:
        qr_data: Raw data from QR code scan
    
    Returns:
        str: Extracted remedial code or None if invalid
    """
    if not qr_data:
        return None
    
    qr_data = qr_data.strip()
    
    # Check if it's our format
    if qr_data.startswith('MAKEUP:'):
        return qr_data[7:]  # Return code after prefix
    
    # Return as-is if it looks like a code
    if validate_code_format(qr_data):
        return qr_data.upper()
    
    return None


def generate_batch_codes(count, prefix='MUP'):
    """
    Generate multiple unique codes at once
    
    Args:
        count: Number of codes to generate
        prefix: Prefix for codes
    
    Returns:
        list: List of unique codes
    """
    codes = set()
    while len(codes) < count:
        codes.add(generate_remedial_code(prefix=prefix))
    return list(codes)
