import tkinter as tk
from datetime import datetime
from PIL import Image, ImageTk
import cv2
from tkinter import Toplevel, Label


class GUI:
    def __init__(self, root, cap):
        self.root = root
        self.cap = cap
        self.processed_frame = None
        self.process_infor_label = None
        #
        self.root.geometry("434x750") #width x height
        self.root.resizable(False, False)

        # init GUI
        self.create_video_label()
        self.create_status_frame()

        # init def func
        self.update_image_label("resource/modes/waiting.png")
        self.update_time()
        self.update_frame()
        self.update_infor_label()


    def create_video_label(self):
        self.video_label = tk.Label(self.root)
        self.video_label.pack(side="top")

    def create_status_frame(self):
        status_frame = tk.Frame(self.root, height=210, width=434, bg="#3399FF", borderwidth=0, highlightthickness=0)
        status_frame.pack(side="bottom", fill="x", expand=True)
        status_frame.pack_propagate(False)

        # date time frame
        show_time = tk.Frame(status_frame, bg="#99CCFF", width=230, height=60)
        show_time.grid(row=0, column=0, padx=10, pady=10, sticky="nw")
        show_time.pack_propagate(False)
        self.time_label = tk.Label(show_time, text="", font=("Courier New", 20), bg="#99CCFF", fg="#FFFFFF")
        self.time_label.pack(anchor="center")
        self.date_label = tk.Label(show_time, text="", font=("Courier New", 14), bg="#99CCFF", fg="#FFFFFF")
        self.date_label.pack(anchor="center")

        # information frame
        infor = tk.Frame(status_frame, bg="#99CCFF", width=230, height=100)
        infor.grid(row=1, column=0, padx=10, pady=10, sticky="nw")
        infor.pack_propagate(False)
        self.name_label = tk.Label(infor, text="", font=("Courier New", 14), bg="#99CCFF", fg="#008631")
        self.name_label.pack(anchor="center", pady=(15, 10))
        self.major_label = tk.Label(infor, text="", font=("Courier New", 14), bg="#99CCFF", fg="#008631")
        self.major_label.pack(anchor="center", pady=(5, 0))

        # image frame
        image_frame = tk.Frame(status_frame, width=175, height=180, bg="#99CCFF")
        image_frame.pack(side="right", pady=10, padx=(0, 10), anchor="n")
        image_frame.pack_propagate(False)
        self.image_label = tk.Label(image_frame, bg="#99CCFF")
        self.image_label.pack(fill="both", expand=True)

    def update_frame(self):
        if self.processed_frame is not None:
            frame = cv2.cvtColor(self.processed_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)
        self.video_label.after(10, self.update_frame)

    def update_processed_frame(self, frame):
        """
        get frame in queue
        """
        self.processed_frame = frame

    def update_time(self):
        """get now time."""
        current_time = datetime.now().strftime("%H:%M:%S")
        current_date = datetime.now().strftime("%Y-%m-%d")
        self.time_label.config(text=current_time)
        self.date_label.config(text=current_date)
        self.time_label.after(1000, self.update_time)

    def update_infor_label(self):
        """
        :return:
        """
        if self.process_infor_label is None:
            name, major = "Unknown", "Unknown"
        else:
            name, major = self.process_infor_label
        self.name_label.config(text=name)
        self.major_label.config(text=major)

    def set_infor_label(self, name, major):
        """
        get name,major to show
        """
        self.process_infor_label = (name, major)
        self.update_infor_label()

    def reset_infor_label(self):
        """
        reset infor if can't recognition
        """
        self.set_infor_label("Unknown", "Unknown")
        self.update_infor_label()

    def show_custom_notification(self, message, duration=3000):
        """
        show notification
        """
        # Tính toán vị trí và kích thước của video_label
        video_label_x = self.video_label.winfo_rootx()
        video_label_y = self.video_label.winfo_rooty()
        video_label_width = self.video_label.winfo_width()
        video_label_height = self.video_label.winfo_height()

        #  Toplevel
        popup_width = 300
        popup_height = 60
        popup_x = video_label_x + (video_label_width - popup_width) // 2
        popup_y = video_label_y + video_label_height - popup_height - 20

        # make Toplevel notification
        popup = Toplevel(self.root)
        popup.title("Thông báo")
        popup.geometry(f"{popup_width}x{popup_height}+{popup_x}+{popup_y}")
        popup.resizable(False, False)
        popup.overrideredirect(True)

        # notification
        label = Label(
            popup,
            text=message,
            font=("Arial", 12),
            bg="#FFD700",
            fg="#000000",
            anchor="center",
            padx=10,
            pady=5
        )
        label.pack(fill="both", expand=True)

        # close notifi after `duration`
        popup.after(duration, popup.destroy)

    def update_image_label(self, status):
        """
            update img by status.
            :param status: Trạng thái (str) như "success", "spoof", "unknown", "late", "already_checked_in".
            """
        image_mapping = {
            "waiting": "resource/modes/waiting.png",
            "spoof": "resource/modes/spoofing.png",
            "unknown": "resource/modes/accessdenied.png",
            "image": "resource/modes/image.png",
        }
        image_path = image_mapping.get(status, "resource/modes/waiting.png")
        img = Image.open(image_path)
        img_tk = ImageTk.PhotoImage(img)
        self.image_label.config(image=img_tk)
        self.image_label.image = img_tk

        # show notification
        if status == "success":
            self.show_custom_notification("Check-in Successful!")
        elif status == "late":
            self.show_custom_notification("You are late!")
        elif status == "already_checked":
            self.show_custom_notification("Already Checked today!")
        elif status == "check_out":
            self.show_custom_notification("Check-out Successful!")

