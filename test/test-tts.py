import win32com.client as wincom
import threading
import pythoncom

# you can insert gaps in the narration by adding sleep calls
import time

def _speak(msg):
	pythoncom.CoInitialize()

	speak = wincom.Dispatch("SAPI.SpVoice")

	text = "Python text-to-speech test. using win32com.client"
	speak.Speak(text)

	# 3 second sleep
	time.sleep(3) 

	text = "This text is read after 3 seconds"
	speak.Speak(text)

# speaker = threading.Thread(target=_speak, args=("This is a test",))
# speaker.start()
# while speaker.is_alive():
# 	pass

_speak("test")