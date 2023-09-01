import json
import subprocess
import time
import turtle
import cv2
import matplotlib.pyplot as plt
import numpy as np
import urllib
from skimage import transform, data, io, measure
from skimage.filters import threshold_otsu
from skimage.morphology import square, erosion, dilation
from PIL import Image, ImageDraw
import math
import concurrent.futures
import socket
import concurrent.futures


class BaseSolution:

    def __init__(self):
        self.render = []

    def load_frame(self):
        # Nacteni jednoho snimku ze serveru

        # Load the fisheye-distorted image
        # https://i.ibb.co/d7Wgk4B/image.png
        # https://i.ibb.co/sKp0Z6g/image.png
        # http://192.168.100.22/image/image.png
        while True:
            try:
                image = io.imread("http://192.168.100.22/image/image.png")

                break  # Only triggered if input is valid...
            except Exception as error:
                print(error)

        im_res = cv2.resize(image, (1920, 1440))

        # Define the distortion coefficients for experimentation
        k1 = -0.013  # Radial distortion coefficient
        k2 = 0.00014  # Radial distortion coefficient
        p1 = -0.0025  # Tangential distortion coefficient
        p2 = 0.0015  # Tangential distortion coefficient

        # Define the parameters for manual correction
        fov = 160  # Field of view (in degrees)
        dst_size = im_res.shape[:2][::-1]  # Destination image size (width, height)

        # Calculate the focal length based on the field of view
        focal_length = dst_size[0] / (2 * np.tan(np.radians(fov) / 2))

        # Generate a simple perspective transformation matrix
        K = np.array([[focal_length, 0, dst_size[0] / 2],
                      [0, focal_length, dst_size[1] / 2],
                      [0, 0, 1]])
        dist_coefs = np.array([k1, k2, p1, p2])

        # Undistort the image using the specified coefficients
        undistorted_image = cv2.undistort(im_res, K, dist_coefs)
        return undistorted_image

    def detect_playground(self, image):
        # Detekce hriste z nacteneho snimku

        im_bin = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        im_bin = cv2.GaussianBlur(im_bin, (5, 5), 0)
        im_bin = cv2.adaptiveThreshold(im_bin, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 201, 2)

        kernel = np.ones((5, 5), np.uint8)
        im_bin = cv2.erode(im_bin, kernel, iterations=10)
        im_bin = cv2.dilate(im_bin, kernel, iterations=10)

        contours, _ = cv2.findContours(im_bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        sorted_contours = sorted(contours, key=cv2.contourArea, reverse=True)

        rect = cv2.minAreaRect(sorted_contours[0])
        box = cv2.boxPoints(rect)
        box = np.intp(box) # type: ignore
        # print(box)

        # mask = np.zeros(image.shape)
        # cv2.drawContours(mask, sorted_contours, -1, (255, 255, 255), 1)
        # cv2.drawContours(mask, [box], 0, (255, 0, 0), 1)

        src_pts = np.array(box, dtype=np.float32)
        dst_pts = np.array([[0, 0], [1000, 0], [1000, 1000], [0, 1000]], dtype=np.float32)

        M = cv2.getPerspectiveTransform(src_pts, dst_pts)
        warp = cv2.warpPerspective(image, M, (1000, 1000))

        leftups = np.zeros((8, 8), dtype=tuple)
        cellsize = 100
        # f, subplt = plt.subplots(8, 8)  # REMOVE AFTER DEBUG!!!!!!!!!!!!!!!!!!
        for i, x in enumerate(range(cellsize, 9 * cellsize, cellsize)):
            for j, y in enumerate(range(cellsize, 9 * cellsize, cellsize)):
                leftups[i, j] = (x, y)
                # subplt[j, i].imshow(warp[y:y+cellsize, x:x+cellsize])  # REMOVE AFTER DEBUG!!!!!!!!!!!!!!!!!!

        # print(leftups)  # REMOVE AFTER DEBUG!!!!!!!!!!!!!!!!!!
        # plt.show()  # REMOVE AFTER DEBUG!!!!!!!!!!!!!!!!!!

        return warp, leftups, cellsize

    def detect_robot(self, image):
        dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
        parameters = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(dictionary, parameters)  # Prepare the CV2 aruco detector object

        image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # Convert a color image to grayscale

        markerCorners, markerIds, rejectedCandidates = detector.detectMarkers(
            image_gray)  # Detect the aruco markers from the grayscale image

        corners = np.array(markerCorners, np.int32)  # Convert markerCorners to a numpy array with type np.int32

        orientation = None  # N = 0, E = 1, S = 2, W = 3
        if len(markerCorners):  # If there are any corners make a bounding polygon
            front = corners[0][0]
            cv2.polylines(image,corners,True,(255,0,0),2) # type: ignore
            vector = [front[0][0]-front[1][0], front[0][1]-front[1][1]]
            vector_perpendicular = [-vector[1],vector[0]]
            angle = ((math.atan2(vector_perpendicular[0],vector_perpendicular[1]) * 180 / math.pi) - 180) * -1
            orientation = int((angle + 45) % 360 // 90) # CHATGPT CAME TO THE RESCUE
            # print(f"Vector: {vector}, Perpendicular: {vector_perpendicular}, Angle: {angle}, Orientation {orientation}")
            cv2.line(image, front[0], front[0]-vector, (0,255,0), 10)
            cv2.line(image, front[0], front[0]-vector_perpendicular, (0,0,255), 10)
            image = cv2.putText(image, f"Angle:{str(round(angle))}, Ori: {orientation}", front[0], cv2.FONT_HERSHEY_DUPLEX, 1, (255,0,0), 1, cv2.LINE_AA)
            # self.render.append([image, "detect_robot"])
            return corners[0][0], orientation

        # print(f"Corners: {corners}, IDs: {markerIds}, Main line: {front}") # Was for debug, best to keep it here

    def recognize_objects(self, image, leftups, cellsize):
        verdict = []
        for line in leftups:
            for cell in line:
                bottomright = (
                    cell[0] + cellsize,
                    cell[1] + cellsize)  # Calculate the coords of the bottom right corner of the cell
                image_cell = image[cell[0]:bottomright[0], cell[1]:bottomright[1]]  # Cut the cell from the image
                channels = []
                for i in range(3):
                    channels.append(image_cell[:, :, i] < threshold_otsu(
                        image_cell[:, :, i]))  # Threshold the idividual images and put them in a nicely indexable array
                    channels[i] = erosion(channels[i], square(3))  # Erode in all the channels
                mask = np.logical_and(channels[0], np.logical_and(channels[1], channels[
                    2]))  # Logical AND all the channels together to get a mask
                shape = []
                for i in range(3):
                    shape.append(np.logical_xor(mask, channels[i]))  # XOR the individual channels with the mask
                    shape[i] = erosion(shape[i], square(5))  # Erode the noise away
                blue, green, red = np.sum(shape[0]), np.sum(shape[1]), np.sum(
                    shape[2])  # Count all the pixels in the thresholded channels
                if red > 300 and green > 300 and blue < 300:
                    verdict.append(["red", ""])
                elif red > 300 and green < 300 and blue > 300:
                    verdict.append(["green", ""])
                elif red < 300 and blue > 300:
                    verdict.append(["blue", ""])
                else:
                    verdict.append(["white", ""])
                contours = None
                for i in range(3):
                    contours, _ = cv2.findContours(shape[i].astype(np.uint8), cv2.RETR_TREE,
                                                   cv2.CHAIN_APPROX_SIMPLE)  # Find countours
                    cv2.drawContours(image_cell, contours, -1, (0, 255, 0),
                                     3)  # Draw them so i won't want to kill myself when i debug this shit
                    for contour in contours:
                        length = cv2.arcLength(contour, True)
                        if length > 50:
                            approx_shape = cv2.approxPolyDP(contour, 0.03 * length, True)  # Approx the shape and length
                            # image_cell = cv2.putText(image_cell, str(len(approx_shape)), (40,20+(20*i)), cv2.FONT_HERSHEY_DUPLEX, 1, (0,0,255), 1, cv2.LINE_AA)
                            if 3 < len(approx_shape) < 6:
                                verdict[-1][1] = "square"
                            elif 7 < len(approx_shape) < 12:
                                verdict[-1][1] = "star"
                # image_cell = cv2.putText(image_cell, str(verdict[-1]), (0,20), cv2.FONT_HERSHEY_DUPLEX, 0.4, (255,0,0), 1, cv2.LINE_AA)
                # image_cell = cv2.putText(image_cell, str(blue), (20,30), cv2.FONT_HERSHEY_DUPLEX, 1, (0,0,255), 1, cv2.LINE_AA)
                # image_cell = cv2.putText(image_cell, str(green), (20,60), cv2.FONT_HERSHEY_DUPLEX, 1, (0,255,0), 1, cv2.LINE_AA)
                # image_cell = cv2.putText(image_cell, str(red), (20,90), cv2.FONT_HERSHEY_DUPLEX, 1, (255,0,0), 1, cv2.LINE_AA)
                # self.render.append([shape[0], "", True])
                # self.render.append([shape[1], "", True])
                # self.render.append([shape[2], "", True])
                # self.render.append([mask, ""])
                # self.render.append([image_cell, ""])
        return np.reshape(verdict, (8, 8, 2))

    def analyze_playground(self, robot, objects, cellsize):
        # Analyza dat vytezenych ze snimku
        pole = objects.copy()

        rob_pos = (round(robot[0][:, 0].mean()) // cellsize - 1, round(robot[0][:, 1].mean()) // cellsize - 1)
        pole[rob_pos[::-1]] = ["robot", robot[1]]

        return pole
      
    def generate_path(self, pole):

        def extract_number_and_letters(input_str):
            try:
                num_chars = []
                letter_chars = []
                is_number = True

                for c in input_str:
                    if (c.isnumeric() and is_number) or c=='-':
                        num_chars.append(c)
                    else:
                        is_number = False
                        letter_chars.append(c)

                number = int(''.join(num_chars))
                letters = ''.join(letter_chars)

                return number, letters
            except:
                return -1000000, ''


        start = (7,4) # y,x
        finish = (1,1) # y,x
        e = -10000
        map = [
            [ e, e,+3, e, e,0 ,0 ,0 ],
            [+3,0 ,0 ,0 , e,0 , e,+3],
            [+3, e, e,+6, e,+6, e,+3],
            [0 ,0 , e,0 ,0 ,0 , e,0 ],
            [0 ,0 ,0 ,0 , e,0 ,0 ,0 ],
            [0 , e, e,+3, e, e, e,0 ],
            [0 ,0 , e, e, e,+6, e,0 ],
            [+1000 ,0 , e,0 ,0 ,0 ,0 ,0 ],
        ]
        start_direction = 0

        # end of test inputs


        # convert to my format
        for x in range(0,8):
            for y in range(0,8):
                if pole[x][y][0] == 'red' and pole[x][y][1] == 'square':
                    map[x][y] = e
                if pole[x][y][0] == 'red' and pole[x][y][1] == 'star':
                    map[x][y] = +6
                if pole[x][y][0] == 'blue' and pole[x][y][1] == 'square':
                    map[x][y] = +3
                if pole[x][y][0] == 'white' and pole[x][y][1] == '':
                    map[x][y] = 0
                if pole[x][y][0] == 'robot':
                    map[x][y] = 0
                
                if pole[x][y][0] == 'robot':
                    start = (x,y)
                    start_direction = int(pole[x][y][1])
                
                if pole[x][y][0] == 'green' and pole[x][y][1] == 'square':
                    map[x][y] = 0
                    finish = (x,y)


        # end of making inputs

        data = {
            "map": map,
            "start": start,
            "finish": finish,
            "start_dir": start_direction
        }
        with open("data.json", "w") as f:
            json.dump(data, f)

        def run_rust_binary():
            result = subprocess.run("rust/target/release/rust", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
            return result

        # start measuring time
        time_start = time.time()

        # Number of threads
        num_instances = 12

        best_score = -10000
        best_path = ""

        # Create a ThreadPoolExecutor with the desired number of threads
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_instances) as executor:
            # Submit the task multiple times
            future_to_instance = {executor.submit(run_rust_binary): i for i in range(num_instances)}

            # Wait for all tasks to complete
            for future in concurrent.futures.as_completed(future_to_instance):
                instance_id = future_to_instance[future]
                try:
                    result = future.result()
                    print(f"Instance {instance_id} completed with stdout: {result.stdout}, and stderr: {result.stderr}")
                    if best_score < extract_number_and_letters(result.stdout)[0]:
                        # found new best path
                        best_score = extract_number_and_letters(result.stdout)[0]
                        best_path = extract_number_and_letters(result.stdout)[1]
                except Exception as e:
                    print(f"Instance {instance_id} raised an exception: {e}")
        
        result = best_path
        print("\n\n Best score: " + str(best_score) + ", with the path:\n" + best_path)

        # end measuring time
        time_end = time.time()
        print("time:", time_end - time_start)

        # center the turtle, does not currently work
        # turtle.penup()
        # turtle.forward(start[1]*100-400)
        # turtle.right(90)
        # turtle.forward(start[0]*100-400)
        # turtle.pendown()
        # turtle.turtlesize(3.0,3.0,3.0)

        if start_direction == 0:
            turtle.setheading(0)
        if start_direction == 1:
            turtle.setheading(90)
        if start_direction == 2:
            turtle.setheading(180)
        if start_direction == 3:
            turtle.setheading(270)
        turtle.left(90)
        # for c in path_to_lrfb(best_path, start_dir=start_direction):
        for c in (result):
            if c == "F":
                turtle.forward(40)
            if c == "L":
                turtle.left(90)
            if c == "R":
                turtle.right(90)
        turtle.mainloop()

        return result

    def visualize(self, pole, path):
        robot = Image.open("assets/robot.png")
        blue_square = Image.open("assets/blue_square.png")
        green_square = Image.open("assets/green_square.png")
        red_square = Image.open("assets/red_square.png")
        red_star = Image.open("assets/red_star.png")
        arrow = Image.open("assets/arrow.png")

        arr_pos = (0, 0)

        rows = len(pole)
        cols = len(pole[0])
        cellsize = 100

        final = Image.new("RGB", (cols * cellsize, rows * cellsize), (255, 255, 255))
        # Draw some lines
        draw = ImageDraw.Draw(final)
        y_start = 0
        y_end = final.height

        x_start = 0
        x_end = final.width

        # Draw columns:
        for x in range(0, x_end + 1, cellsize):
            line = ((x-1, y_start), (x-1, y_end))
            draw.line(line, fill=(127, 127, 127), width=10)

        # Draw rows:
        for y in range(0, y_end + 1, cellsize):
            line = ((x_start, y-1), (x_end, y-1))
            draw.line(line, fill=(127, 127, 127), width=10)

        del draw

        for j, row in enumerate(pole):
            for i, cell in enumerate(row):
                x, y = i * cellsize + 5, j * cellsize + 5
                if cell[0] == "robot":
                    robot.rotate(-90 * int(cell[1]), Image.NEAREST, expand=True)
                    final.paste(robot, (x, y), robot)

                    arr_pos = (x, y)
                    arrow.rotate(-90 * int(cell[1]), Image.NEAREST, expand=True)

                elif all(cell == ["blue", "square"]):
                    final.paste(blue_square, (x, y), blue_square)
                elif all(cell == ["green", "square"]):
                    final.paste(green_square, (x, y), green_square)
                elif all(cell == ["red", "square"]):
                    final.paste(red_square, (x, y), red_square)
                elif all(cell == ["red", "star"]):
                    final.paste(red_star, (x, y), red_star)

        # x, y = robot
        # for char in path:
        #     if char = ""

        self.render.append([final, "lolik", False])

    def send_solution(self, instructions: str):
        if len(self.render):
            count = len(self.render)
            x = math.floor(math.sqrt(count))
            y = math.ceil(count / x)
            fig, subplot = plt.subplots(x, y)
            fig.suptitle('Lampone 2023')
            subplot = np.reshape(subplot, x * y)
            for i in range(count):
                if len(self.render[i]) == 2 or self.render[i][2] == False:
                    subplot[i].imshow(self.render[i][0])
                else:
                    subplot[i].imshow(self.render[i][0], cmap="binary")
                subplot[i].set_title(self.render[i][1])
                subplot[i].axis("off")
            plt.show()
        
        udp_ip = "localhost" # debug only, replace with real address
        udp_port = 5005
        msg = str(instructions).encode("ascii")

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(msg, (udp_ip, udp_port))


        # Poslani reseni na server pomoci UTP spojeni.

    def solve(self):
        print("load frame")
        image = self.load_frame()
        print("detect playground")
        fixed_image, leftups, cellsize = self.detect_playground(image)
        print("detect robot")
        robot = self.detect_robot(fixed_image.copy())
        print("recognize objects")
        objects = self.recognize_objects(fixed_image, leftups, cellsize)
        print("analyze playground")
        pole = self.analyze_playground(robot, objects, cellsize)
        print("generate path and send solution")
        path = self.generate_path(pole)
        self.visualize(pole, path)
        self.send_solution(path)
        pass



if __name__ == "__main__":
    solution = BaseSolution()
    solution.solve()
