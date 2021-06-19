### TO-DO:
### *Auto face cropping
### *Scrollable MainWindow
import os
import sys
import getpass
import platform
from pathlib import Path
from functools import partial

import cv2
import dlib
import imageio
from imutils import face_utils
from PIL import Image, ImageTk

from tkinter import BooleanVar, IntVar, Tk, Menu, Text, PhotoImage, Canvas, Listbox
from tkinter import BOTH, CURRENT, INSERT, FIRST, END, RIGHT, Y, LEFT, VERTICAL, HORIZONTAL
from tkinter.ttk import Frame, Button, Scrollbar, Checkbutton, Entry, Label, Separator
from tkinter import messagebox as mbox
from tkinter.filedialog import askopenfilename, asksaveasfilename

from ImageMorpher import processFrame
from ImageResizer import image_resize, resize

class GlobalVariables:
    IMAGE_1  = None
    IMAGE_2  = None

    TK_IMAGE_1 = None
    TK_IMAGE_2 = None

    DELTA    = None
    DURATION = None
    REVERSED = True

    IMG_MAX_HEIGHT = 350
    IMG_MAX_WIDTH = 350

    LAST_NUM_LIST = 0

    if platform.system() == "Windows":
        LAST_OPEN_PATH = 'C:\\Users\\{}\\Pictures'.format(getpass.getuser())
        LAST_SAVE_PATH = 'C:\\Users\\{}\\Pictures'.format(getpass.getuser())
    elif platform.system() == "Linux":
        LAST_OPEN_PATH = '/home/{}/Pictures'.format(getpass.getuser())
        LAST_SAVE_PATH = '/home/{}/Pictures'.format(getpass.getuser())
    else:
        LAST_OPEN_PATH = ''
        LAST_SAVE_PATH = ''

    IMAGES = []
    CURR_FRAME = None
    DO_ANIMATION = True
    POINTS_1 = []
    POINTS_2 = []

class MainWindow(Frame):
    def __init__(self):
        super().__init__()

        self.GLOBAL_VARS = GlobalVariables()


        self.initUI()
        self.initMenu()
        self.bindKeys()

        self.detector = dlib.get_frontal_face_detector()
        try:
            self.predictor = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
        except:
            self.onError("Could not find the following file: 'shape_predictor_68_face_landmarks.dat'. Download the file and relaunch the app!")
            sys.exit(-1)
 
    def initUI(self):
        self.master.title("Image Morphing GUI")
        self.grid()


        btn_open_1 = Button(self, text="Open Image #1", command=partial(self.open_file, 1))
        btn_open_1.grid(row=0, column=0)

        btn_open_2 = Button(self, text="Open Image #2", command=partial(self.open_file, 2))
        btn_open_2.grid(row=0, column=1)


        self.reset_img_1_canvas()
        self.reset_img_2_canvas()


        ##### -------------------------------


        self.label_settings = Label(self, text="Settings", font='bold')
        self.label_settings.grid(row=0, column=2)

        self.settings_frame = Frame(self)
        self.settings_frame.grid(row=1, column=2, sticky='n')

        self.delta_label = Label(self.settings_frame, text="Delta (from 1 to 100): ")
        self.delta_label.grid(row=0, column=0, sticky="w")
        self.delta_vcmd = (self.register(self.onEntryEditDelta), '%P')
        self.delta_input = Entry(self.settings_frame, validate="key", validatecommand=self.delta_vcmd, width=5)
        self.delta_input.grid(row=0, column=1, sticky='w')

        self.duration_label = Label(self.settings_frame, text="Duration (from 0.01 to 10.00): ")
        self.duration_label.grid(row=1, column=0, sticky="w")
        self.duration_vcmd = (self.register(self.onEntryEditDuration), '%P')
        self.duration_input = Entry(self.settings_frame, validate="key", validatecommand=self.duration_vcmd, width=5)
        self.duration_input.grid(row=1, column=1, sticky='w')

        self.reversed_label = Label(self.settings_frame, text="Reversed? ")
        self.reversed_label.grid(row=2, column=0, sticky="w")
        self.reversed_var = BooleanVar()
        self.reversed_var.set(1)
        self.reversed_input = Checkbutton(self.settings_frame, variable=self.reversed_var, onvalue=1, offvalue=0, command=self.onEntryEditReversed)
        self.reversed_input.grid(row=2, column=1)

        self.face_rec_gen_btn = Button(self.settings_frame, text="Generate points from face recognition", command=self.onFaceRecBtn)
        self.face_rec_gen_btn.grid(row=4, column=0, columnspan=2, sticky='ew')

        self.start_btn = Button(self.settings_frame, text="Start", command=self.onStartBtn)
        self.start_btn.grid(row=5, column=0, columnspan=2, sticky='ew')

        self.save_btn = Button(self.settings_frame, text="Save animation", command=self.save_file)
        self.save_btn.grid(row=6, column=0, columnspan=2, sticky='ew')

        self.Reset_btn = Button(self.settings_frame, text="Reset", command=self.onResetBtn)
        self.Reset_btn.grid(row=7, column=0, columnspan=2, sticky='ew')


        ##### -------------------------------


        self.points_label = Label(self, text="List of pairs", font='bold')
        self.points_label.grid(row=0, column=3)

        self.points_container = Frame(self)
        self.points_container.grid(row=1, column=3, sticky='news')

        self.points_canvas = Canvas(self.points_container)
        self.points_canvas.grid(row=0, column=0, sticky="news")

        self.points_scrollbar = Scrollbar(self.points_canvas)
        self.points_scrollbar.grid(row=0, column=1, sticky='ns')

        self.points_list = Listbox(self.points_canvas, yscrollcommand=self.points_scrollbar.set, height=15, selectmode="extended")
        self.points_list.bind('<Delete>', self.deletePtsList)

        self.points_list.grid(row=0, column=0, sticky='ns')
        self.points_scrollbar.config(command = self.points_list.yview)

        
        self.gif_label = Label(self, text="Animation", font='bold')
        self.gif_label.grid(row=2, column=2, columnspan=2)

        self.start_gif_viewer()

        self.initSeparators()

    def initSeparators(self):
        return
        Separator(self, orient=VERTICAL).grid(column=0, row=0, rowspan=4, sticky='nse')
        Separator(self, orient=VERTICAL).grid(column=1, row=0, rowspan=4, sticky='nse')
        Separator(self, orient=VERTICAL).grid(column=2, row=0, rowspan=2, sticky='nse')

        Separator(self, orient=HORIZONTAL).grid(column=0, row=1, columnspan=4, sticky='ewn')
        Separator(self, orient=HORIZONTAL).grid(column=0, row=2, columnspan=5, sticky='ewn')
        Separator(self, orient=HORIZONTAL).grid(column=0, row=3, columnspan=4, sticky='ewn')

    def add2PtsList(self, pt1, pt2):
        self.points_list.insert(END, "Pair #" + str(self.GLOBAL_VARS.LAST_NUM_LIST))
        self.GLOBAL_VARS.LAST_NUM_LIST += 1

        self.GLOBAL_VARS.POINTS_1.append(pt1)
        self.GLOBAL_VARS.POINTS_2.append(pt2)

    def deletePtsList(self, *args):
        sel = self.points_list.curselection()
        for index in sel[::-1]:
            self.points_list.delete(index)
            self.GLOBAL_VARS.POINTS_1.pop(index)
            self.GLOBAL_VARS.POINTS_2.pop(index)

        if self.points_list.size() == 0:
            self.GLOBAL_VARS.LAST_NUM_LIST = 0

    def deleteAllPts(self):
        self.points_list.delete(0, END)
        self.GLOBAL_VARS.POINTS_1 = []
        self.GLOBAL_VARS.POINTS_2 = []
        self.GLOBAL_VARS.LAST_NUM_LIST = 0

    def onResetBtn(self):
        self.face_rec_gen_btn['state'] = 'normal'
        self.GLOBAL_VARS.IMAGES = []
        self.GLOBAL_VARS.IMAGE_1 = None
        self.GLOBAL_VARS.IMAGE_2 = None
        
        self.deleteAllPts()
        self.reset_img_1_canvas()
        self.reset_img_2_canvas()
        self.stop_gif_viewer()
        self.start_gif_viewer()

        self.initSeparators()

    def onStartBtn(self):
        if self.GLOBAL_VARS.IMAGE_1 is None or self.GLOBAL_VARS.IMAGE_2 is None:
            self.onError("One of the images is not chosen!")
            return
        if self.GLOBAL_VARS.DELTA is None or self.GLOBAL_VARS.DURATION is None:
            self.onError("Delta or duration value is not set!")
            return     

        self.GLOBAL_VARS.IMAGES = []
        for i in range(0, 101, self.GLOBAL_VARS.DELTA):
            alpha = min(i / 100, 1.0)
            frame = processFrame(self.GLOBAL_VARS.IMAGE_1, self.GLOBAL_VARS.IMAGE_2, alpha, self.GLOBAL_VARS.POINTS_1, self.GLOBAL_VARS.POINTS_2)
            self.GLOBAL_VARS.IMAGES.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        if self.GLOBAL_VARS.REVERSED:
            self.GLOBAL_VARS.IMAGES += list(reversed(self.GLOBAL_VARS.IMAGES))

    def addCorners(self):
        self.add2PtsList([self.GLOBAL_VARS.IMAGE_1.shape[1] - 1, 0], [self.GLOBAL_VARS.IMAGE_2.shape[1] - 1, 0])
        self.add2PtsList([self.GLOBAL_VARS.IMAGE_1.shape[1] - 1, self.GLOBAL_VARS.IMAGE_1.shape[0] - 1], [self.GLOBAL_VARS.IMAGE_2.shape[1] - 1, self.GLOBAL_VARS.IMAGE_2.shape[0] - 1])
        self.add2PtsList([0, self.GLOBAL_VARS.IMAGE_1.shape[0] - 1], [0, self.GLOBAL_VARS.IMAGE_2.shape[0] - 1])
        self.add2PtsList([0, 0], [0, 0])

        self.add2PtsList([self.GLOBAL_VARS.IMAGE_1.shape[1]//2 - 1, 0], [self.GLOBAL_VARS.IMAGE_2.shape[1]//2 - 1, 0]) 
        self.add2PtsList([0, self.GLOBAL_VARS.IMAGE_1.shape[0]//2 - 1], [0, self.GLOBAL_VARS.IMAGE_2.shape[0]//2 - 1])
        self.add2PtsList([self.GLOBAL_VARS.IMAGE_1.shape[1]//2 - 1, self.GLOBAL_VARS.IMAGE_1.shape[0] - 1], [self.GLOBAL_VARS.IMAGE_2.shape[1]//2 - 1, self.GLOBAL_VARS.IMAGE_2.shape[0] - 1])
        self.add2PtsList([self.GLOBAL_VARS.IMAGE_1.shape[1] - 1, self.GLOBAL_VARS.IMAGE_1.shape[0]//2 - 1], [self.GLOBAL_VARS.IMAGE_2.shape[1] - 1, self.GLOBAL_VARS.IMAGE_2.shape[0]//2 - 1])

    def onFaceRecBtn(self):
        self.onInfo("Several faces may be recognized.\nOnly the largest faces will be used!")

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
            self.add2PtsList(points1[i], points2[i])

        self.face_rec_gen_btn['state'] = 'disabled'

    def onEntryEditReversed(self):
        if self.reversed_var.get() == 1:
            self.GLOBAL_VARS.REVERSED = True
        else:
            self.GLOBAL_VARS.REVERSED = False

    def onEntryEditDelta(self, t):
        if not(t.isdigit()) and t != "":
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
            temp = float(t)
        except:
            self.bell()
            self.duration_input.config(validate="none")
            self.duration_input.delete(self.duration_input.index("end"))
            self.duration_input.config(validate="key")
            return False
        
        if t.count('.') == 0:
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
        elif len(t) - t.index('.') - 1 <= 2:
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



    def reload_img_1_canvas(self):
        temp_np_img = cv2.cvtColor(self.GLOBAL_VARS.IMAGE_1, cv2.COLOR_BGR2RGB)

        if temp_np_img.shape[0] > temp_np_img.shape[1]:
            temp_np_img = image_resize(temp_np_img,  height=self.GLOBAL_VARS.IMG_MAX_HEIGHT)
        else:
            temp_np_img = image_resize(temp_np_img,  width=self.GLOBAL_VARS.IMG_MAX_WIDTH)

        img_PIL = Image.fromarray(temp_np_img)
        self.GLOBAL_VARS.TK_IMAGE_1 = ImageTk.PhotoImage(img_PIL)
        
        self.img_canvas_1.create_image(temp_np_img.shape[1]//2 + 2, temp_np_img.shape[0]//2 + 2, image=self.GLOBAL_VARS.TK_IMAGE_1)
        self.img_canvas_1.config(width=temp_np_img.shape[1] + 5, height=temp_np_img.shape[0] + 5)
        self.img_canvas_1.grid(row=1, column=0, sticky='news')

    def reload_img_2_canvas(self):
        temp_np_img = cv2.cvtColor(self.GLOBAL_VARS.IMAGE_2, cv2.COLOR_BGR2RGB)

        if temp_np_img.shape[0] > temp_np_img.shape[1]:
            temp_np_img = image_resize(temp_np_img,  height=self.GLOBAL_VARS.IMG_MAX_HEIGHT)
        else:
            temp_np_img = image_resize(temp_np_img,  width=self.GLOBAL_VARS.IMG_MAX_WIDTH)

        img_PIL = Image.fromarray(temp_np_img)
        self.GLOBAL_VARS.TK_IMAGE_2 = ImageTk.PhotoImage(img_PIL)
        
        self.img_canvas_2.create_image(temp_np_img.shape[1]//2 + 2, temp_np_img.shape[0]//2 + 2, image=self.GLOBAL_VARS.TK_IMAGE_2)
        self.img_canvas_2.config(width=temp_np_img.shape[1] + 5, height=temp_np_img.shape[0] + 5)
        self.img_canvas_2.grid(row=1, column=1, sticky='news')

    def update_gif_viewer(self, ind):
        if not self.GLOBAL_VARS.DO_ANIMATION:
            return

        if len(self.GLOBAL_VARS.IMAGES) != 0:
            frame = self.GLOBAL_VARS.IMAGES[ind]

            ind += 1
            if ind == len(self.GLOBAL_VARS.IMAGES):
                ind = 0

            if frame.shape[0] > frame.shape[1]:
                frame = image_resize(frame,  height=self.GLOBAL_VARS.IMG_MAX_HEIGHT)
            else:
                frame = image_resize(frame,  width=self.GLOBAL_VARS.IMG_MAX_WIDTH)

            img_PIL = Image.fromarray(frame)
            self.GLOBAL_VARS.CURR_FRAME = ImageTk.PhotoImage(img_PIL)
            
            self.gif_canvas.create_image(frame.shape[1]//2 + 2, frame.shape[0]//2 + 2, image=self.GLOBAL_VARS.CURR_FRAME)
            self.gif_canvas.config(width=frame.shape[1] + 5, height=frame.shape[0] + 5)
            self.gif_canvas.grid(row=3, column=2, sticky='news')
        else:
            self.reset_gif_viewer()
        if self.GLOBAL_VARS.DURATION is None or self.GLOBAL_VARS.DURATION == 0.0 :
            self.after(150, self.update_gif_viewer, ind)
        else:
            self.after(int(self.GLOBAL_VARS.DURATION*1000), self.update_gif_viewer, ind)

    def reset_img_1_canvas(self):
        self.img_canvas_1 = Canvas(self,  width=self.GLOBAL_VARS.IMG_MAX_WIDTH ,  height=self.GLOBAL_VARS.IMG_MAX_HEIGHT)
        self.img_canvas_1.grid(row=1, column=0, sticky='news')

    def reset_img_2_canvas(self):
        self.img_canvas_2 = Canvas(self,  width=self.GLOBAL_VARS.IMG_MAX_WIDTH,  height=self.GLOBAL_VARS.IMG_MAX_HEIGHT)
        self.img_canvas_2.grid(row=1, column=1, sticky='news')

    def reset_gif_viewer(self):
        self.gif_canvas = Canvas(self, width=350, height=350)
        self.gif_canvas.grid(row=3, column=2, columnspan=2, sticky='news')
    
    def start_gif_viewer(self):
        self.reset_gif_viewer()
        self.GLOBAL_VARS.DO_ANIMATION = True
        self.update_gif_viewer(0)
    
    def stop_gif_viewer(self):
        self.GLOBAL_VARS.DO_ANIMATION = False

        
    def open_file(self, *args):
        filepath = askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.tiff")],
            initialdir=self.GLOBAL_VARS.LAST_OPEN_PATH
        )
        if not filepath:
            return
        filepath = Path(filepath)

        self.GLOBAL_VARS.LAST_OPEN_PATH = filepath.resolve().parent
        
        if len(args) == 1:
            self.face_rec_gen_btn['state'] = 'normal'
            self.GLOBAL_VARS.IMAGES = []
            self.GLOBAL_VARS.POINTS_1 = []
            self.GLOBAL_VARS.POINTS_2 = []
            self.deleteAllPts()

            if args[0] == 1:
                self.GLOBAL_VARS.IMAGE_1 = cv2.imread(str(filepath))

                if self.GLOBAL_VARS.IMAGE_1 is None:
                    self.onError("Could not open the image!")
                    self.reset_img_1_canvas()
                    return
                if self.GLOBAL_VARS.IMAGE_1.shape[0] > 4000 or self.GLOBAL_VARS.IMAGE_1.shape[1] > 4000:
                    self.onError("One of the dimensions of the first image is larger than 4000 px.\nThis can lead to serious memory problems.\nReverting...")
                    self.reset_img_1_canvas()
                    return
                
                if self.GLOBAL_VARS.IMAGE_2 is None:
                    self.reload_img_1_canvas()
                else:
                    new_shape = (
                        max(self.GLOBAL_VARS.IMAGE_1.shape[0], self.GLOBAL_VARS.IMAGE_2.shape[0]),
                        max(self.GLOBAL_VARS.IMAGE_1.shape[1], self.GLOBAL_VARS.IMAGE_2.shape[1])
                    )

                    self.GLOBAL_VARS.IMAGE_1 = resize(self.GLOBAL_VARS.IMAGE_1, new_shape, True)
                    self.GLOBAL_VARS.IMAGE_2 = resize(self.GLOBAL_VARS.IMAGE_2, new_shape, True)

                    self.reload_img_1_canvas()
                    self.reload_img_2_canvas()

                    self.addCorners()    
            elif args[0] == 2:
                self.GLOBAL_VARS.IMAGE_2 = cv2.imread(str(filepath))
                
                if self.GLOBAL_VARS.IMAGE_2 is None:
                    self.onError("Could not open the image!")

                    self.reset_img_2_canvas()
                    return
                if self.GLOBAL_VARS.IMAGE_2.shape[0] > 4000 or self.GLOBAL_VARS.IMAGE_2.shape[1] > 4000:
                    self.onError("One of the dimensions of the second image is larger than 4000 px.\nThis can lead to serious memory problems.\nReverting...")

                    self.reset_img_2_canvas()
                    return


                if self.GLOBAL_VARS.IMAGE_1 is None:
                    self.reload_img_2_canvas()
                else:
                    new_shape = (
                        max(self.GLOBAL_VARS.IMAGE_1.shape[0], self.GLOBAL_VARS.IMAGE_2.shape[0]),
                        max(self.GLOBAL_VARS.IMAGE_1.shape[1], self.GLOBAL_VARS.IMAGE_2.shape[1])
                    )

                    self.GLOBAL_VARS.IMAGE_1 = resize(self.GLOBAL_VARS.IMAGE_1, new_shape, True)
                    self.GLOBAL_VARS.IMAGE_2 = resize(self.GLOBAL_VARS.IMAGE_2, new_shape, True)

                    self.reload_img_1_canvas()
                    self.reload_img_2_canvas()

                    self.addCorners()

    def save_file(self, *args):
        filepath = asksaveasfilename(
            defaultextension="gif",
            filetypes=[("Graphics Interchange Format", "*.gif")],
            initialdir=self.GLOBAL_VARS.LAST_SAVE_PATH
        )
        if not filepath:
            return
        filepath = Path(filepath)
        self.GLOBAL_VARS.LAST_SAVE_PATH = filepath.resolve().parent
        
        if len(self.GLOBAL_VARS.IMAGES) == 0:
            self.onError("Could not write the file. Empty animation!")
        else:
            try:
                imageio.mimsave(str(filepath), self.GLOBAL_VARS.IMAGES, duration=self.GLOBAL_VARS.DURATION)
            except:
                self.onError("Error occured while saving the file!")


    def onAbout(self):
        ABOUT_TEXT = "Image Morphing, v0.0.1\nBy Dmitriy Okoneshnikov, 2021\nVisit website: https://magicwinnie.github.io"
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
    root.state('zoomed')
    width = root.winfo_screenwidth() 
    height = root.winfo_screenheight()
    root.geometry("%dx%d" % (int(width*0.75), int(height*0.85)))
    root.mainloop()
 
 
if __name__ == '__main__':
    main()