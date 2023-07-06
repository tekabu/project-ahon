from pathlib import Path
import files_util as fu
import os

_file = Path(__file__)
_dir = _file.resolve().parent
_runs = os.path.join(_dir, 'runs')

fu.create_folder(_runs)

_runs_count = fu.count_folders(_runs)
_run = os.path.join(_runs, 'run{}'.format(_runs_count+1))
fu.create_folder(_run)

from ultralytics import YOLO
import supervision as sv
import frame_util as fru
import pandas as pd
import numpy as np
import imutils
import time
import json
import cv2

with open('distances.json', 'r') as file:
	distances = json.load(file)

vehicles = {}

def get_index(tracker_id):
	if tracker_id is None:
		return ""

	index = list(vehicles.keys()).index(int(tracker_id))

	if index < 0:
		return ""

	return index + 1;

def estimate_distance(known_width, known_height, pixel_width, pixel_height, focal_length):
	distance = (known_width * focal_length) / pixel_width
	return distance

def main():
	box_annotator = sv.BoxAnnotator(
		thickness=2,
		text_thickness=1,
		text_scale=0.5
	)

	model = YOLO("best_2023_06_21_001.pt")
	source = "videos\\video1a.mp4"
	#source = "images-distance\\random\\Screenshot 2023-06-27 233426.png"
	csv_rows = []

	try:
		for result in model.track(source=source, stream=True, agnostic_nms=True, conf=0.7, verbose=False):
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
				distance = distances[name]
				px_w, px_h = fru.frame_dimension(xyxy)
				print(px_w, px_h)

				if tracker_id not in vehicles:
					vehicles[tracker_id] = {'class_name': name}

				vehicle_index = get_index(tracker_id)
				vehicle_path = os.path.join(_run, str(vehicle_index))
				fu.create_folder(vehicle_path)
				vehicle_path_count = fu.count_files(vehicle_path) + 1
				vehicle_path_img = os.path.join(vehicle_path, '{}.jpg'.format(vehicle_path_count))

				detect_img = fru.frame_bb(frame0, xyxy)
				detect_img = fru.frame_center_text(detect_img, xyxy, '{}, {}'.format(px_w, px_h))
				fru.frame_save(detect_img, vehicle_path_img)

				csv_rows.append({
					'Index': vehicle_index,
					'Child': vehicle_path_count,
					'Class': name,
					'Known Width': distance['width'],
					'Known Height': distance['height'],
					'Pixel Width': px_w,
					'Pixel Height': px_h,
					'Distance': '',
					'Focal': '',
					'Focal Formula': '(Pixel Width x Distance) / Known Width'
				});
				
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

			frame = imutils.resize(frame, height=800)

			cv2.imshow("Project Ahon", frame)

			# if len(labels) > 0:
			# 	while True:
			# 		if cv2.waitKey(1) & 0xFF==ord('q'):
			# 			break
			# 	break

			if cv2.waitKey(1) & 0xFF==ord('q'):
				break

	except KeyboardInterrupt:
		print('bye')

	df = pd.DataFrame(csv_rows)
	df.to_csv(os.path.join(_run, 'data.csv'), index=False)

if __name__ == "__main__":
	main()