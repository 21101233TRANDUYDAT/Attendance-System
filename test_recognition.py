import cv2
from recognition.face_recognition import FaceRecognition
from utils.drawing import DrawingTool
import torch
import onnxruntime as ort

print(f"CUDA is : {torch.cuda.is_available()}")
print("Available providers:", ort.get_available_providers())

def main():
    face_recognition = FaceRecognition()
    drawer = DrawingTool()

    # Mở camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Không thể mở camera. Vui lòng kiểm tra kết nối!")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Không nhận được frame từ camera!")
            break
        # crop frame
        frame = face_recognition.crop_frame(frame)
        # target face
        frame, start_point, end_point = drawer.draw_target_frame(frame, 310, (0, 0, 255))
        faces = face_recognition.detect_faces(frame)
        face_recognition.process_frame(frame, faces, start_point, end_point, drawer)

        cv2.imshow('frame', frame)
        if cv2.waitKey(1) == ord('q'):
            break

    # Giải phóng tài nguyên
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
