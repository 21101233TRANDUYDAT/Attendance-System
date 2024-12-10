import cv2
import numpy as np
import math
from insightface.app import FaceAnalysis
from library.face_antspoofing import SpoofingDetector
from numpy.linalg import norm
from utils.config import load_config
from utils.encoding import load_face_encodings
import time
from recognition.face_process import Face_process

class FaceRecognition:
    def __init__(self, config_path="config.yaml", encoding_path="encoding_face.yaml"):
        """
        :param config_path: (str) path to config.yaml file
        :param encoding_path: (str) path to encoding_face file
        """
        #load config file
        self.configs = load_config(config_path)
        #load face encodings
        self.data = load_face_encodings(encoding_path)
        #Load model parameters and recognition parameters
        self.load_model_parameters()
        self.load_face_recognition_parameters()
        self.load_face_encoding_parameters()
        #tạo đối tượng
        self.face_process = Face_process()


    def load_model_parameters(self):
        """
        Load parameters model
        :return:
        """
        models_config = self.configs["models"]
        self.face_model_name = models_config["face_analysis_model"]
        self.antispoofing_model = models_config["antispoofing_model"]

        #load model face analysis
        self.face_app = FaceAnalysis(name=self.face_model_name, providers=["CUDAExecutionProvider"])
        self.face_app.prepare(ctx_id=0, det_size=(640, 640)) # ctx_id = 0 to use GPU ctx = 1 to use CPU

        #load model face anti spoofing
        self.spoofing_detector = SpoofingDetector(self.antispoofing_model)

    def load_face_recognition_parameters(self):

        recognition_config = self.configs["recognition"]
        self.similarity_threshold = recognition_config["similarity_threshold"]
        self.margin = recognition_config["margin"]
        self.s = recognition_config["s"]
        self.real_threshold = recognition_config["real_threshold"]
        self.spoof_threshold = recognition_config["spoof_threshold"]
        self.num_true = recognition_config["num_true"]
        self.num_false = recognition_config["num_false"]
        self.unknown_time_threshold = recognition_config["unknown_time_threshold"]
        self.spoof_time_threshold = recognition_config["spoof_time_threshold"]
        self.last_unknown_time = None
        self.last_spoof_time = None


    def load_face_encoding_parameters(self):
        try:
            self.user_ids = self.data['id']
            self.known_names = self.data['name']
            self.known_encodings = np.array(self.data['encoding'])

            if self.known_encodings.ndim == 1:
                self.known_encodings = self.known_encodings[np.newaxis, :]

        except KeyError as e:
            print(f"Missing key in encoding file: {e}")
            exit(1)
        except Exception as e:
            print(f"Error loading face encodings: {e}")
            exit(1)

    def crop_frame(self, frame):
        """
        :param frame:
        :return:
        """
        frame = frame[:, 263:697, :] #(540, 434, 3) h w c
        return frame

    def detect_faces(self, frame):
        """
        detect face
        """
        try:
            faces = self.face_app.get(frame)
            return faces
        except Exception as e:
            print(f"Error detecting faces: {e}")
            return []

    def is_face_inside(self, bbox, start_point, end_point):
        """
        check is face inside target
        """
        face_x1, face_y1, face_x2, face_y2 = bbox
        target_x1, target_y1 = start_point
        target_x2, target_y2 = end_point

        return (face_x1 >= target_x1 and face_y1 >= target_y1 and
                face_x2 <= target_x2 and face_y2 <= target_y2)

    def check_spoofing(self, bbox, frame):
        """
        check spoof
        :return: Tuple (is_real, score).
        """
        spoofing_results = self.spoofing_detector([bbox], frame)
        return spoofing_results[0] #(is real, score)

    def calculate_similarity(self, embedding1, embedding2):
        """
        cal similarity of 2 embedding
        """
        cosine_sim = np.dot(embedding1, embedding2) / (norm(embedding1) * norm(embedding2))
        theta = math.acos(min(1, max(-1, cosine_sim)))
        theta_m = theta + self.margin
        return self.s * math.cos(theta_m)

    def recognize_face(self, face_embedding):
        """
        recognize
        """
        best_similarity = 0
        best_identity = "Unknown"
        best_id_index = -1
        user_id = None

        for i, encoding in enumerate(self.known_encodings):
            similarity = self.calculate_similarity(face_embedding, encoding)
            if similarity > best_similarity:
                best_similarity = similarity
                best_identity = self.known_names[i]
                best_id_index = i
                user_id = self.user_ids[best_id_index]

        if best_similarity > self.similarity_threshold:
            return best_identity, best_similarity, user_id
        return "Unknown", best_similarity, user_id

    def process_frame(self, frame, faces, start_point, end_point, drawer):
        """
        process check target, check spoof and recognition
        """
        recognized_user_id = None
        status = ""
        bbox = []

        if not faces:
            self.num_true = 0
            self.num_false = 0
            drawer.put_text(frame, "No Face Detected", (start_point[0], start_point[1] - 10), (0, 0, 255))
            status = "waiting"
            return frame, bbox, recognized_user_id, status
        for face in faces:
            landmarks = face.landmark_3d_68
            for landmark in landmarks:
                cv2.circle(frame, (int(landmark[0]), int(landmark[1])), 2, (0, 0, 255), -1)
            bbox = face.bbox.astype(int)
            face_embedding = face.normed_embedding.flatten()
            # check face in target?
            if not self.is_face_inside(bbox, start_point, end_point):
                drawer.put_text(frame, "Face Outside", (start_point[0], start_point[1] - 10), (0, 0, 255))
                status = "waiting"
                return frame, bbox, recognized_user_id, status

            # check spoof
            is_real, score = self.check_spoofing(bbox, frame)
            if is_real:
                self.num_true += 1
                self.num_false = 0
                if self.num_true >= self.real_threshold:
                    # recognition
                    recognized_user_id = self.handle_recognition(frame, bbox, face_embedding, drawer)
                    status = "image" if recognized_user_id is not None else "unknown"

            else:
                self.num_false += 1
                self.num_true = 0
                current_time = time.time()
                if self.num_false >= self.spoof_threshold:
                    self.handle_spoofing(frame, bbox, drawer)
                    status = "spoof"

            return frame, bbox, recognized_user_id, status
    #=====================handle_methods=========================
    def handle_spoofing(self, frame, bbox, drawer):
        """

        """
        drawer.draw_rectangle(frame, bbox, (0, 0, 255))
        drawer.put_text(frame, "Spoof", (bbox[0], bbox[1] - 10), (0, 0, 255))

    def handle_recognition(self, frame, bbox, face_embedding, drawer):
        """

        """
        identity, similarity, user_id = self.recognize_face(face_embedding)
        split_name = identity.split('_')[0] if '_' in identity else identity
        if split_name != "Unknown":
            drawer.draw_rectangle(frame, bbox, (0, 255, 0))
            # drawer.put_text(frame, f"{split_name}", (bbox[0], bbox[1] - 10),(0, 255, 0))
            # drawer.put_text(frame, f"{user_id}", (bbox[0], bbox[3] + 30), (0, 255, 0))
            return user_id
        else:
            drawer.draw_rectangle(frame, bbox, (0, 0, 255))
            drawer.put_text(frame, f"Unknown {similarity:.2f}", (bbox[0], bbox[1] - 10), (0, 0, 255))
            return None

    def handle_warning(self, frame, bbox, status):
        """

        """

        current_time = time.time()

        # Reset times if the status is not 'spoof' or 'unknown'
        if status not in ["spoof", "unknown"]:
            self.last_spoof_time = None
            self.last_unknown_time = None
            return None

        # process spoof
        if status == "spoof":
            # check first time
            if self.last_spoof_time is None:
                self.last_spoof_time = current_time
                print("First spoof detected, skipping upload.")
                return None

            if current_time - self.last_spoof_time > self.spoof_time_threshold:
                img_path = self.face_process.save_warning(frame, bbox, status)
                self.last_spoof_time = None
                print(f"Spoof warning saved: {img_path}")
                return img_path

        # process unknown
        elif status == "unknown":
            # check first time
            if self.last_unknown_time is None:
                self.last_unknown_time = current_time
                print("First unknown detected, skipping upload.")
                return None

            if current_time - self.last_unknown_time > self.unknown_time_threshold:
                img_path = self.face_process.save_warning(frame, bbox, status)
                self.last_unknown_time = None
                print(f"Unknown warning saved: {img_path}")
                return img_path