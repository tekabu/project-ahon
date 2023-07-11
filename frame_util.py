import cv2
import os

def frame_dimension(xyxy):
	x1, y1, x2, y2 = xyxy
	w = x2 - x1
	h = y2 - y1
	return w, h

def frame_bb(frame, xyxy):
	x1, y1, x2, y2 = xyxy
	frame = cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
	return frame

def frame_center_text(frame, xyxy, text):
	x1, y1, x2, y2 = xyxy
	cx = int((x1 + x2) / 2)
	cy = int((y1 + y2) / 2)
	thickness = 2
	text_size, _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, thickness)
	text_width, text_height = text_size
	text_x = cx - int(text_width / 2)
	text_y = cy + int(text_height / 2)

	rectangle_start = (x1 + 2, text_y - text_size[1] - int(text_height / 2))
	rectangle_end = (x2 - 2, text_y + int(text_height / 2))
	cv2.rectangle(frame, rectangle_start, rectangle_end, (255, 255, 255), cv2.FILLED)

	frame = cv2.putText(frame, text, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
	return frame

def frame_save(frame, path):
	if os.path.isfile(path):
		os.remove(path)
	cv2.imwrite(path, frame)

def frame_distance(focal_length, real_width, width_in_frame):
	distance = (real_width * focal_length) / width_in_frame
	return distance