from firebase.firebase_service import FirebaseService


if __name__ == "__main__":
    firebase = FirebaseService()

    firebase.upload_to_cloudinary("violations_folder/dat.jpg","spoof")