from utils.encoding import load_face_encodings

if __name__ == "__main__":
    # Load face encodings
    inf = load_face_encodings()

    # Kiểm tra kết quả
    print("Encodings:", inf["encoding"])
    print("IDs:", inf["id"])
    print("Names:", inf["name"])
