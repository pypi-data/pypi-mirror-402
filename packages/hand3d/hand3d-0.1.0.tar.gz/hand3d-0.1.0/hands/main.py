import cv2
import mediapipe as mp
import threading
from .Models.cube_renderer import start_renderer
from .packages.shared_state import shared_state
from .packages.hand_landmarks import get_frame_and_landmarks
from .packages.gestures import detect_gestures, detect_zoom


def run():
    prev_index_pos = None
    prev_gesture = None
    mp_draw = mp.solutions.drawing_utils
    cap = cv2.VideoCapture(0)

    prev_zoom_dist = None
    baseline_zoom_dist = None

    threading.Thread(
        target = start_renderer,
        args = (shared_state,),
        daemon= True
    ).start()

    while cap.isOpened():
        frame, result = get_frame_and_landmarks(cap)
        if frame is None:
            break

        gesture = "NONE"
        finger_positions = None

        if result.multi_hand_landmarks:
            if len(result.multi_hand_landmarks) == 2:
                gesture, prev_zoom_dist, baseline_zoom_dist, finger_positions = detect_zoom(
                    result.multi_hand_landmarks[0],
                    result.multi_hand_landmarks[1],
                    prev_zoom_dist,
                    baseline_zoom_dist
                )
            else:
                prev_zoom_dist = None
                baseline_zoom_dist = None
                for hand_landmarks in result.multi_hand_landmarks:
                    gesture = detect_gestures(hand_landmarks)

            for hand_landmarks in result.multi_hand_landmarks:
                mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp.solutions.hands.HAND_CONNECTIONS
                )

        else:
            prev_zoom_dist = None
            baseline_zoom_dist = None

        if finger_positions is not None:
            h, w, _ = frame.shape
            for finger_pos in finger_positions:
                x, y = finger_pos
                cx, cy = int(x * w), int(y * h)
                cv2.circle(frame, (cx, cy), 10, (0, 165, 255), -1)

        cv2.putText(
            frame,
            gesture,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

        if result.multi_hand_landmarks and len(result.multi_hand_landmarks) == 1:
            hand_landmarks = result.multi_hand_landmarks[0]
            lm = hand_landmarks.landmark

            x, y = lm[8].x, lm[8].y

            if gesture != prev_gesture:
                prev_index_pos = (x, y)
                prev_gesture = gesture

            if prev_index_pos is not None:
                dx = x - prev_index_pos[0]
                dy = y - prev_index_pos[1]

                prev_index_pos = (x, y)

                if abs(dx) < 0.002: dx = 0
                if abs(dy) < 0.002: dy = 0

                if gesture == "ROTATE":
                    shared_state["rot_y"] += dx * 200
                    shared_state["rot_x"] += dy * 200
                
                elif gesture == "DRAG_XY":
                    shared_state["pos_x"] += dx * 5
                    shared_state["pos_y"] -= dy * 5

                elif gesture == "DRAG_Z":
                    shared_state["pos_z"] -= dy * 10
                

        else:
            prev_index_pos = None
            prev_gesture = None

        if "ZOOM" in gesture:
            zoom_value = float(gesture.split()[1].replace("x",""))
            shared_state["zoom"] = zoom_value

        cv2.imshow("H.A.N.D.", frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
