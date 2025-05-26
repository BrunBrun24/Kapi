
from django.http import HttpResponseBadRequest

def html_error_response(title, body_lines):
    html = f"""
    <h2>{title}</h2>
    {"".join(f"<p>{line}</p>" for line in body_lines)}
    """
    return HttpResponseBadRequest(html)
