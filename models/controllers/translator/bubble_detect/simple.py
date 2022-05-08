import cv2
import numpy as np
import itertools

from models.controllers.translator.BubbleDetect import BubbleDetectEngine

class SimpleBubbleDetectEngine(BubbleDetectEngine):
	def __init__(self):
		super(SimpleBubbleDetectEngine, self).__init__()

	def get_bubble_from_file(self,file_name):
		#print(f"filename:{file_name}")
		#original_image = cv2.imread(file_name)
		original_image = cv2.imdecode(np.fromfile(file_name, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
		#print(f"org_image {original_image}")
		height, width, channels = original_image.shape
		# draw a 2 line border!
		original_image = cv2.rectangle(original_image, (0, 0), (original_image.shape[1], original_image.shape[0]), (0, 0, 0,), 2)

		image = self._preprocess_image(original_image)
		# show_cv_image(image)

		box_candidates = self._connected_components(image, offset=0)

		box_stats = self._bubble_contours(image, box_candidates)

		results = []
		for box_stat in box_stats:
			approx, (y0, y1, x0, x1) = box_stat
			results.append([x0,y0,x1-x0,y1-y0])

		return results

	@staticmethod
	def _preprocess_image(in_image):
		out_image = cv2.cvtColor(in_image, cv2.COLOR_BGR2GRAY)
		out_image = cv2.adaptiveThreshold(out_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 75, 10)
		out_image = cv2.erode(out_image, np.ones((3, 3)), iterations=1)
		return out_image

	@staticmethod
	def _connected_components(image, offset=10):
		# CV_16U   CV_32S
		num_labels, labels, box_stats, centroids = cv2.connectedComponentsWithStats(image, 4, cv2.CV_32S)
		box_area = box_stats[:, 4]

		img_h, img_w = image.shape
		area_condition = (box_area > img_h * img_w / 20 ** 2) & (box_area < img_h * img_w / 4 ** 2)
		#print(f"area_condition: {area_condition}")
		filtered_stats = box_stats[area_condition]
		#filtered_stats = box_stats

		box_candidates = []
		counter = 0
		for x, y, w, h in filtered_stats[:, :4]:
			#print(f"old:{x}-{y}-{w}-{h}")
			counter += 1
			y0 = y - offset//2
			y1 = y + h + offset
			x0 = x - offset//2
			x1 = x + w + offset
			if y0 < 0:
				y1 = y1 - y0
				y0 = 0
			if y1 > img_h-1:
				y0 = y0 - (y1-img_h+1)
				y1 = img_h-1
			if x0 < 0:
				x1 = x1 - x0
				x0 = 0
			if x1 > img_w-1:
				x0 = x0 - (x1-img_w+1)
				x1 = img_w-1
			box_candidates.append((y0, y1, x0, x1))
		return box_candidates

	@staticmethod
	def _bubble_contours(image, box_candidates, iom_threshold=0.5, convexify=False):
		draw_mask = np.zeros_like(image)

		box_stats = []
		for y0, y1, x0, x1 in box_candidates:
			# Find contours of speech bubbles in connected components (rectangular boxes)
			mask = np.zeros_like(image)
			mask[y0:y1, x0:x1] = image[y0:y1, x0:x1]
			# _, contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
			contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
			cnts = sorted(contours, key=cv2.contourArea, reverse=True)[:3]
			for cnt in cnts:
				approx = cv2.approxPolyDP(cnt, 0.01 * cv2.arcLength(cnt, True), True)
				# print(f"getContourStat(cnt, image):{getContourStat(cnt, image)}")
				# Check pixel intensity and discard those lying outside normal (heuristic) range
				# if getContourStat(cnt, image) > 240 or getContourStat(cnt, image) < 100:
				if SimpleBubbleDetectEngine._get_contour_stat(cnt, image) > 245 or SimpleBubbleDetectEngine._get_contour_stat(cnt, image) < 100:
					continue

				x, y, w, h = cv2.boundingRect(cnt)
				cnt_area = cv2.contourArea(cnt)
				circle_radius = cv2.minEnclosingCircle(cnt)[1]
				circle_area_ratio = int(3.14 * circle_radius ** 2 / (cnt_area + 1e-6))
				rect_area_ratio = int(w * h / cnt_area)
				# This is a speech "bubble" heuristic, it should also work for boxes
				# The basic idea is that a bubbles area should approximate that of an enclosing circle
				if ((circle_area_ratio <= 2) & (cnt_area > 4000)) or (rect_area_ratio == 1):
					if convexify:
						approx = cv2.convexHull(approx)
					box_stats.append((approx, (y, y + h, x, x + w)))
					cv2.fillPoly(draw_mask, [approx], (255, 255, 255))

		# Remove overlapping boxes
		coordinates = [pts for _, pts in box_stats]
		coordinate_pairs = itertools.combinations(coordinates, 2)

		for bb1, bb2 in coordinate_pairs:
			dict1 = dict(zip(['y1', 'y2', 'x1', 'x2'], bb1))
			dict2 = dict(zip(['y1', 'y2', 'x1', 'x2'], bb2))

			iom, bigger_ix = SimpleBubbleDetectEngine._calculate_iom(dict1, dict2)
			if iom > iom_threshold:
				if bigger_ix == 0:
					smaller = bb2
				else:
					smaller = bb1
				if smaller in coordinates:
					smaller_ix = coordinates.index(smaller)
					del coordinates[smaller_ix]
					del box_stats[smaller_ix]
		return box_stats

	@staticmethod
	def _get_contour_stat(contour, image):
		mask = np.zeros(image.shape, dtype="uint8")
		cv2.drawContours(mask, [contour], -1, 255, -1)
		mean, stddev = cv2.meanStdDev(image, mask=mask)
		return mean

	@staticmethod
	def _calculate_iom(bb1, bb2):
		x_left = max(bb1['x1'], bb2['x1'])
		y_top = max(bb1['y1'], bb2['y1'])
		x_right = min(bb1['x2'], bb2['x2'])
		y_bottom = min(bb1['y2'], bb2['y2'])

		if x_right < x_left or y_bottom < y_top:
			return 0.0, None
		intersection_area = (x_right - x_left) * (y_bottom - y_top)
		bb1_area = (bb1['x2'] - bb1['x1']) * (bb1['y2'] - bb1['y1'])
		bb2_area = (bb2['x2'] - bb2['x1']) * (bb2['y2'] - bb2['y1'])
		iom = intersection_area / float(min(bb1_area, bb2_area) + 1e-6)
		bigger_area = max(bb1_area, bb2_area)
		bigger_ix = int(bigger_area == bb2_area)
		return iom, bigger_ix