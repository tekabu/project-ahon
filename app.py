from pathlib import Path
import files_util as fu
import os

_file = Path(__file__)
_dir = _file.resolve().parent
_runs = os.path.join(_dir, 'runs')

fu.create_folder(_runs)

_runs_count = fu.count_folders(_runs)
_new_run = _runs_count + 1
_run = os.path.join(_runs, 'run{}'.format(_new_run))
fu.create_folder(_run)
print('new run', _new_run)

from flask import Flask, request, Response
from ultralytics import YOLO
import supervision as sv
import frame_util as fru
import pandas as pd
import numpy as np
import subprocess
import threading
import imutils
import signal
import time
import json
import cv2
import sys

MIN_DISTANCE = 5 # meters threshold
FIRST_DETECTION_DELAY = 1 # seconds before distance computation after 1st detection

app = Flask(__name__)
gframe = None
exit_app = False

with open('vehicles.json', 'r') as file:
	vehicles = json.load(file)

vehicle_detections = {}

def speak(msg, tracker_id):
	process = subprocess.Popen(['/home/ubuntu/projects/lib/mimic1/mimic', '-t', msg, '-voice', 'rms'], 
		stdout=subprocess.PIPE, 
		stderr=subprocess.PIPE)
	out, err = process.communicate()

speaker = threading.Thread(target=speak, args=("This is a test", 0))

def get_index(tracker_id):
	if tracker_id is None:
		return ""

	index = list(vehicle_detections.keys()).index(int(tracker_id))

	if index < 0:
		return ""

	return index + 1;

def video_source():
	global gframe

	box_annotator = sv.BoxAnnotator(
		thickness=2,
		text_thickness=1,
		text_scale=0.5
	)

	model = YOLO("best_2023_06_21_001.pt")
	source = "videos/video1a.mp4"
	# source = 0 # camera
	record_file = 'video{}.mp4'.format(_new_run)
	record_filename = os.path.join(_run, record_file)
	# fourcc = cv2.VideoWriter_fourcc(*'vp80') # webm
	fourcc = cv2.VideoWriter_fourcc(*'mp4v')
	out = None

	cam = cv2.VideoCapture(source)
	fps = cam.get(cv2.CAP_PROP_FPS)
	total_frames = int(cam.get(cv2.CAP_PROP_FRAME_COUNT))
	cam.release()

	try:
		for result in model.track(source=source, stream=True, agnostic_nms=True, conf=0.7, verbose=False):
			if exit_app:
				break

			frame = result.orig_img
			frame0 = np.copy(frame)
			
			detections = sv.Detections.from_yolov8(result)

			# print(dir(result))
			# print(result.names)

			for index, box in enumerate(result.boxes):
				if box.id is None:
					continue
				
				tracker_id = box.id.cpu().numpy().astype(int)[0]
				xyxy = box.xyxy.cpu().numpy().astype(int)[0]
				cls = int(box.cls[0])
				name = result.names[cls]
				vehicle = vehicles[name]
				px_w, px_h = fru.frame_dimension(xyxy)
				estimated_distance = fru.frame_distance(vehicle['focal'], vehicle['width'], px_w)
				estimated_distance = int(estimated_distance)
				# print(px_w, px_h)

				if tracker_id not in vehicle_detections:
					vehicle_detections[tracker_id] = {
						'class_name': name, 
						'distance': estimated_distance,
						'time': int(round(time.time() * 1000))
					}
				else:
					if estimated_distance <= MIN_DISTANCE:
						previous_distance = vehicle_detections[tracker_id]['distance']
						previous_time = vehicle_detections[tracker_id]['time']
						td = int(round(time.time() * 1000)) - previous_time >= (FIRST_DETECTION_DELAY * 1000)
						if estimated_distance < previous_distance and td:
							print('previous_distance', previous_distance, 'estimated_distance', estimated_distance)
							global speaker
							if not speaker.is_alive():
								ed = estimated_distance if estimated_distance > 0 else 1
								_meters = "meters" if ed > 1 else "meter"
								_name = name.replace("half ", "")
								msg = "{} in {} {} ".format(_name, ed, _meters)
								speaker = threading.Thread(target=speak, args=(msg, tracker_id))
								speaker.start()

					vehicle_detections[tracker_id]['distance'] = estimated_distance

				frame = fru.frame_center_text(frame, xyxy, '{:.2f}'.format(estimated_distance))
				
			if result.boxes.id is not None:
				detections.tracker_id = result.boxes.id.cpu().numpy().astype(int)
			else:
				detections.tracker_id = None

			labels = [
				f"#{get_index(tracker_id)} {model.model.names[class_id]} {confidence:0.2f}"
				for _, confidence, class_id, tracker_id in detections
			]

			# print(labels)

			frame = box_annotator.annotate(
				scene=frame, 
				detections=detections,
				labels=labels
			)

			gframe = imutils.resize(frame, height=800)

			if not out:
				vh, vw, _ = gframe.shape
				out = cv2.VideoWriter(record_filename, fourcc, fps, (vw, vh))

			out.write(gframe)

			if cv2.waitKey(1) & 0xFF==ord('q'):
				break

	# except KeyboardInterrupt:
	# 	print('bye')

	except Exception as e:
		print(e)

	print('bye video_source')
	out.release()

vs = threading.Thread(target=video_source)

def get_video():
	while not exit_app:
		_, buffer = cv2.imencode('.jpg', gframe)
		fr = buffer.tobytes()
		yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + fr + b'\r\n')

	print('bye get_video')

def signal_handler(signal, frame):
	print('You pressed Ctrl + C')
	global exit_app
	exit_app = True
	vs.join()
	sys.exit(0)

@app.route('/video')
def video():
	global vs
	if not vs.is_alive():
		vs = threading.Thread(target=video_source)
		vs.start()
	return Response(get_video(), mimetype='multipart/x-mixed-replace; boundary=frame')

def main():
	global gframe
	gframe = np.zeros(shape=[512, 512, 3], dtype=np.uint8)

	signal.signal(signal.SIGINT, signal_handler)

	app.run(host='0.0.0.0')

def main2():
	video_source()

if __name__ == "__main__":
	main2()