import os
import cv2
import numpy as np
from utils.config import load_config
from insightface.app import FaceAnalysis
import yaml
from datetime import datetime


class Face_process:
    def __init__(self, config_path="config.yaml"):
        """

        :param config_path:
        """
        #load config file
        self.configs = load_config(config_path)
        self.dataset_dir = self.configs["capture"]["dataset_dir"]
        self.violations_folder = self.configs["capture"]["violations"]
        self.max_images = self.configs["capture"]["max_images"]
        self.face_model_name = self.configs["models"]["face_analysis_model"]
        self.output_file = self.configs["encoding"]["output_file"]

        # Initialize InsightFace
        self.face_app = FaceAnalysis(name=self.face_model_name, providers=["CUDAExecutionProvider"])
        self.face_app.prepare(ctx_id=0, det_size=(640, 640))  # ctx_id=0: Use GPU; ctx_id=-1: Use CPU

        # Ensure dataset directory exists
        os.makedirs(self.dataset_dir, exist_ok=True)

    def capture(self, user_name, user_id, video_path=0):
        """
        Capture images of a user's face from a video source.

        :param user_name: Name of the user.
        :param user_id: ID of the user.
        :param video_path: Video source (default is 0 for webcam).
        :return: None
        """
        user_dir = os.path.join(self.dataset_dir, f"{user_name}.{user_id}")
        os.makedirs(user_dir, exist_ok=True)

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError("Cannot open video source.")

        num_saved = 0
        count = len(os.listdir(user_dir))
        frame_count = 0  # Counter to track the number of frames read

        while num_saved < self.max_images:
            ret, frame = cap.read()
            if not ret:
                print("Cannot receive frame from the video source.")
                break

            frame_count += 1  # Increment the frame count

            # Chỉ xử lý và lưu ảnh mỗi 10 frame
            if frame_count % 10 != 0:
                continue

            # Detect faces in the frame
            faces = self.face_app.get(frame)
            for face in faces:
                bbox = face.bbox.astype(int)
                x1, y1, x2, y2 = bbox

                # Calculate the margin
                width = x2 - x1
                height = y2 - y1
                x_margin = int(0.2 * width)  # 20% of width
                y_margin = int(0.2 * height)  # 20% of height

                # Apply margin and ensure the cropped region is within frame bounds
                x1 = max(0, x1 - x_margin)
                y1 = max(0, y1 - y_margin)
                x2 = min(frame.shape[1], x2 + x_margin)
                y2 = min(frame.shape[0], y2 + y_margin)

                # Crop the face with the margin
                cropped_face = frame[y1:y2, x1:x2]
                count += 1
                num_saved += 1

                # Save the cropped image
                img_path = os.path.join(user_dir, f"{user_name}.{user_id}.face.{count}.jpg")
                cv2.imwrite(img_path, cropped_face)
                print(f"Saved image: {img_path}")
                if num_saved >= self.max_images:
                    break

        cap.release()
        cv2.destroyAllWindows()
        print(f"Captured {num_saved} images for {user_name}.{user_id}.")

    def encoding(self):
        person_encodings = {}

        for person_name in os.listdir(self.dataset_dir):
            user_path = os.path.join(self.dataset_dir, person_name)
            if not os.path.isdir(user_path):
                continue

            user_name, user_id = person_name.split('.')
            encoding_list = []
            for img_file in os.listdir(user_path):
                img_path = os.path.join(user_path, img_file)
                print(img_path)
                img = cv2.imread(img_path)
                if img is None:
                    print(f"Could not read image: {img_path}")
                    continue

                # Detect face and get embedding
                faces = self.face_app.get(img)
                if not faces:
                    print(f"No face detected in {img_path}. Skipping...")
                    continue

                for face in faces:
                    encoding_list.append(face.normed_embedding.flatten())
            # Calculate mean if faces were detected
            if encoding_list:
                mean_encoding = np.mean(encoding_list, axis=0)
                print(f"Mean encoding shape for {person_name}: {mean_encoding.shape}")
                person_encodings[f"{person_name}.{user_id}"] = mean_encoding.tolist()

        #save to yaml file
        data = {
            'encoding': list(person_encodings.values()),
            'name': [key.split('.')[0] for key in person_encodings.keys()],
            'id': [key.split('.')[1] for key in person_encodings.keys()]
        }

        with open(self.output_file, 'w') as file:
            yaml.dump(data, file)

        print(type(data['encoding']))
        print(f"num of encoding: {len(data['encoding'])}")
        for i, enc in enumerate(data['encoding']):
            print(f"shape of encoding {i}: {np.array(enc).shape}")
        for i, name in enumerate(data['name']):
            print(f"name in {i} : {name}")

        print("Process completed, data has been saved to file YAML")

    def save_warning(self, frame, bbox, status):
        x1, y1, x2, y2 = bbox
        # Calculate the margin
        width = x2 - x1
        height = y2 - y1
        x_margin = int(0.4 * width)  # 40% of width
        y_margin = int(0.4 * height)  # 40% of height

        # Apply margin and ensure the cropped region is within frame bounds
        x1 = max(0, x1 - x_margin)
        y1 = max(0, y1 - y_margin)
        x2 = min(frame.shape[1], x2 + x_margin)
        y2 = min(frame.shape[0], y2 + y_margin)

        # Crop the face with the margin
        cropped_face = frame[y1:y2, x1:x2]

        # create folder (spoof or unknown)
        status_folder = os.path.join(self.violations_folder, status)
        os.makedirs(status_folder, exist_ok=True)

        # create file name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        image_path = os.path.join(status_folder, f"{status}_{timestamp}.jpg")

        # save image
        cv2.imwrite(image_path, cropped_face)

        return image_path

