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
        print("Cannot open camera. Please check the connection!")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Could not receive frame from camera!")
            break

        frame = face_recognition.crop_frame(frame)
        faces = face_recognition.detect_faces(frame)
        for face in faces:
            bbox = face.bbox.astype(int)
            is_real, score = face_recognition.check_spoofing(bbox, frame)
            if str(is_real) == "True":
                face_embedding = face.normed_embedding.flatten()
                face_recognition.recognize_face(face_embedding)
                face_recognition.handle_recognition(frame, bbox, face_embedding, drawer)
            else:
                face_recognition.handle_spoofing(frame, bbox, drawer)

        cv2.imshow('frame', frame)
        if cv2.waitKey(1) == ord('q'):
            break

    # Giải phóng tài nguyên
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
