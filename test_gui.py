import cv2
import tkinter as tk
from gui.gui import GUI

def start_gui():
    # Mở camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        exit()

    # Khởi tạo GUI
    root = tk.Tk()
    app = GUI(root, cap)
    root.mainloop()

    # Đóng camera khi GUI kết thúc
    cap.release()

if __name__ == "__main__":
    start_gui()
