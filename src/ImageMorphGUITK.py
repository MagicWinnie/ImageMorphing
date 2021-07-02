### TO-DO:
### *Auto face cropping
### *Fix layout
import os
import sys
import getpass
import platform
from pathlib import Path
from copy import deepcopy
from functools import partial

import cv2
import dlib
import imageio
from imutils import face_utils
from PIL import Image, ImageTk

from tkinter import BooleanVar, Tk, Menu, PhotoImage, Canvas, Listbox
from tkinter import END, VERTICAL, HORIZONTAL
from tkinter.ttk import Frame, Button, Scrollbar, Checkbutton, Entry, Label, Separator
from tkinter import messagebox as mbox
from tkinter.filedialog import askopenfilename, asksaveasfilename

from ImageMorpher import processFrame
from ImageResizer import image_resize, resize


class GlobalVariables:
    IMAGE_1 = None
    IMAGE_2 = None

    TK_IMAGE_1 = None
    TK_IMAGE_2 = None

    DELTA = None
    DURATION = None
    SCALE = None
    REVERSED = True
    CROPPED = False

    CANVAS_1_POS = None
    CANVAS_2_POS = None

    IMG_MAX_HEIGHT = 350
    IMG_MAX_WIDTH = 350

    LAST_NUM_LIST_CORNER = 0
    LAST_NUM_LIST_FACE = 0
    LAST_NUM_LIST_USER = 0

    if platform.system() == "Windows":
        LAST_OPEN_PATH = "C:\\Users\\{}\\Pictures".format(getpass.getuser())
    elif platform.system() == "Linux":
        LAST_OPEN_PATH = "/home/{}/Pictures".format(getpass.getuser())
    else:
        LAST_OPEN_PATH = ""

    IMAGES = []
    CURR_FRAME = None
    DO_ANIMATION = True
    CORNER_POINTS_1 = []
    CORNER_POINTS_2 = []
    FACE_POINTS_1 = []
    FACE_POINTS_2 = []
    USER_POINTS_1 = []
    USER_POINTS_2 = []


class MainWindow(Frame):
    def __init__(self):
        super().__init__()

        self.GLOBAL_VARS = GlobalVariables()

        self.initUI()
        self.initMenu()
        self.bindKeys()

        self.drawPoints()

        self.detector = dlib.get_frontal_face_detector()

        pwd = os.path.abspath(os.path.dirname(__file__))
        if os.path.isfile(os.path.join(pwd, "shape_predictor_68_face_landmarks.dat")):
            self.predictor = dlib.shape_predictor(
                os.path.join(pwd, "shape_predictor_68_face_landmarks.dat")
            )
        else:
            self.onError(
                "Could not find the following file: 'shape_predictor_68_face_landmarks.dat'. Download the file and relaunch the app!"
            )
            sys.exit(-1)

    def initUI(self):
        self.master.title("Image Morphing GUI")
        self.grid()

        btn_open_1 = Button(
            self, text="Open Image #1", command=partial(self.open_file, 1)
        )
        btn_open_1.grid(row=0, column=0)

        btn_open_2 = Button(
            self, text="Open Image #2", command=partial(self.open_file, 2)
        )
        btn_open_2.grid(row=0, column=1)

        self.reset_img_1_canvas()
        self.reset_img_2_canvas()

        ##### -------------------------------

        self.label_settings = Label(self, text="Settings", font="bold")
        self.label_settings.grid(row=0, column=5)

        self.settings_frame = Frame(self)
        self.settings_frame.grid(row=1, column=5, sticky="n")

        self.delta_label = Label(self.settings_frame, text="Delta (from 1 to 100): ")
        self.delta_label.grid(row=0, column=0, sticky="w")
        self.delta_vcmd = (self.register(self.onEntryEditDelta), "%P")
        self.delta_input = Entry(
            self.settings_frame,
            validate="key",
            validatecommand=self.delta_vcmd,
            width=5,
        )
        self.delta_input.grid(row=0, column=1, sticky="w")
        self.delta_input.insert(END, "10")

        self.duration_label = Label(
            self.settings_frame, text="Duration (from 0.01 to 10.00): "
        )
        self.duration_label.grid(row=1, column=0, sticky="w")
        self.duration_vcmd = (self.register(self.onEntryEditDuration), "%P")
        self.duration_input = Entry(
            self.settings_frame,
            validate="key",
            validatecommand=self.duration_vcmd,
            width=5,
        )
        self.duration_input.grid(row=1, column=1, sticky="w")
        self.duration_input.insert(END, "0.15")

        self.reversed_label = Label(self.settings_frame, text="Loop? ")
        self.reversed_label.grid(row=2, column=0, sticky="w")
        self.reversed_var = BooleanVar()
        self.reversed_var.set(1)
        self.reversed_input = Checkbutton(
            self.settings_frame,
            variable=self.reversed_var,
            onvalue=1,
            offvalue=0,
            command=self.onEntryEditReversed,
        )
        self.reversed_input.grid(row=2, column=1)

        # self.cropped_label = Label(self.settings_frame, text="Crop and fit? ")
        # self.cropped_label.grid(row=3, column=0, sticky="w")
        # self.cropped_var = BooleanVar()
        # self.cropped_var.set(0)
        # self.cropped_input = Checkbutton(
        #     self.settings_frame,
        #     variable=self.cropped_var,
        #     onvalue=1,
        #     offvalue=0,
        #     command=self.onEntryEditCropped,
        # )
        # self.cropped_input.grid(row=3, column=1)

        self.corner_pt_gen_btn = Button(
            self.settings_frame,
            text="Add corner points",
            command=self.addCorners,
        )
        self.corner_pt_gen_btn.grid(row=4, column=0, columnspan=2, sticky="ew")

        self.face_rec_gen_btn = Button(
            self.settings_frame,
            text="Generate points from face recognition",
            command=self.onFaceRecBtn,
        )
        self.face_rec_gen_btn.grid(row=5, column=0, columnspan=2, sticky="ew")

        self.start_btn = Button(
            self.settings_frame, text="Start", command=self.onStartBtn
        )
        self.start_btn.grid(row=6, column=0, columnspan=2, sticky="ew")

        self.output_size_label = Label(
            self.settings_frame, text="Output GIF resolution: None", anchor="center"
        )
        self.output_size_label.grid(row=7, column=0, columnspan=2, sticky="ew")

        self.output_scale_label = Label(
            self.settings_frame, text="Output GIF size scale:"
        )
        self.output_scale_label.grid(row=8, column=0, sticky="w")
        self.output_scale_vcmd = (self.register(self.onEntryEditOutputScale), "%P")
        self.output_scale_input = Entry(
            self.settings_frame,
            validate="key",
            validatecommand=self.output_scale_vcmd,
            width=5,
        )
        self.output_scale_input.grid(row=8, column=1, sticky="e")

        self.save_btn = Button(
            self.settings_frame, text="Save animation", command=self.save_file
        )
        self.save_btn.grid(row=9, column=0, columnspan=2, sticky="ew")

        self.Reset_btn = Button(
            self.settings_frame, text="Reset", command=self.onResetBtn
        )
        self.Reset_btn.grid(row=10, column=0, columnspan=2, sticky="ew")

        self.points_label = Label(self, text="List of pairs", font="bold")
        self.points_label.grid(row=0, column=6)

        ##### --------------CORNER-----------------

        self.points_container = Frame(self)
        self.points_container.grid(row=1, column=6, sticky="news")

        self.points_canvas = Canvas(self.points_container)
        self.points_canvas.grid(row=0, column=0, sticky="news")

        self.corner_points_label = Label(
            self.points_canvas, text="CORNER POINTS", font=("Arial", 10)
        )
        self.corner_points_label.grid(row=0, column=0)

        self.corner_points_scrollbar = Scrollbar(self.points_canvas)
        self.corner_points_scrollbar.grid(row=1, column=1, sticky="ns")

        self.corner_points_list = Listbox(
            self.points_canvas,
            yscrollcommand=self.corner_points_scrollbar.set,
            height=8,
            selectmode="extended",
        )
        self.corner_points_list.bind("<Delete>", self.deleteCornerPtsList)

        self.corner_points_list.grid(row=1, column=0, sticky="ns")
        self.corner_points_scrollbar.config(command=self.corner_points_list.yview)

        ##### --------------FACE-----------------

        self.face_points_label = Label(
            self.points_canvas, text="FACE POINTS", font=("Arial", 10)
        )
        self.face_points_label.grid(row=2, column=0)

        self.face_points_scrollbar = Scrollbar(self.points_canvas)
        self.face_points_scrollbar.grid(row=3, column=1, sticky="ns")

        self.face_points_list = Listbox(
            self.points_canvas,
            yscrollcommand=self.face_points_scrollbar.set,
            height=8,
            selectmode="extended",
        )
        self.face_points_list.bind("<Delete>", self.deleteFacePtsList)

        self.face_points_list.grid(row=3, column=0, sticky="ns")
        self.face_points_scrollbar.config(command=self.face_points_list.yview)

        ##### --------------USER-----------------

        self.user_points_label = Label(
            self.points_canvas, text="USER POINTS", font=("Arial", 10)
        )
        self.user_points_label.grid(row=4, column=0)

        self.user_points_scrollbar = Scrollbar(self.points_canvas)
        self.user_points_scrollbar.grid(row=5, column=1, sticky="ns")

        self.user_points_list = Listbox(
            self.points_canvas,
            yscrollcommand=self.user_points_scrollbar.set,
            height=8,
            selectmode="extended",
        )
        self.user_points_list.bind("<Delete>", self.deleteUserPtsList)

        self.user_points_list.grid(row=5, column=0, sticky="ns")
        self.user_points_scrollbar.config(command=self.user_points_list.yview)

        self.gif_label = Label(self, text="Animation", font="bold")
        self.gif_label.grid(row=0, column=3, columnspan=2)

        self.start_gif_viewer()

        self.initSeparators()

    def initSeparators(self):
        return
        Separator(self, orient=VERTICAL).grid(column=0, row=0, rowspan=4, sticky="nse")
        Separator(self, orient=VERTICAL).grid(column=1, row=0, rowspan=4, sticky="nse")
        Separator(self, orient=VERTICAL).grid(column=2, row=0, rowspan=2, sticky="nse")

        Separator(self, orient=HORIZONTAL).grid(
            column=0, row=1, columnspan=4, sticky="ewn"
        )
        Separator(self, orient=HORIZONTAL).grid(
            column=0, row=2, columnspan=5, sticky="ewn"
        )
        Separator(self, orient=HORIZONTAL).grid(
            column=0, row=3, columnspan=4, sticky="ewn"
        )

    def add2PtsList(self, pt1, pt2, t):
        if t == 0:
            self.corner_points_list.insert(
                END, "Pair #" + str(self.GLOBAL_VARS.LAST_NUM_LIST_CORNER)
            )
            self.GLOBAL_VARS.CORNER_POINTS_1.append(pt1)
            self.GLOBAL_VARS.CORNER_POINTS_2.append(pt2)
            self.GLOBAL_VARS.LAST_NUM_LIST_CORNER += 1
        elif t == 1:
            self.face_points_list.insert(
                END, "Pair #" + str(self.GLOBAL_VARS.LAST_NUM_LIST_FACE)
            )
            self.GLOBAL_VARS.FACE_POINTS_1.append(pt1)
            self.GLOBAL_VARS.FACE_POINTS_2.append(pt2)
            self.GLOBAL_VARS.LAST_NUM_LIST_FACE += 1
        elif t == 2:
            self.user_points_list.insert(
                END, "Pair #" + str(self.GLOBAL_VARS.LAST_NUM_LIST_USER)
            )
            self.GLOBAL_VARS.USER_POINTS_1.append(pt1)
            self.GLOBAL_VARS.USER_POINTS_2.append(pt2)
            self.GLOBAL_VARS.LAST_NUM_LIST_USER += 1

    def deleteCornerPtsList(self, *args):
        sel = self.corner_points_list.curselection()
        for index in sel[::-1]:
            self.corner_points_list.delete(index)
            self.GLOBAL_VARS.CORNER_POINTS_1.pop(index)
            self.GLOBAL_VARS.CORNER_POINTS_2.pop(index)

    def deleteFacePtsList(self, *args):
        sel = self.face_points_list.curselection()
        for index in sel[::-1]:
            self.face_points_list.delete(index)
            self.GLOBAL_VARS.FACE_POINTS_1.pop(index)
            self.GLOBAL_VARS.FACE_POINTS_2.pop(index)

    def deleteUserPtsList(self, *args):
        sel = self.user_points_list.curselection()
        for index in sel[::-1]:
            self.user_points_list.delete(index)
            self.GLOBAL_VARS.USER_POINTS_1.pop(index)
            self.GLOBAL_VARS.USER_POINTS_2.pop(index)

    def deleteListPts(self):
        self.GLOBAL_VARS.CORNER_POINTS_1 = []
        self.GLOBAL_VARS.CORNER_POINTS_2 = []
        self.GLOBAL_VARS.FACE_POINTS_1 = []
        self.GLOBAL_VARS.FACE_POINTS_2 = []
        self.GLOBAL_VARS.USER_POINTS_1 = []
        self.GLOBAL_VARS.USER_POINTS_2 = []

    def deleteAllPts(self):
        self.corner_points_list.delete(0, END)
        self.face_points_list.delete(0, END)
        self.user_points_list.delete(0, END)
        self.deleteListPts()
        self.GLOBAL_VARS.LAST_NUM_LIST_CORNER = 0
        self.GLOBAL_VARS.LAST_NUM_LIST_FACE = 0
        self.GLOBAL_VARS.LAST_NUM_LIST_USER = 0

    def onResetBtn(self):
        self.GLOBAL_VARS.IMAGES = []
        self.GLOBAL_VARS.IMAGE_1 = None
        self.GLOBAL_VARS.IMAGE_2 = None

        self.deleteAllPts()
        self.reset_img_1_canvas()
        self.reset_img_2_canvas()
        self.stop_gif_viewer()
        self.start_gif_viewer()

        self.initSeparators()

        self.output_size_label.configure(text="Output GIF resolution: None")

    def onStartBtn(self):
        if self.GLOBAL_VARS.IMAGE_1 is None or self.GLOBAL_VARS.IMAGE_2 is None:
            self.onError("One of the images is not chosen!")
            return
        if self.GLOBAL_VARS.DELTA is None or self.GLOBAL_VARS.DURATION is None:
            self.onError("Delta or duration value is not set!")
            return
        if (
            len(self.GLOBAL_VARS.CORNER_POINTS_1)
            + len(self.GLOBAL_VARS.FACE_POINTS_1)
            + len(self.GLOBAL_VARS.USER_POINTS_1)
        ) < 3:
            self.onError("You must have at least 3 points!")
            return
        if len(self.GLOBAL_VARS.CORNER_POINTS_1) != len(self.GLOBAL_VARS.CORNER_POINTS_2):
            self.onError(
                "Length of self.GLOBAL_VARS.CORNER_POINTS_1 != self.GLOBAL_VARS.CORNER_POINTS_2!\nThis is unplanned behaviour! Please report the bug!"
            )
            return
        if len(self.GLOBAL_VARS.FACE_POINTS_1) != len(self.GLOBAL_VARS.FACE_POINTS_2):
            self.onError(
                "Length of self.GLOBAL_VARS.FACE_POINTS_1 != self.GLOBAL_VARS.FACE_POINTS_2!\nThis is unplanned behaviour! Please report the bug!"
            )
            return
        if len(self.GLOBAL_VARS.USER_POINTS_1) != len(self.GLOBAL_VARS.USER_POINTS_2):
            self.onError(
                "Length of self.GLOBAL_VARS.USER_POINTS_1 != self.GLOBAL_VARS.USER_POINTS_2!\nThis is unplanned behaviour! Please report the bug!"
            )
            return

        img1 = self.GLOBAL_VARS.IMAGE_1.copy()
        img2 = self.GLOBAL_VARS.IMAGE_2.copy()

        pts1 = deepcopy(self.GLOBAL_VARS.CORNER_POINTS_1) + deepcopy(self.GLOBAL_VARS.FACE_POINTS_1) + deepcopy(self.GLOBAL_VARS.USER_POINTS_1)
        pts2 = deepcopy(self.GLOBAL_VARS.CORNER_POINTS_2) + deepcopy(self.GLOBAL_VARS.FACE_POINTS_2) + deepcopy(self.GLOBAL_VARS.USER_POINTS_2)

        if self.GLOBAL_VARS.CROPPED:
            extreme_pts_1 = self.get_extreme_points(1)
            extreme_pts_2 = self.get_extreme_points(2)

            out_box = 50

            left_up_1 = (extreme_pts_1[0][0] - out_box, extreme_pts_1[2][1] - out_box)
            left_up_2 = (extreme_pts_2[0][0] - out_box, extreme_pts_2[2][1] - out_box)

            img1 = img1[
                extreme_pts_1[2][1]
                - out_box : (extreme_pts_1[2][1] - out_box)
                + (extreme_pts_1[3][1] - extreme_pts_1[2][1] + 1 + out_box),
                extreme_pts_1[0][0]
                - out_box : (extreme_pts_1[0][0] - out_box)
                + (extreme_pts_1[1][0] - extreme_pts_1[0][0] + 1 + out_box),
            ]
            img2 = img2[
                extreme_pts_2[2][1]
                - out_box : (extreme_pts_2[2][1] - out_box)
                + (extreme_pts_2[3][1] - extreme_pts_2[2][1] + 1 + out_box),
                extreme_pts_2[0][0]
                - out_box : (extreme_pts_2[0][0] - out_box)
                + (extreme_pts_2[1][0] - extreme_pts_2[0][0] + 1 + out_box),
            ]

            max_width = max(img1.shape[1], img2.shape[1])
            max_height = max(img1.shape[0], img2.shape[0])

            img1 = cv2.resize(
                img1, (max_width, max_height), interpolation=cv2.INTER_AREA
            )
            img2 = cv2.resize(
                img2, (max_width, max_height), interpolation=cv2.INTER_AREA
            )

            pts1 = deepcopy(self.GLOBAL_VARS.CORNER_POINTS_1) + deepcopy(self.GLOBAL_VARS.FACE_POINTS_1) + deepcopy(self.GLOBAL_VARS.USER_POINTS_1)
            pts2 = deepcopy(self.GLOBAL_VARS.CORNER_POINTS_2) + deepcopy(self.GLOBAL_VARS.FACE_POINTS_2) + deepcopy(self.GLOBAL_VARS.USER_POINTS_2)

            for i in range(len(pts1)):
                pts1[i] = (pts1[i][0] - left_up_1[0], pts1[i][1] - left_up_1[1])
                pts2[i] = (pts2[i][0] - left_up_2[0], pts2[i][1] - left_up_2[1])

            for p in pts1:
                img1 = cv2.circle(img1, tuple(p), 8, (255, 0, 0), -1)
            for p in pts2:
                img2 = cv2.circle(img2, tuple(p), 8, (255, 0, 0), -1)
            # cv2.imwrite("img1.jpg", img1)
            # cv2.imwrite("img2.jpg", img2)
            # print(pts1)
            # print(pts2)

        self.GLOBAL_VARS.IMAGES = []
        for i in range(0, 101, self.GLOBAL_VARS.DELTA):
            try:
                frame = processFrame(img1, img2, min(i / 100, 1.0), pts1, pts2)
            except Exception as e:
                self.onError("Some error occured on frame processing!\n{}".format(e))
                self.GLOBAL_VARS.IMAGES = []
                return

            self.GLOBAL_VARS.IMAGES.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        if self.GLOBAL_VARS.REVERSED:
            self.GLOBAL_VARS.IMAGES += list(reversed(self.GLOBAL_VARS.IMAGES))

        self.output_size_label.configure(
            text="Output GIF resolution: {}x{}".format(
                self.GLOBAL_VARS.IMAGES[0].shape[1], self.GLOBAL_VARS.IMAGES[0].shape[0]
            )
        )

    def addCorners(self):
        self.corner_points_list.delete(0, END)
        self.GLOBAL_VARS.CORNER_POINTS_1 = []
        self.GLOBAL_VARS.CORNER_POINTS_2 = []
        self.GLOBAL_VARS.LAST_NUM_LIST_CORNER = 0

        self.add2PtsList(
            [self.GLOBAL_VARS.IMAGE_1.shape[1] - 1, 0],
            [self.GLOBAL_VARS.IMAGE_2.shape[1] - 1, 0],
            0,
        )
        self.add2PtsList(
            [
                self.GLOBAL_VARS.IMAGE_1.shape[1] - 1,
                self.GLOBAL_VARS.IMAGE_1.shape[0] - 1,
            ],
            [
                self.GLOBAL_VARS.IMAGE_2.shape[1] - 1,
                self.GLOBAL_VARS.IMAGE_2.shape[0] - 1,
            ],
            0,
        )
        self.add2PtsList(
            [0, self.GLOBAL_VARS.IMAGE_1.shape[0] - 1],
            [0, self.GLOBAL_VARS.IMAGE_2.shape[0] - 1],
            0,
        )
        self.add2PtsList([0, 0], [0, 0], 0)

        self.add2PtsList(
            [self.GLOBAL_VARS.IMAGE_1.shape[1] // 2 - 1, 0],
            [self.GLOBAL_VARS.IMAGE_2.shape[1] // 2 - 1, 0],
            0,
        )
        self.add2PtsList(
            [0, self.GLOBAL_VARS.IMAGE_1.shape[0] // 2 - 1],
            [0, self.GLOBAL_VARS.IMAGE_2.shape[0] // 2 - 1],
            0,
        )
        self.add2PtsList(
            [
                self.GLOBAL_VARS.IMAGE_1.shape[1] // 2 - 1,
                self.GLOBAL_VARS.IMAGE_1.shape[0] - 1,
            ],
            [
                self.GLOBAL_VARS.IMAGE_2.shape[1] // 2 - 1,
                self.GLOBAL_VARS.IMAGE_2.shape[0] - 1,
            ],
            0,
        )
        self.add2PtsList(
            [
                self.GLOBAL_VARS.IMAGE_1.shape[1] - 1,
                self.GLOBAL_VARS.IMAGE_1.shape[0] // 2 - 1,
            ],
            [
                self.GLOBAL_VARS.IMAGE_2.shape[1] - 1,
                self.GLOBAL_VARS.IMAGE_2.shape[0] // 2 - 1,
            ],
            0,
        )

    def onFaceRecBtn(self):
        if self.GLOBAL_VARS.IMAGE_1 is None or self.GLOBAL_VARS.IMAGE_2 is None:
            self.onError("One of the images is not chosen!")
            return
        self.onInfo(
            "Several faces may be recognized.\nOnly the largest faces will be used!"
        )

        self.face_points_list.delete(0, END)
        self.GLOBAL_VARS.FACE_POINTS_1 = []
        self.GLOBAL_VARS.FACE_POINTS_2 = []
        self.GLOBAL_VARS.LAST_NUM_LIST_FACE = 0

        gray1 = cv2.cvtColor(self.GLOBAL_VARS.IMAGE_1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(self.GLOBAL_VARS.IMAGE_2, cv2.COLOR_BGR2GRAY)

        rects1 = self.detector(gray1, 1)
        rects2 = self.detector(gray2, 1)

        try:
            rects1[0]
            rects2[0]
        except IndexError:
            self.onError("No faces were found in one of the images!")
            return

        max_area_1 = -1
        max_shape_1 = None
        for rect in rects1:
            shape = self.predictor(gray1, rect)
            shape = face_utils.shape_to_np(shape)
            (x, y, w, h) = face_utils.rect_to_bb(rect)
            area = (x + w) * (y + h)
            if area > max_area_1:
                max_area_1 = area
                max_shape_1 = shape

        max_area_2 = -1
        max_shape_2 = None
        for rect in rects2:
            shape = self.predictor(gray2, rect)
            shape = face_utils.shape_to_np(shape)
            (x, y, w, h) = face_utils.rect_to_bb(rect)
            area = (x + w) * (y + h)
            if area > max_area_2:
                max_area_2 = area
                max_shape_2 = shape

        points1 = max_shape_1.tolist()
        points2 = max_shape_2.tolist()

        for i in range(61):
            self.add2PtsList(points1[i], points2[i], 1)

    def onEntryEditCropped(self):
        if self.reversed_var.get() == 1:
            self.GLOBAL_VARS.CROPPED = True
        else:
            self.GLOBAL_VARS.CROPPED = False

    def onEntryEditOutputScale(self, t):
        if t == "":
            return True
        try:
            float(t)
        except:
            self.bell()
            self.output_scale_input.config(validate="none")
            self.output_scale_input.delete(self.output_scale_input.index("end"))
            self.output_scale_input.config(validate="key")
            return False
        if len(self.GLOBAL_VARS.IMAGES) == 0:
            self.output_scale_input.config(validate="none")
            self.output_scale_input.delete(self.output_scale_input.index("end"))
            self.output_scale_input.config(validate="key")
            self.onError(
                "You can change the scale value after you generate the animation"
            )
            return False
        elif (t.count(".") == 0) or (len(t) - t.index(".") - 1 <= 2):
            t = float(t)

            if t == 0:
                return True

            new_width = int(self.GLOBAL_VARS.IMAGES[0].shape[1] * t)
            new_height = int(self.GLOBAL_VARS.IMAGES[0].shape[0] * t)

            if 100 <= new_width <= 6000 and 100 <= new_height <= 6000:
                self.GLOBAL_VARS.SCALE = t
                self.output_size_label.configure(
                    text="Output GIF resolution: {}x{}".format(new_width, new_height)
                )
                return True
            else:
                self.output_scale_input.config(validate="none")
                self.output_scale_input.delete(self.output_scale_input.index("end"))
                self.output_scale_input.config(validate="key")
                self.onError("Output resolution must be from 100 to 6000 px")
                return False
        else:
            self.bell()
            self.output_scale_input.config(validate="none")
            self.output_scale_input.delete(self.output_scale_input.index("end"))
            self.output_scale_input.config(validate="key")
            return False

    def onEntryEditReversed(self):
        if self.reversed_var.get() == 1:
            self.GLOBAL_VARS.REVERSED = True
        else:
            self.GLOBAL_VARS.REVERSED = False

    def onEntryEditDelta(self, t):
        if not (t.isdigit()) and t != "":
            self.bell()
            self.delta_input.config(validate="none")
            self.delta_input.delete(self.delta_input.index("end"))
            self.delta_input.config(validate="key")
            return False
        elif t == "":
            return True

        t = int(t)
        if 1 <= t <= 100:
            self.GLOBAL_VARS.DELTA = t
            return True
        else:
            self.bell()
            self.delta_input.config(validate="none")
            self.delta_input.delete(self.delta_input.index("end"))
            self.delta_input.config(validate="key")
            return False

    def onEntryEditDuration(self, t):
        if t == "":
            return True
        try:
            float(t)
        except:
            self.bell()
            self.duration_input.config(validate="none")
            self.duration_input.delete(self.duration_input.index("end"))
            self.duration_input.config(validate="key")
            return False

        if (t.count(".") == 0) or (len(t) - t.index(".") - 1 <= 2):
            t = float(t)
            if 0 <= t <= 10:
                self.GLOBAL_VARS.DURATION = t
                return True
            else:
                self.bell()
                self.duration_input.config(validate="none")
                self.duration_input.delete(self.duration_input.index("end"))
                self.duration_input.config(validate="key")
                return False
        else:
            self.bell()
            self.duration_input.config(validate="none")
            self.duration_input.delete(self.duration_input.index("end"))
            self.duration_input.config(validate="key")
            return False

    def initMenu(self):
        menubar = Menu(self.master)
        self.master.config(menu=menubar)

        fileMenu = Menu(menubar)

        fileMenu.add_command(label="Save as", underline=0, command=self.save_file)
        fileMenu.add_command(label="About", underline=0, command=self.onAbout)
        fileMenu.add_command(label="Exit", underline=0, command=self.onExit)

        menubar.add_cascade(label="File", underline=0, menu=fileMenu)

    def bindKeys(self):
        self.bind_all("<Control-q>", self.onExit)
        self.bind_all("<Control-s>", self.save_file)

    def reload_img_1_canvas(self, img):
        temp_np_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        if temp_np_img.shape[0] > temp_np_img.shape[1]:
            temp_np_img = image_resize(
                temp_np_img, height=self.GLOBAL_VARS.IMG_MAX_HEIGHT
            )
        else:
            temp_np_img = image_resize(
                temp_np_img, width=self.GLOBAL_VARS.IMG_MAX_WIDTH
            )

        img_PIL = Image.fromarray(temp_np_img)
        self.GLOBAL_VARS.TK_IMAGE_1 = ImageTk.PhotoImage(img_PIL)

        self.img_canvas_1.create_image(
            temp_np_img.shape[1] // 2 + 2,
            temp_np_img.shape[0] // 2 + 2,
            image=self.GLOBAL_VARS.TK_IMAGE_1,
        )
        self.img_canvas_1.config(
            width=temp_np_img.shape[1] + 5, height=temp_np_img.shape[0] + 5
        )
        self.img_canvas_1.grid(row=1, column=0, sticky="news")

    def reload_img_2_canvas(self, img):
        temp_np_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        if temp_np_img.shape[0] > temp_np_img.shape[1]:
            temp_np_img = image_resize(
                temp_np_img, height=self.GLOBAL_VARS.IMG_MAX_HEIGHT
            )
        else:
            temp_np_img = image_resize(
                temp_np_img, width=self.GLOBAL_VARS.IMG_MAX_WIDTH
            )

        img_PIL = Image.fromarray(temp_np_img)
        self.GLOBAL_VARS.TK_IMAGE_2 = ImageTk.PhotoImage(img_PIL)

        self.img_canvas_2.create_image(
            temp_np_img.shape[1] // 2 + 2,
            temp_np_img.shape[0] // 2 + 2,
            image=self.GLOBAL_VARS.TK_IMAGE_2,
        )
        self.img_canvas_2.config(
            width=temp_np_img.shape[1] + 5, height=temp_np_img.shape[0] + 5
        )
        self.img_canvas_2.grid(row=1, column=1, sticky="news")

    def get_extreme_points(self, n):
        if n == 1:
            left_cor = min(self.GLOBAL_VARS.CORNER_POINTS_1, key=lambda p: p[0])
            right_cor = max(self.GLOBAL_VARS.CORNER_POINTS_1, key=lambda p: p[0])
            top_cor = min(self.GLOBAL_VARS.CORNER_POINTS_1, key=lambda p: p[1])
            bottom_cor = max(self.GLOBAL_VARS.CORNER_POINTS_1, key=lambda p: p[1])
            
            left_face = min(self.GLOBAL_VARS.FACE_POINTS_1, key=lambda p: p[0])
            right_face = max(self.GLOBAL_VARS.FACE_POINTS_1, key=lambda p: p[0])
            top_face = min(self.GLOBAL_VARS.FACE_POINTS_1, key=lambda p: p[1])
            bottom_face = max(self.GLOBAL_VARS.FACE_POINTS_1, key=lambda p: p[1])
            
            left_user = min(self.GLOBAL_VARS.USER_POINTS_1, key=lambda p: p[0])
            right_user = max(self.GLOBAL_VARS.USER_POINTS_1, key=lambda p: p[0])
            top_user = min(self.GLOBAL_VARS.USER_POINTS_1, key=lambda p: p[1])
            bottom_user = max(self.GLOBAL_VARS.USER_POINTS_1, key=lambda p: p[1])

            left = min(left_cor, left_face, left_user)
            right = max(right_cor, right_face, right_user)
            top = min(top_cor, top_face, top_user)
            bottom = max(bottom_cor, bottom_face, bottom_user)
        else:
            left_cor = min(self.GLOBAL_VARS.CORNER_POINTS_2, key=lambda p: p[0])
            right_cor = max(self.GLOBAL_VARS.CORNER_POINTS_2, key=lambda p: p[0])
            top_cor = min(self.GLOBAL_VARS.CORNER_POINTS_2, key=lambda p: p[1])
            bottom_cor = max(self.GLOBAL_VARS.CORNER_POINTS_2, key=lambda p: p[1])
            
            left_face = min(self.GLOBAL_VARS.FACE_POINTS_2, key=lambda p: p[0])
            right_face = max(self.GLOBAL_VARS.FACE_POINTS_2, key=lambda p: p[0])
            top_face = min(self.GLOBAL_VARS.FACE_POINTS_2, key=lambda p: p[1])
            bottom_face = max(self.GLOBAL_VARS.FACE_POINTS_2, key=lambda p: p[1])
            
            left_user = min(self.GLOBAL_VARS.USER_POINTS_2, key=lambda p: p[0])
            right_user = max(self.GLOBAL_VARS.USER_POINTS_2, key=lambda p: p[0])
            top_user = min(self.GLOBAL_VARS.USER_POINTS_2, key=lambda p: p[1])
            bottom_user = max(self.GLOBAL_VARS.USER_POINTS_2, key=lambda p: p[1])

            left = min(left_cor, left_face, left_user)
            right = max(right_cor, right_face, right_user)
            top = min(top_cor, top_face, top_user)
            bottom = max(bottom_cor, bottom_face, bottom_user)

        return (left, right, top, bottom)

    def update_gif_viewer(self, ind):
        if not self.GLOBAL_VARS.DO_ANIMATION:
            return

        if len(self.GLOBAL_VARS.IMAGES) != 0:
            frame = self.GLOBAL_VARS.IMAGES[ind]

            ind += 1
            if ind == len(self.GLOBAL_VARS.IMAGES):
                ind = 0

            if frame.shape[0] > frame.shape[1]:
                frame = image_resize(frame, height=self.GLOBAL_VARS.IMG_MAX_HEIGHT)
            else:
                frame = image_resize(frame, width=self.GLOBAL_VARS.IMG_MAX_WIDTH)

            img_PIL = Image.fromarray(frame)
            self.GLOBAL_VARS.CURR_FRAME = ImageTk.PhotoImage(img_PIL)

            self.gif_canvas.create_image(
                frame.shape[1] // 2 + 2,
                frame.shape[0] // 2 + 2,
                image=self.GLOBAL_VARS.CURR_FRAME,
            )
            self.gif_canvas.config(width=frame.shape[1] + 5, height=frame.shape[0] + 5)
            self.gif_canvas.grid(row=1, column=3, columnspan=2, sticky="news")
        else:
            self.reset_gif_viewer()
        if self.GLOBAL_VARS.DURATION is None or self.GLOBAL_VARS.DURATION == 0.0:
            self.after(150, self.update_gif_viewer, ind)
        else:
            self.after(
                int(self.GLOBAL_VARS.DURATION * 1000), self.update_gif_viewer, ind
            )

    def onImg1Click(self, event):
        if self.GLOBAL_VARS.IMAGE_1 is None or self.GLOBAL_VARS.IMAGE_2 is None:
            return

        ratio_x = (
            self.GLOBAL_VARS.IMAGE_1.shape[1] / self.GLOBAL_VARS.TK_IMAGE_1.width()
        )
        ratio_y = (
            self.GLOBAL_VARS.IMAGE_1.shape[0] / self.GLOBAL_VARS.TK_IMAGE_1.height()
        )
        self.GLOBAL_VARS.CANVAS_1_POS = [int(event.x * ratio_x), int(event.y * ratio_y)]

    def onImg2Click(self, event):
        if self.GLOBAL_VARS.IMAGE_1 is None or self.GLOBAL_VARS.IMAGE_2 is None:
            return
        if self.GLOBAL_VARS.CANVAS_1_POS is None:
            self.onError("You should firstly choose a point on the first image!")
            return

        ratio_x = (
            self.GLOBAL_VARS.IMAGE_2.shape[1] / self.GLOBAL_VARS.TK_IMAGE_2.width()
        )
        ratio_y = (
            self.GLOBAL_VARS.IMAGE_2.shape[0] / self.GLOBAL_VARS.TK_IMAGE_2.height()
        )
        self.GLOBAL_VARS.CANVAS_2_POS = [int(event.x * ratio_x), int(event.y * ratio_y)]

        self.add2PtsList(
            self.GLOBAL_VARS.CANVAS_1_POS, self.GLOBAL_VARS.CANVAS_2_POS, 2
        )

        self.GLOBAL_VARS.CANVAS_1_POS = None
        self.GLOBAL_VARS.CANVAS_2_POS = None

    def drawPoints(self):
        sel_corner = self.corner_points_list.curselection()
        sel_face = self.face_points_list.curselection()
        sel_user = self.user_points_list.curselection()

        if (
            self.GLOBAL_VARS.IMAGE_1 is not None
            and self.GLOBAL_VARS.IMAGE_2 is not None
        ):
            temp_img_1 = self.GLOBAL_VARS.IMAGE_1.copy()
            temp_img_2 = self.GLOBAL_VARS.IMAGE_2.copy()

            size_big = max(5, temp_img_1.shape[1] // 103)
            size_small = max(3, temp_img_1.shape[1] // 123)

            # CORNER
            for i in range(len(self.GLOBAL_VARS.CORNER_POINTS_1)):
                temp_img_1 = cv2.circle(
                    temp_img_1,
                    tuple(self.GLOBAL_VARS.CORNER_POINTS_1[i]),
                    size_small,
                    (0, 0, 255) if i in sel_corner else (0, 255, 0),
                    -1,
                )
                temp_img_1 = cv2.circle(
                    temp_img_1,
                    tuple(self.GLOBAL_VARS.CORNER_POINTS_1[i]),
                    size_big,
                    (0, 0, 0),
                    2,
                )
                temp_img_2 = cv2.circle(
                    temp_img_2,
                    tuple(self.GLOBAL_VARS.CORNER_POINTS_2[i]),
                    size_small,
                    (0, 0, 255) if i in sel_corner else (0, 255, 0),
                    -1,
                )
                temp_img_2 = cv2.circle(
                    temp_img_2,
                    tuple(self.GLOBAL_VARS.CORNER_POINTS_2[i]),
                    size_big,
                    (0, 0, 0),
                    2,
                )
            # FACE
            for i in range(len(self.GLOBAL_VARS.FACE_POINTS_1)):
                temp_img_1 = cv2.circle(
                    temp_img_1,
                    tuple(self.GLOBAL_VARS.FACE_POINTS_1[i]),
                    size_small,
                    (0, 0, 255) if i in sel_face else (0, 255, 0),
                    -1,
                )
                temp_img_1 = cv2.circle(
                    temp_img_1,
                    tuple(self.GLOBAL_VARS.FACE_POINTS_1[i]),
                    size_big,
                    (0, 0, 0),
                    2,
                )
                temp_img_2 = cv2.circle(
                    temp_img_2,
                    tuple(self.GLOBAL_VARS.FACE_POINTS_2[i]),
                    size_small,
                    (0, 0, 255) if i in sel_face else (0, 255, 0),
                    -1,
                )
                temp_img_2 = cv2.circle(
                    temp_img_2,
                    tuple(self.GLOBAL_VARS.FACE_POINTS_2[i]),
                    size_big,
                    (0, 0, 0),
                    2,
                )
            # USER
            for i in range(len(self.GLOBAL_VARS.USER_POINTS_1)):
                temp_img_1 = cv2.circle(
                    temp_img_1,
                    tuple(self.GLOBAL_VARS.USER_POINTS_1[i]),
                    size_small,
                    (0, 0, 255) if i in sel_user else (0, 255, 0),
                    -1,
                )
                temp_img_1 = cv2.circle(
                    temp_img_1,
                    tuple(self.GLOBAL_VARS.USER_POINTS_1[i]),
                    size_big,
                    (0, 0, 0),
                    2,
                )
                temp_img_2 = cv2.circle(
                    temp_img_2,
                    tuple(self.GLOBAL_VARS.USER_POINTS_2[i]),
                    size_small,
                    (0, 0, 255) if i in sel_user else (0, 255, 0),
                    -1,
                )
                temp_img_2 = cv2.circle(
                    temp_img_2,
                    tuple(self.GLOBAL_VARS.USER_POINTS_2[i]),
                    size_big,
                    (0, 0, 0),
                    2,
                )

            if self.GLOBAL_VARS.CANVAS_1_POS is not None:
                temp_img_1 = cv2.circle(
                    temp_img_1,
                    tuple(self.GLOBAL_VARS.CANVAS_1_POS),
                    size_small,
                    (255, 0, 0),
                    -1,
                )
                temp_img_1 = cv2.circle(
                    temp_img_1,
                    tuple(self.GLOBAL_VARS.CANVAS_1_POS),
                    size_big,
                    (0, 0, 0),
                    2,
                )
            if self.GLOBAL_VARS.CANVAS_2_POS is not None:
                temp_img_2 = cv2.circle(
                    temp_img_2,
                    tuple(self.GLOBAL_VARS.CANVAS_2_POS),
                    size_small,
                    (255, 0, 0),
                    -1,
                )
                temp_img_2 = cv2.circle(
                    temp_img_2,
                    tuple(self.GLOBAL_VARS.CANVAS_2_POS),
                    size_big,
                    (0, 0, 0),
                    2,
                )

            self.reload_img_1_canvas(temp_img_1)
            self.reload_img_2_canvas(temp_img_2)

        self.after(150, self.drawPoints)

    def reset_img_1_canvas(self):
        self.img_canvas_1 = Canvas(
            self,
            width=self.GLOBAL_VARS.IMG_MAX_WIDTH,
            height=self.GLOBAL_VARS.IMG_MAX_HEIGHT,
        )
        self.img_canvas_1.bind("<Button-1>", self.onImg1Click)
        self.img_canvas_1.grid(row=1, column=0, sticky="news")

    def reset_img_2_canvas(self):
        self.img_canvas_2 = Canvas(
            self,
            width=self.GLOBAL_VARS.IMG_MAX_WIDTH,
            height=self.GLOBAL_VARS.IMG_MAX_HEIGHT,
        )
        self.img_canvas_2.bind("<Button-1>", self.onImg2Click)
        self.img_canvas_2.grid(row=1, column=1, sticky="news")

    def reset_gif_viewer(self):
        self.gif_canvas = Canvas(self, width=350, height=350)
        self.gif_canvas.grid(row=1, column=3, columnspan=2, sticky="news")

    def start_gif_viewer(self):
        self.reset_gif_viewer()
        self.GLOBAL_VARS.DO_ANIMATION = True
        self.update_gif_viewer(0)

    def stop_gif_viewer(self):
        self.GLOBAL_VARS.DO_ANIMATION = False

    def open_file(self, *args):
        filepath = askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.tiff")],
            initialdir=self.GLOBAL_VARS.LAST_OPEN_PATH,
        )
        if not filepath:
            return
        filepath = Path(filepath)

        self.GLOBAL_VARS.LAST_OPEN_PATH = filepath.resolve().parent

        if len(args) == 1:
            self.GLOBAL_VARS.IMAGES = []
            self.deleteListPts()
            self.deleteAllPts()

            if args[0] == 1:
                self.GLOBAL_VARS.IMAGE_1 = cv2.imread(str(filepath))

                if self.GLOBAL_VARS.IMAGE_1 is None:
                    self.onError("Could not open the image!")
                    self.reset_img_1_canvas()
                    return
                if (
                    self.GLOBAL_VARS.IMAGE_1.shape[0] > 6000
                    or self.GLOBAL_VARS.IMAGE_1.shape[1] > 6000
                ):
                    self.onError(
                        "One of the dimensions of the first image is larger than 4000 px.\nThis can lead to serious memory problems.\nReverting..."
                    )
                    self.reset_img_1_canvas()
                    return

                if self.GLOBAL_VARS.IMAGE_2 is None:
                    self.reload_img_1_canvas(self.GLOBAL_VARS.IMAGE_1)
                else:
                    new_shape = (
                        max(
                            self.GLOBAL_VARS.IMAGE_1.shape[0],
                            self.GLOBAL_VARS.IMAGE_2.shape[0],
                        ),
                        max(
                            self.GLOBAL_VARS.IMAGE_1.shape[1],
                            self.GLOBAL_VARS.IMAGE_2.shape[1],
                        ),
                    )

                    self.GLOBAL_VARS.IMAGE_1 = resize(
                        self.GLOBAL_VARS.IMAGE_1, new_shape, True
                    )
                    self.GLOBAL_VARS.IMAGE_2 = resize(
                        self.GLOBAL_VARS.IMAGE_2, new_shape, True
                    )

                    self.reload_img_1_canvas(self.GLOBAL_VARS.IMAGE_1)
                    self.reload_img_2_canvas(self.GLOBAL_VARS.IMAGE_2)

                    self.addCorners()
            elif args[0] == 2:
                self.GLOBAL_VARS.IMAGE_2 = cv2.imread(str(filepath))

                if self.GLOBAL_VARS.IMAGE_2 is None:
                    self.onError("Could not open the image!")

                    self.reset_img_2_canvas()
                    return
                if (
                    self.GLOBAL_VARS.IMAGE_2.shape[0] > 6000
                    or self.GLOBAL_VARS.IMAGE_2.shape[1] > 6000
                ):
                    self.onError(
                        "One of the dimensions of the second image is larger than 4000 px.\nThis can lead to serious memory problems.\nReverting..."
                    )

                    self.reset_img_2_canvas()
                    return

                if self.GLOBAL_VARS.IMAGE_1 is None:
                    self.reload_img_2_canvas(self.GLOBAL_VARS.IMAGE_2)
                else:
                    new_shape = (
                        max(
                            self.GLOBAL_VARS.IMAGE_1.shape[0],
                            self.GLOBAL_VARS.IMAGE_2.shape[0],
                        ),
                        max(
                            self.GLOBAL_VARS.IMAGE_1.shape[1],
                            self.GLOBAL_VARS.IMAGE_2.shape[1],
                        ),
                    )

                    self.GLOBAL_VARS.IMAGE_1 = resize(
                        self.GLOBAL_VARS.IMAGE_1, new_shape, True
                    )
                    self.GLOBAL_VARS.IMAGE_2 = resize(
                        self.GLOBAL_VARS.IMAGE_2, new_shape, True
                    )

                    self.reload_img_1_canvas(self.GLOBAL_VARS.IMAGE_1)
                    self.reload_img_2_canvas(self.GLOBAL_VARS.IMAGE_2)

                    self.addCorners()

    def save_file(self, *args):
        filepath = asksaveasfilename(
            defaultextension="gif",
            filetypes=[("Graphics Interchange Format", "*.gif")],
            initialdir=self.GLOBAL_VARS.LAST_OPEN_PATH,
        )
        if not filepath:
            return
        filepath = Path(filepath)
        self.GLOBAL_VARS.LAST_OPEN_PATH = filepath.resolve().parent

        if len(self.GLOBAL_VARS.IMAGES) == 0:
            self.onError("Could not write the file. Empty animation!")
        else:
            images = []
            for i in range(len(self.GLOBAL_VARS.IMAGES)):
                scale = 1 if self.GLOBAL_VARS.SCALE is None else self.GLOBAL_VARS.SCALE
                images.append(
                    cv2.resize(
                        self.GLOBAL_VARS.IMAGES[i],
                        (
                            int(scale * self.GLOBAL_VARS.IMAGES[i].shape[1]),
                            int(scale * self.GLOBAL_VARS.IMAGES[i].shape[0]),
                        ),
                        interpolation=cv2.INTER_AREA,
                    )
                )
            try:
                imageio.mimsave(
                    str(filepath), images, duration=self.GLOBAL_VARS.DURATION
                )
            except:
                self.onError("Error occured while saving the file!")

    def onAbout(self):
        ABOUT_TEXT = "Image Morphing, v0.1.0\nBy Dmitriy Okoneshnikov, 2021\nVisit website: https://magicwinnie.github.io"
        self.onInfo(ABOUT_TEXT)

    def onExit(self, *args):
        self.quit()

    def onError(self, text):
        mbox.showerror("Error", text)

    def onWarn(self, text):
        mbox.showwarning("Warning", text)

    def onQuest(self, text):
        return mbox.askquestion("Question", text)

    def onInfo(self, text):
        mbox.showinfo("Information", text)


def main():
    root = Tk()
    ex = MainWindow()
    root.state("zoomed")
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.geometry("%dx%d" % (int(width * 0.75), int(height * 0.85)))
    root.mainloop()


if __name__ == "__main__":
    main()
