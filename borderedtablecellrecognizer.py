import cv2
import numpy as np
import matplotlib.pyplot as plt


class Points:
    def __init__(self):
        self._x1 = []
        self._x2 = []

    def add(self, x1, x2):
        self._x1.append(x1)
        self._x2.append(x2)

    def remove_all(self):
        self._x1 = []
        self._x2 = []

    def get_len(self):
        return len(self._x1)

    def get_best_line_coordinates(self):
        return min(self._x1), max(self._x2)  # the widest line


def display(I):
    plt.imshow(I, cmap='gray')
    plt.show()


def preprocessing(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    bw = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, 1)
    bw = cv2.bitwise_not(bw)  # turning black to white and white to black
    return bw


def vertical_line(bw):
    vertical = bw.copy()
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 15))
    # morfology:
    vertical = cv2.erode(vertical, vertical_kernel)
    vertical = cv2.dilate(vertical, vertical_kernel)
    vertical = cv2.dilate(vertical, (1, 1), iterations=8)
    vertical = cv2.erode(vertical, (1, 1), iterations=7)
    # line detection:
    ver_lines = cv2.HoughLinesP(vertical, rho=1, theta=np.pi / 180, threshold=20, minLineLength=20, maxLineGap=2)
    if ver_lines is None:
        return None
    temp_line = []
    for line in ver_lines:
        for x1, y1, x2, y2 in line:
            temp_line.append([x1, y1, x2, y2])
    ver_lines = sorted(temp_line, key=lambda x: x[0])
    # best fitting line selection:
    points = Points()
    last_x = -999
    res = []
    i = 0
    for x1, y1, x2, y2 in ver_lines:
        if last_x <= x1 <= last_x + 15:
            points.add(y1, y2)
        else:
            if i != 0 and points.get_len() != 0:
                left, right = points.get_best_line_coordinates()
                res.append([last_x, left - 5, last_x, right - 5])
            last_x = x1
            points.remove_all()
            points.add(y1, y2)
            i += 1
    left, right = points.get_best_line_coordinates()
    res.append([last_x, left - 5, last_x, right - 5])
    return res


def horizontal_line(bw):
    horizontal = bw.copy()
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 1))
    # morfology:
    horizontal = cv2.erode(horizontal, horizontal_kernel)
    horizontal = cv2.dilate(horizontal, horizontal_kernel)
    horizontal = cv2.dilate(horizontal, (1, 1), iterations=5)
    horizontal = cv2.erode(horizontal, (1, 1), iterations=5)
    # line detection:
    hor_lines = cv2.HoughLinesP(horizontal, rho=1, theta=np.pi / 180, threshold=100, minLineLength=30,
                                maxLineGap=3)
    if hor_lines is None:
        return None
    temp_line = []
    for line in hor_lines:
        for x1, y1, x2, y2 in line:
            temp_line.append([x1, y1 - 5, x2, y2 - 5])
    hor_lines = sorted(temp_line, key=lambda x: x[1])
    # best fitting line selection:
    '''
    clue jest takie: mamy posortowane po y, teraz dzielimy na sekcje wysokie o 10 i wybieramy najlepsze linie
    jak znajdzie sie jakas linia z poza zakresu, dodajemy najlepsza jako reprezentatywna dany obszar
    else w forze nizej wywola sie zawsze na poczatku
    '''
    points = Points()
    last_y = -999
    res = []
    i = 0
    for x1, y1, x2, y2 in hor_lines:
        if last_y <= y1 <= last_y + 15:
            points.add(x1, x2)
        else:
            if i != 0 and points.get_len() != 0:
                left, right = points.get_best_line_coordinates()
                res.append([left, last_y, right, last_y])
            last_y = y1
            points.remove_all()
            points.add(x1, x2)
            i += 1
    left, right = points.get_best_line_coordinates()
    res.append([left, last_y, right, last_y])  # przypadek jednej linii?
    return res


def line_intersection(x1, y1, x2, y2, x3, y3, x4, y4):
    if (x1 >= x3 - 5 or x1 >= x3 + 5) and (x1 <= x4 + 5 or x1 <= x4 - 5) and (y3 + 8 >= min(y1, y2) or y3 - 5 >= min(y1, y2)) and y3 <= max(y1, y2) + 5:
        return x1, y3
    return -1, -1


def bordered(coordinates, image):  # [x1,y1,x2,y2]
    boxed_image = image[coordinates[1] - 10:coordinates[3] + 10, coordinates[0] - 10:coordinates[2] + 10]
    bw = preprocessing(boxed_image)
    horizontal_lines = horizontal_line(bw)
    vertical_lines = vertical_line(bw)
    # print("VERTICAL ->" + str(vertical_lines))
    # print("HORIZONTAl ->" + str(horizontal_lines))

    table = bw.copy()
    # find intersection points:
    i = 0
    points = []
    for x1, y1, x2, y2 in vertical_lines:
        point = []
        for x3, y3, x4, y4 in horizontal_lines:
            x, y = line_intersection(x1, y1, x2, y2, x3, y3, x4, y4)
            if x != -1 and y != -1:
                i += 1
                point.append([x, y])
        points.append(point)
    # bounding boxes
    box = []
    last_cache = []
    for i, row in enumerate(points):
        row_n = len(row)
        current_value = []
        for j, col in enumerate(row):
            if j == row_n - 1:
                break
            next_col = row[j + 1]
            if i == 0:
                last_cache.append([col[0], col[1], next_col[0], next_col[1], 9999, 9999, 9999, 9999])
            else:
                current_value.append([col[0], col[1], next_col[0], next_col[1], 9999, 9999, 9999, 9999])
                flag = 1
                index = []
                for k, last in enumerate(last_cache):
                    if col[1] == last[1] and last_cache[k][4] == 9999:
                        last_cache[k][4] = col[0]
                        last_cache[k][5] = col[1]
                        if last_cache[k][4] != 9999 and last_cache[k][6] != 9999:
                            box.append(last_cache[k])
                            index.append(k)
                            flag = 1
                    if next_col[1] == last[3] and last_cache[k][6] == 9999:
                        last_cache[k][6] = next_col[0]
                        last_cache[k][7] = next_col[1]
                        if last_cache[k][4] != 9999 and last_cache[k][6] != 9999:
                            box.append(last_cache[k])
                            index.append(k)
                            flag = 1
                    if len(last_cache) != 0:
                        if last_cache[k][4] == 9999 or last_cache[k][6] == 9999:
                            flag = 0
                for k in index:
                    last_cache.pop(k)
                if flag == 0:
                    for last in last_cache:
                        if last[4] == 9999 or last[6] == 9999:
                            current_value.append(last)
        if i != 0:
            last_cache = current_value
    return box

if __name__ == '__main__':
    img = cv2.imread("271232799_1108162776675302_5322818247320402492_n.jpg")
    coords = [171, 849, 1420, 887]
    boxes = bordered(coords, img)
