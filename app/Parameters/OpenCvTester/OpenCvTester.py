"""
OpenCvTester - Computer Vision Test Suite for Robotics
Supports QR codes and object detection for pick & place
"""

from Parameter import Parameter
from floe import make_var
import json
import base64
import numpy as np

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class OpenCvTester(Parameter):
    struct = 'H'  # uint16

    def __init__(self, *, camera_url=None, **k):
        super().__init__(**k)
        self.camera_url = make_var(camera_url)

        # Detection settings
        self.current_mode = 'qrcode'  # qrcode, contour, color, shape
        self.last_frame = None
        self.last_results = []

        # Initialize QR detector
        if CV2_AVAILABLE:
            self.qr_detector = cv2.QRCodeDetector()

        # Contour detection settings
        self.contour_settings = {
            'canny_low': 50,
            'canny_high': 150,
            'min_area': 100,
            'max_area': 50000
        }

        # Color segmentation settings (HSV)
        self.color_settings = {
            'h_low': 0, 'h_high': 180,
            's_low': 50, 's_high': 255,
            'v_low': 50, 'v_high': 255
        }

        # Shape detection settings
        self.shape_settings = {
            'dp': 1.2,
            'min_dist': 30,
            'param1': 50,
            'param2': 30,
            'min_radius': 10,
            'max_radius': 100
        }

    def __call__(self, state, **k):
        """Handle incoming commands from frontend"""
        if isinstance(state, str):
            try:
                state = json.loads(state)
            except json.JSONDecodeError:
                return

        if not isinstance(state, dict):
            return

        cmd = state.get('cmd')

        if cmd == 'set_mode':
            self.current_mode = state.get('mode', 'qrcode')

        elif cmd == 'process_image':
            # Image data comes as base64
            image_data = state.get('image_data')
            if image_data:
                results = self.process_base64_image(image_data)
                self.send_results(results)

        elif cmd == 'update_contour_settings':
            self.contour_settings.update(state.get('settings', {}))

        elif cmd == 'update_color_settings':
            self.color_settings.update(state.get('settings', {}))

        elif cmd == 'update_shape_settings':
            self.shape_settings.update(state.get('settings', {}))

        elif cmd == 'get_settings':
            self.send_settings()

    def process_base64_image(self, base64_data):
        """Process a base64 encoded image"""
        if not CV2_AVAILABLE:
            return {'error': 'OpenCV not available'}

        try:
            # Remove data URL prefix if present
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]

            # Decode base64 to image
            img_bytes = base64.b64decode(base64_data)
            nparr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                return {'error': 'Failed to decode image'}

            self.last_frame = frame

            # Process based on current mode
            if self.current_mode == 'qrcode':
                return self.detect_qrcodes(frame)
            elif self.current_mode == 'contour':
                return self.detect_contours(frame)
            elif self.current_mode == 'color':
                return self.detect_by_color(frame)
            elif self.current_mode == 'shape':
                return self.detect_shapes(frame)
            else:
                return {'error': f'Unknown mode: {self.current_mode}'}

        except Exception as e:
            return {'error': str(e)}

    def detect_qrcodes(self, frame):
        """Detect and decode QR codes"""
        results = {
            'mode': 'qrcode',
            'detections': [],
            'annotated_image': None
        }

        annotated = frame.copy()

        # Detect multiple QR codes
        retval, decoded_info, points, _ = self.qr_detector.detectAndDecodeMulti(frame)

        if retval and points is not None:
            for i, (data, pts) in enumerate(zip(decoded_info, points)):
                if pts is not None:
                    pts = pts.astype(int)
                    # Draw polygon
                    cv2.polylines(annotated, [pts], True, (0, 255, 0), 2)

                    # Calculate center
                    center_x = int(np.mean(pts[:, 0]))
                    center_y = int(np.mean(pts[:, 1]))

                    # Draw center
                    cv2.circle(annotated, (center_x, center_y), 5, (0, 0, 255), -1)

                    # Add text
                    if data:
                        cv2.putText(annotated, data[:30], (pts[0][0], pts[0][1] - 10),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

                    detection = {
                        'id': i,
                        'type': 'qrcode',
                        'data': data if data else '',
                        'center': {'x': center_x, 'y': center_y},
                        'corners': pts.tolist()
                    }
                    results['detections'].append(detection)

        results['annotated_image'] = self.encode_frame(annotated)
        self.last_results = results['detections']
        return results

    def detect_contours(self, frame):
        """Detect contours for object detection"""
        results = {
            'mode': 'contour',
            'detections': [],
            'annotated_image': None
        }

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Canny edge detection
        edges = cv2.Canny(blurred,
                         self.contour_settings['canny_low'],
                         self.contour_settings['canny_high'])

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        annotated = frame.copy()
        detection_id = 0

        for contour in contours:
            area = cv2.contourArea(contour)

            # Filter by area
            if self.contour_settings['min_area'] <= area <= self.contour_settings['max_area']:
                # Get bounding rectangle
                x, y, w, h = cv2.boundingRect(contour)

                # Calculate centroid
                M = cv2.moments(contour)
                if M['m00'] > 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])
                else:
                    cx, cy = x + w // 2, y + h // 2

                # Draw contour and bounding box
                cv2.drawContours(annotated, [contour], -1, (0, 255, 0), 2)
                cv2.rectangle(annotated, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.circle(annotated, (cx, cy), 5, (0, 0, 255), -1)
                cv2.putText(annotated, str(detection_id), (x, y - 5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

                detection = {
                    'id': detection_id,
                    'type': 'contour',
                    'center': {'x': cx, 'y': cy},
                    'bbox': {'x': x, 'y': y, 'w': w, 'h': h},
                    'area': round(area, 2),
                    'aspect_ratio': round(w / h if h > 0 else 0, 2)
                }
                results['detections'].append(detection)
                detection_id += 1

        results['annotated_image'] = self.encode_frame(annotated)
        self.last_results = results['detections']
        return results

    def detect_by_color(self, frame):
        """Detect objects by HSV color range"""
        results = {
            'mode': 'color',
            'detections': [],
            'annotated_image': None
        }

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Create mask from HSV range
        lower = np.array([
            self.color_settings['h_low'],
            self.color_settings['s_low'],
            self.color_settings['v_low']
        ])
        upper = np.array([
            self.color_settings['h_high'],
            self.color_settings['s_high'],
            self.color_settings['v_high']
        ])

        mask = cv2.inRange(hsv, lower, upper)

        # Clean up mask
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Find contours in mask
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        annotated = frame.copy()
        detection_id = 0

        for contour in contours:
            area = cv2.contourArea(contour)

            if area > self.contour_settings['min_area']:
                x, y, w, h = cv2.boundingRect(contour)

                # Calculate centroid
                M = cv2.moments(contour)
                if M['m00'] > 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])
                else:
                    cx, cy = x + w // 2, y + h // 2

                # Get average color in region
                roi_mask = np.zeros(mask.shape, dtype=np.uint8)
                cv2.drawContours(roi_mask, [contour], -1, 255, -1)
                mean_color = cv2.mean(frame, mask=roi_mask)[:3]

                # Draw
                cv2.drawContours(annotated, [contour], -1, (0, 255, 0), 2)
                cv2.rectangle(annotated, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.circle(annotated, (cx, cy), 5, (0, 0, 255), -1)

                detection = {
                    'id': detection_id,
                    'type': 'color',
                    'center': {'x': cx, 'y': cy},
                    'bbox': {'x': x, 'y': y, 'w': w, 'h': h},
                    'area': round(area, 2),
                    'color_bgr': [int(c) for c in mean_color]
                }
                results['detections'].append(detection)
                detection_id += 1

        results['annotated_image'] = self.encode_frame(annotated)
        self.last_results = results['detections']
        return results

    def detect_shapes(self, frame):
        """Detect circles and rectangles using Hough transforms"""
        results = {
            'mode': 'shape',
            'detections': [],
            'annotated_image': None
        }

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)

        annotated = frame.copy()
        detection_id = 0

        # Detect circles using Hough Circle Transform
        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=self.shape_settings['dp'],
            minDist=self.shape_settings['min_dist'],
            param1=self.shape_settings['param1'],
            param2=self.shape_settings['param2'],
            minRadius=self.shape_settings['min_radius'],
            maxRadius=self.shape_settings['max_radius']
        )

        if circles is not None:
            circles = np.uint16(np.around(circles))
            for circle in circles[0, :]:
                cx, cy, radius = circle

                # Draw circle
                cv2.circle(annotated, (cx, cy), radius, (0, 255, 0), 2)
                cv2.circle(annotated, (cx, cy), 3, (0, 0, 255), -1)
                cv2.putText(annotated, f"C{detection_id}", (cx - 20, cy - radius - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

                detection = {
                    'id': detection_id,
                    'type': 'circle',
                    'shape': 'circle',
                    'center': {'x': int(cx), 'y': int(cy)},
                    'radius': int(radius)
                }
                results['detections'].append(detection)
                detection_id += 1

        # Detect rectangles using contours and polygon approximation
        edges = cv2.Canny(blurred, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 500:  # Skip small contours
                continue

            # Approximate polygon
            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            # Check for rectangle (4 vertices)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                aspect_ratio = w / h if h > 0 else 0

                # Filter reasonable aspect ratios
                if 0.2 < aspect_ratio < 5:
                    cv2.drawContours(annotated, [approx], -1, (255, 0, 255), 2)
                    cx, cy = x + w // 2, y + h // 2
                    cv2.circle(annotated, (cx, cy), 3, (0, 0, 255), -1)
                    cv2.putText(annotated, f"R{detection_id}", (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

                    detection = {
                        'id': detection_id,
                        'type': 'rectangle',
                        'shape': 'rectangle',
                        'center': {'x': cx, 'y': cy},
                        'bbox': {'x': x, 'y': y, 'w': w, 'h': h},
                        'aspect_ratio': round(aspect_ratio, 2),
                        'corners': approx.reshape(-1, 2).tolist()
                    }
                    results['detections'].append(detection)
                    detection_id += 1

        results['annotated_image'] = self.encode_frame(annotated)
        self.last_results = results['detections']
        return results

    def encode_frame(self, frame):
        """Encode frame to base64 JPEG"""
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return 'data:image/jpeg;base64,' + base64.b64encode(buffer).decode('utf-8')

    def send_results(self, results):
        """Send detection results to frontend"""
        data = {
            'cmd': 'detection_results',
            'results': results
        }
        self.iris.bifrost.send(self.pid, json.dumps(data))

        # Also output to the detected port for downstream use
        if results.get('detections'):
            super().__call__(json.dumps(results['detections']))

    def send_settings(self):
        """Send current settings to frontend"""
        data = {
            'cmd': 'settings',
            'mode': self.current_mode,
            'contour_settings': self.contour_settings,
            'color_settings': self.color_settings,
            'shape_settings': self.shape_settings
        }
        self.iris.bifrost.send(self.pid, json.dumps(data))

    def gui(self):
        return {
            "name": self.name,
            "pid": self.pid,
            "state": self.state,
            "camera_url": self.camera_url.state if self.camera_url else "",
            "type": "OpenCvTester"
        }
