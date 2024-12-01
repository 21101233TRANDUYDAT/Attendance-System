import cv2

class DrawingTool:
    def __init__(self, font_scale=1, thickness=2):
        """

        :param font_scale:
        :param thickness:
        """
        self.font_scale = font_scale
        self.thickness = thickness

    def draw_rectangle(self, frame, bbox, color):
        """

        :param frame:
        :param bbox:
        :param color:
        :return:
        """
        cv2.rectangle(frame,(bbox[0], bbox[1]), (bbox[2], bbox[3]), color, self.thickness)

        return frame

    def put_text(self, frame, text, position, color):
        """

        :param frame:
        :param text:
        :param position:
        :param color:
        :return:
        """
        cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, self.font_scale, color, self.thickness)
        return frame

    def draw_target_frame(self, frame, rectangle_size, color):
        h, w, c = frame.shape
        center_x, center_y = w // 2, h // 2
        start_point = (center_x - rectangle_size // 2, center_y - rectangle_size // 2)
        end_point = (center_x + rectangle_size // 2, center_y + rectangle_size // 2)
        cv2.rectangle(frame, start_point, end_point, color, self.thickness)

        return frame, start_point, end_point