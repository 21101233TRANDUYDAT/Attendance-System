from recognition.face_process import Face_process
import torch

if __name__ == "__main__":
    print(torch.cuda.is_available())
    #
    face_process = Face_process()

    #
    user_name = "dat"
    user_id = "21101233"
    video_path = "face_data/dat.mp4"
    face_process.capture(user_name, user_id, video_path)
    face_process.encoding()