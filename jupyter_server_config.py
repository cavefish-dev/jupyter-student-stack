from jupyter_server.auth import passwd
from os import environ

password = environ.get("jupyter_password")
if password is not None:
    c.ServerApp.password = passwd(password)
else:
    print("No password set for Jupyter Server.")

frame_origin = environ.get("jupyter_frame_origin")
if frame_origin is not None:
    c.NotebookApp.tornado_settings = {
        'headers': {
            'Content-Security-Policy': "frame-ancestors %s 'self' " % frame_origin
        }
    }
    c.ServerApp.allow_origin = frame_origin
