import cv2
from recognition.face_recognition import FaceRecognition
from utils.drawing import DrawingTool
from firebase.firebase_service import FirebaseService
import tkinter as tk
from gui.gui import GUI
import threading
from queue import Queue

class VideoProcessor:
    """
    process video
    """
    def __init__(self, cap, face_recognition, drawer, app, stop_event, firebase_queue, firebase_service):
        self.cap = cap
        self.face_recognition = face_recognition
        self.drawer = drawer
        self.app = app
        self.stop_event = stop_event
        self.firebase_queue = firebase_queue
        self.firebase_service = firebase_service
        self.last_recognized_id = None

    def process(self):
        while not self.stop_event.is_set():
            ret, frame = self.cap.read()
            if not ret:
                print("Could not receive frame from camera!")
                break

            # crop frame
            frame = self.face_recognition.crop_frame(frame)
            frame, start_point, end_point = self.drawer.draw_target_frame(frame, 350, (0, 0, 255))

            # face recognition
            faces = self.face_recognition.detect_faces(frame)
            processed_frame, bbox, recognized_user_id, face_status = self.face_recognition.process_frame(
                frame, faces, start_point, end_point, self.drawer
            )

            # update frame and img label
            self.app.update_processed_frame(processed_frame)
            self.app.update_image_label(face_status)

            # upload img to cloud
            img_path = self.face_recognition.handle_warning(processed_frame, bbox, face_status)
            if img_path:
                threading.Thread(target=self.upload_to_cloudinary, args=(img_path, face_status), daemon=True).start()

            # recognition process
            if recognized_user_id != self.last_recognized_id:
                self.last_recognized_id = recognized_user_id
                if recognized_user_id:
                    self.firebase_queue.put(recognized_user_id)
                else:
                    self.app.reset_infor_label()

    def upload_to_cloudinary(self, img_path, face_status):
        """
        upload and write alert log
        """
        try:
            link_img = self.firebase_service.upload_to_cloudinary(img_path, face_status)
            if link_img:
                # write log alert on Firebase
                self.firebase_service.log_alert_access(link_img, message=f"{face_status.capitalize()} detected")
                print(f"Image link on Cloudinary: {link_img}")
            else:
                print("Cannot log due to Cloudinary upload error.")
        except Exception as e:
            print(f"Error uploading to Cloudinary: {e}")



class FirebaseProcessor:
    """
    Firebase service
    """
    def __init__(self, firebase, app, queue, stop_event):
        self.firebase = firebase
        self.app = app
        self.queue = queue
        self.stop_event = stop_event

    def process(self):
        while not self.stop_event.is_set():
            try:
                employee_id = self.queue.get(timeout=1)
                if employee_id:
                    name = self.firebase.get_employee(employee_id, "name")
                    major = self.firebase.get_employee(employee_id, "major")
                    self.app.set_infor_label(name, major)

                    firebase_status = self.firebase.update_attendance(employee_id)
                    if firebase_status:
                        self.app.update_image_label(firebase_status)
                self.queue.task_done()
            except Exception:
                pass


def setup_gui_and_processors():
    """
    GUI and processors
    """
    # Khởi tạo các thành phần chính
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera. Please check the connection!")
        return

    face_recognition = FaceRecognition()
    drawer = DrawingTool()
    firebase = FirebaseService()
    root = tk.Tk()
    app = GUI(root, cap)
    stop_event = threading.Event()

    # init queue
    firebase_queue = Queue()
    video_processor = VideoProcessor(cap, face_recognition, drawer, app, stop_event, firebase_queue, firebase)
    firebase_processor = FirebaseProcessor(firebase, app, firebase_queue, stop_event)

    # close process
    def on_closing():
        print("Stopping processing threads...")
        stop_event.set()
        root.quit()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # start queue
    threading.Thread(target=video_processor.process, daemon=True).start()
    threading.Thread(target=firebase_processor.process, daemon=True).start()

    # run GUI Tkinter
    root.mainloop()

    # release window
    cap.release()
    cv2.destroyAllWindows()
    print("Resources released!")




if __name__ == "__main__":
    setup_gui_and_processors()
