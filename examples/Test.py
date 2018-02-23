
import os
import numpy
import cv2

from AnnulusDetector import *

def imshow(image):
    cv2.namedWindow("Image", cv2.WINDOW_NORMAL)
    cv2.imshow("Image", image)
    cv2.waitKey()


def draw_annuli(image, annuli):
    if annuli is None:
        return

    for c, e1, e2, _, _ in annuli:
        u = c.round().astype(np.int)
        cv2.rectangle(image, tuple(u - [1,1]), tuple(u + [1, 1]), (0, 255, 0))
        cv2.ellipse(image, e1, (0, 255, 0))
        cv2.ellipse(image, e2, (0, 0, 255))


def draw_numbering(image, H, grid, color):
    if H is None:
        return

    Hinv = np.linalg.inv(H)
    for g in grid:
        x = map_point(Hinv, g).astype(np.int)
        cv2.putText(image, str(g.astype(np.int)), tuple(x), cv2.FONT_HERSHEY_SIMPLEX, 0.3, color)


def draw_grid(image, H, grid):
    if H is None:
        return

    Hinv = np.linalg.inv(H)
    for x in grid:
        x1 = map_point(Hinv, x + [-0.5, -0.5]).astype(np.int)
        x2 = map_point(Hinv, x + [ 0.5, -0.5]).astype(np.int)
        x3 = map_point(Hinv, x + [ 0.5,  0.5]).astype(np.int)
        x4 = map_point(Hinv, x + [-0.5,  0.5]).astype(np.int)

        cv2.line(image, tuple(x1), tuple(x2), (255, 0, 0))
        cv2.line(image, tuple(x2), tuple(x3), (255, 0, 0))
        cv2.line(image, tuple(x3), tuple(x4), (255, 0, 0))
        cv2.line(image, tuple(x4), tuple(x1), (255, 0, 0))



def map_point(H, x):
    y = np.dot(H, np.hstack((x, 1)))
    return y[0:2] / y[2]

def threshold_image(image, block_size = (64, 64), step_size = (32, 32)):
    binary = np.zeros_like(image)
    for row in range(0, image.shape[0], step_size[0]):
        for col in range(0, image.shape[1], step_size[1]):
            im = image[row:row + block_size[0], col:col + block_size[1]]
            if np.ptp(im) < 32:
                if np.min(im) > 64:
                    binary[row:row + block_size[0], col:col + block_size[1]] = 255
            else:
                _, bin = cv2.threshold(im, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
                binary[row:row + block_size[0], col:col + block_size[1]] = bin
    return binary


def detect_annuli(gray, binary):
    detect = AnnulusDetection()
    #detect.add_filter(annuli_shape_filter())
    #detect.add_filter(cross_ratio_filter(inner_circle_diameter = 0.01, outer_circle_diameter = 0.02))
    #detect.add_filter(neighbor_filter(outer_circle_diameter = 0.02, marker_spacing = 0.03))
    annuli = detect.detect(gray,  binary, high_quality = False)

    return annuli

def detect_grid(ellipse):
    grid = Grid(outer_circle_diamater = 0.02, marker_spacing = 0.03)
    H = grid.find_grid(ellipse)
    if H is None:
        return None, None
    grid = map_ellipse(H, ellipse)
    return H, grid




def process(image):
    image = image.copy()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.blur(gray, (5, 5))
    #binary = threshold_image(gray, (64, 64))
    binary = binarize(gray, 65)

    detector = AnnulusDetection()
    detector.add_filter(annuli_shape_filter())
    detector.add_filter(cross_ratio_filter(inner_circle_diameter = 0.01, outer_circle_diameter = 0.02, tolerance = 0.2))
    detector.add_filter(neighbor_filter(outer_circle_diameter = 0.02, marker_spacing = 0.03))
    annuli = detector.detect(gray,  binary, high_quality = True)
    points = np.array([m[0] for m in annuli])

    draw_annuli(image, annuli)

    grid = Grid(outer_circle_diamater = 0.02, marker_spacing = 0.03)
    H, idx, grid, pixel = grid.find_grid(annuli)
    if H is not None:
        draw_grid(image, H, grid)
        

        M = find_numbering(binary, H, grid)
        if M is not None:
            H, grid = transformed_homography(M, pixel, grid)
            color = (0, 255, 0)
        else:
            color = (0, 0, 255)
            
        draw_numbering(image, H, grid, color)
    
    return image




def single(image_file):
    image = cv2.imread(image_file)
    image = process(image)
    imshow(image)


def video():

    cam = cv2.VideoCapture(0)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1270)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)


    cv2.namedWindow("Image", cv2.WINDOW_NORMAL)
    while True:
        key = cv2.waitKey(10)
        _, image = cam.read()
        if key == ord("q"):
            break
        elif key == ord("s"):
            cv2.imwrite("image.png", image)
    
        try:
            image = process(image)
        except:
            print("error")
            cv2.imwrite("error.png", image)

        cv2.imshow("Image", image);



#single("image.png")
video()


