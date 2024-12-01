import cv2
from recognition.face_recognition import FaceRecognition
from utils.drawing import DrawingTool
from firebase.firebase_service import FirebaseService
import tkinter as tk
from gui.gui import GUI
import threading
from queue import Queue
import numpy as np 



class VideoProcessor:
    """
    Xử lý luồng video và nhận diện khuôn mặt.
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
                print("Không nhận được frame từ camera!")
                break

            # Cắt và vẽ khung mục tiêu
            frame = self.face_recognition.crop_frame(frame)
            frame, start_point, end_point = self.drawer.draw_target_frame(frame, 350, (0, 0, 255))

            # Phát hiện khuôn mặt
            faces = self.face_recognition.detect_faces(frame)
            processed_frame, bbox, recognized_user_id, face_status = self.face_recognition.process_frame(
                frame, faces, start_point, end_point, self.drawer
            )

            # Cập nhật giao diện
            self.app.update_processed_frame(processed_frame)
            self.app.update_image_label(face_status)

            # Tải ảnh lên Cloudinary nếu cần
            img_path = self.face_recognition.handle_warning(processed_frame, bbox, face_status)
            if img_path:
                threading.Thread(target=self.upload_to_cloudinary, args=(img_path, face_status), daemon=True).start()

            # Xử lý nhận diện khuôn mặt
            if recognized_user_id != self.last_recognized_id:
                self.last_recognized_id = recognized_user_id
                if recognized_user_id:
                    self.firebase_queue.put(recognized_user_id)
                else:
                    self.app.reset_infor_label()

    def upload_to_cloudinary(self, img_path, face_status):
        """
        Tải ảnh lên Cloudinary và trả về URL.
        """
        try:
            link_img = self.firebase_service.upload_to_cloudinary(img_path, face_status)
            if link_img:
                # Ghi log alert lên Firebase
                self.firebase_service.log_alert_access(link_img, message=f"{face_status.capitalize()} detected")
                print(f"Đường dẫn ảnh trên Cloudinary: {link_img}")
            else:
                print("Không thể ghi log do lỗi upload Cloudinary.")
        except Exception as e:
            print(f"Lỗi khi tải lên Cloudinary: {e}")



class FirebaseProcessor:
    """
    Xử lý các tác vụ liên quan đến Firebase.
    """
    def __init__(self, firebase, app, queue, stop_event):
        self.firebase = firebase
        self.app = app
        self.queue = queue
        self.stop_event = stop_event

    def process(self):
        while not self.stop_event.is_set():
            try:
                employee_id = self.queue.get(timeout=1)  # Thời gian chờ để tránh treo luồng
                if employee_id:
                    name = self.firebase.get_employee(employee_id, "name")
                    major = self.firebase.get_employee(employee_id, "major")
                    self.app.set_infor_label(name, major)

                    firebase_status = self.firebase.update_attendance(employee_id)
                    if firebase_status:
                        self.app.update_image_label(firebase_status)
                self.queue.task_done()
            except Exception:
                pass  # Hàng đợi trống hoặc lỗi nhẹ


def setup_gui_and_processors():
    """
    Thiết lập giao diện người dùng và các luồng xử lý.
    """
    # Khởi tạo các thành phần chính
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Không thể mở camera. Vui lòng kiểm tra kết nối!")
        return

    face_recognition = FaceRecognition()
    drawer = DrawingTool()
    firebase = FirebaseService()
    root = tk.Tk()
    app = GUI(root, cap)
    stop_event = threading.Event()

    # Khởi tạo hàng đợi và các bộ xử lý
    firebase_queue = Queue()
    video_processor = VideoProcessor(cap, face_recognition, drawer, app, stop_event, firebase_queue, firebase)
    firebase_processor = FirebaseProcessor(firebase, app, firebase_queue, stop_event)

    # Hàm xử lý khi đóng ứng dụng
    def on_closing():
        print("Đang dừng các luồng xử lý...")
        stop_event.set()  # Kích hoạt cờ dừng
        root.quit()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Khởi chạy các luồng
    threading.Thread(target=video_processor.process, daemon=True).start()
    threading.Thread(target=firebase_processor.process, daemon=True).start()

    # Chạy giao diện Tkinter
    root.mainloop()

    # Giải phóng tài nguyên
    cap.release()
    cv2.destroyAllWindows()
    print("Đã giải phóng tài nguyên!")




if __name__ == "__main__":
    setup_gui_and_processors()
