# compteur clignement d'œil sans class
import cv2
import cvzone
from cvzone.FaceMeshModule import FaceMeshDetector
from cvzone.PlotModule import LivePlot

cap = cv2.VideoCapture(0)
detector = FaceMeshDetector(maxFaces=1)
idListleft = [22, 23, 24, 26, 110, 157, 158, 159, 160, 161, 130, 243]  # Points des yeux
idListRight = [362, 385, 387, 263, 249, 466, 467, 468, 469, 470, 359, 454]  # Points des yeux
plotY = LivePlot(640, 480, [20, 50])
Ratiolistleft = []
Ratiolistright = []
blinkCount = 0
counter = 0


while True:
    if cap.get(cv2.CAP_PROP_POS_FRAMES) == cap.get(cv2.CAP_PROP_FRAME_COUNT):
        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        success, img = cap.read()
        img, face = detector.findFaceMesh(img)

        if face:
            face = face[0]
            for id in idListleft:
                cv2.circle(img, face[id], 5, (255, 0, 255), cv2.FILLED)
            leftUp = face[159]
            leftDown = face[23]
            leftLeft = face[130]
            leftRight = face[243]
            lenghtverL, _ = detector.findDistance(leftUp, leftDown)
            lenghthorL, _ = detector.findDistance(leftLeft, leftRight)

            ratio = int((lenghtverL / lenghthorL) * 100)
            Ratiolistleft.append(ratio)
            if len(Ratiolistleft) > 2:
                Ratiolistleft.pop(0)
            ratioAvg = sum(Ratiolistleft) / len(Ratiolistleft)

            rightUp = face[386]
            rightDown = face[253]
            rightLeft = face[362]
            rightRight = face[454]
            lenghtverR, _ = detector.findDistance(rightUp, rightDown)
            lenghthorR, _ = detector.findDistance(rightLeft, rightRight)

            ratioR = int((lenghtverR / lenghthorR) * 100)
            Ratiolistright.append(ratioR)
            if len(Ratiolistright) > 2:
                Ratiolistright.pop(0)
            ratioAvgR = sum(Ratiolistright) / len(Ratiolistright)

            if ratioAvg < 35 and counter == 0:
                blinkCount += 1
                counter = 1
            if counter != 0:
                counter += 1
                if counter > 10:
                    counter = 0    

            cv2.putText(img, f'Blinks: {blinkCount}', (50, 100), cv2.FONT_HERSHEY_PLAIN, 3, (255, 0, 255), 3)

            cv2.line(img, leftUp, leftDown, (0, 200, 0), 3)

            imgplot = plotY.update(ratioAvg)
            imageStack = cvzone.stackImages([img, imgplot], 2, 1)
        else:
            imageStack = cvzone.stackImages([img, img], 2, 1) 

    cv2.imshow("Image", imageStack)
    cv2.waitKey(1)