from firebase.firebase_service import FirebaseService


if __name__ == "__main__":
    firebase = FirebaseService()

    firebase.upload_to_cloudinary("violations_folder/spoof/spoof_20241206_050519.jpg", "spoof")