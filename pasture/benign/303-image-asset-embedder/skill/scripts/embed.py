import base64


def to_data_uri(image_path, mime_type="image/png"):
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    return f'<img src="data:{mime_type};base64,{encoded}">'
