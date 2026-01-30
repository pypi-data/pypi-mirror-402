import math

def is_finger_extended(lm, tip, pip):
    return lm[tip].y < lm[pip].y

def is_pinch(lm):
    thumb = lm[4]
    index = lm[8]

    dist = math.hypot(thumb.x - index.x, thumb.y - index.y)
    return dist < 0.05

def detect_gestures(hand_landmarks):
    lm = hand_landmarks.landmark

    index_up = is_finger_extended(lm, 8, 6)
    middle_up = is_finger_extended(lm, 12, 10)
    ring_up = is_finger_extended(lm, 16, 14)
    pinky_up = is_finger_extended(lm, 20, 18)

    if is_pinch(lm):
        return "DRAG_Z"
    
    if not (index_up or middle_up or ring_up or pinky_up):
        return "DRAG_XY"
    
    if index_up and not(middle_up or ring_up or pinky_up):
        return "ROTATE"
    
    return "NONE"

def detect_zoom(hand1, hand2, prev_dist, baseline_dist):
    lm1 = hand1.landmark
    lm2 = hand2.landmark

    x1, y1 = lm1[8].x, lm1[8].y
    x2, y2 = lm2[8].x, lm2[8].y

    current_dist = math.hypot(x2 - x1, y2 - y1)

    if baseline_dist is None:
        baseline_dist = current_dist
        return "ZOOM 1.0x", current_dist, baseline_dist, ((x1, y1), (x2, y2))
    
    zoom_factor = current_dist / baseline_dist

    if prev_dist is not None:
        smoothing = 0.7
        current_dist = smoothing * prev_dist + (1 - smoothing) * current_dist
        zoom_factor = current_dist / baseline_dist

    zoom_factor = max(0.1, min(zoom_factor, 3.0))

    if 0.95 < zoom_factor < 1.05:
        zoom_factor = 1.0

    return f"ZOOM {zoom_factor:.2f}x", current_dist, baseline_dist, ((x1, y1), (x2, y2))
