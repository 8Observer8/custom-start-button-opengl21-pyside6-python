import numpy as np
from OpenGL.GL import *
from PySide6.QtCore import QFile, QIODevice, QJsonDocument, Qt
from PySide6.QtGui import QImage, QMatrix4x4, QSurfaceFormat, QVector3D
from PySide6.QtOpenGL import (QOpenGLBuffer, QOpenGLShader, QOpenGLShaderProgram,
                            QOpenGLTexture, QOpenGLWindow)


class MainWindow(QOpenGLWindow):

    def __init__(self):
        super().__init__()
        self.resize(350, 350)
        self.setTitle("OpenGL 2.1, PySide6, Python")

        # Set format
        format = QSurfaceFormat()
        format.setSamples(4)
        format.setSwapInterval(1)
        self.frameSwapped.connect(self.update)
        self.setFormat(format)

        self.buttonPosition = QVector3D(100, 100, 0)
        self.buttonSize = QVector3D(114, 38, 1)
        self.mouseX = 0
        self.mouseY = 0
        self.clicked = False
        self.pressed = False

        # Model matrix
        self.modelMatrix = QMatrix4x4()
        # View matrix
        self.viewMatrix = QMatrix4x4()
        self.viewMatrix.lookAt(QVector3D(0, 0, 1), QVector3D(0, 0, 0),
            QVector3D(0, 1, 0))
        # Projection matrix
        self.projMatrix = QMatrix4x4()
        self.projMatrix.ortho(0, 200, 0, 200, 1, -1)
        # ProjView matrix
        self.projViewMatrix = self.projMatrix * self.viewMatrix
        # MvpMatrix
        self.mvpMatrix = None

    def initializeGL(self):
        glClearColor(0.77, 0.64, 0.52, 1) # Light brown

        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.program = QOpenGLShaderProgram(self)
        self.program.addShaderFromSourceFile(QOpenGLShader.ShaderTypeBit.Vertex,
            "assets/shaders/texture.vert")
        self.program.addShaderFromSourceFile(QOpenGLShader.ShaderTypeBit.Fragment,
            "assets/shaders/texture.frag")
        self.program.link()
        self.program.bind()

        self.uClickLocation = self.program.uniformLocation("uClick")
        self.uPickColorLocation = self.program.uniformLocation("uPickColor")
        self.uMvpMatrixLocation = self.program.uniformLocation("uMvpMatrix")
        self.program.setUniformValue(self.uClickLocation, False)

        file = QFile("assets/textures/button.json")
        content = None
        if file.open(QIODevice.OpenModeFlag.ReadOnly):
            content = file.readAll()
        file.close()
        doc = QJsonDocument.fromJson(content)
        root = doc.object()
        # Width and height
        tw = root["meta"]["size"]["w"]
        th = root["meta"]["size"]["h"]
        # Frames
        frames = root["frames"]
        # Button normal
        buttonNormal = frames["button-normal.png"]
        frame1 = buttonNormal["frame"]
        f1x = frame1["x"]
        f1y = frame1["y"]
        f1w = frame1["w"]
        f1h = frame1["h"]
        # Button active
        buttonActive = frames["button-active.png"]
        frame2 = buttonActive["frame"]
        f2x = frame2["x"]
        f2y = frame2["y"]
        f2w = frame2["w"]
        f2h = frame2["h"]

        vertPositions = np.array([
            -0.5, -0.5,
            0.5, -0.5,
            -0.5, 0.5,
            0.5, 0.5,
            -0.5, -0.5,
            0.5, -0.5,
            -0.5, 0.5,
            0.5, 0.5
        ], dtype=np.float32)
        self.vertPosBuffer = QOpenGLBuffer()
        self.vertPosBuffer.create()
        self.vertPosBuffer.bind()
        self.vertPosBuffer.allocate(vertPositions, len(vertPositions) * 4)
        aPositionLocation = self.program.attributeLocation("aPosition")
        self.program.setAttributeBuffer(aPositionLocation, GL_FLOAT, 0, 2)
        self.program.enableAttributeArray(aPositionLocation)

        texCoords = np.array([
            f1x / tw, (f1y + f1h) / th, # First button texture
            (f1x + f1w) / tw, (f1y + f1h) / th,
            f1x / tw, f1y / th,
            (f1x + f1w) / tw, f1y / th,
            f2x / tw, (f2y + f2h) / th, # Second button texture
            (f2x + f2w) / tw, (f2y + f2h) / th,
            f2x / tw, f2y / th,
            (f2x + f2w) / tw, f2y / th
        ], dtype=np.float32)
        self.texCoordBuffer = QOpenGLBuffer()
        self.texCoordBuffer.create()
        self.texCoordBuffer.bind()
        self.texCoordBuffer.allocate(texCoords, len(texCoords) * 4)
        aTexCoordLocation = self.program.attributeLocation("aTexCoord")
        self.program.setAttributeBuffer(aTexCoordLocation, GL_FLOAT, 0, 2)
        self.program.enableAttributeArray(aTexCoordLocation)

        self.texture = QOpenGLTexture(QOpenGLTexture.Target.Target2D)
        self.texture.create()
        self.texture.setData(QImage("assets/textures/button.png"))
        self.texture.setMinMagFilters(QOpenGLTexture.Filter.Linear,
            QOpenGLTexture.Filter.Linear)
        self.texture.setWrapMode(QOpenGLTexture.WrapMode.ClampToEdge)

    def paintGL(self):
        if self.clicked:
            self.clicked = False

            glClear(GL_COLOR_BUFFER_BIT)
            self.program.bind()

            self.program.setUniformValue(self.uClickLocation, True)
            self.program.setUniformValue(self.uPickColorLocation, QVector3D(1, 0, 0))

            self.modelMatrix.setToIdentity()
            self.modelMatrix.translate(self.buttonPosition)
            self.modelMatrix.rotate(30, QVector3D(0, 0, 1))
            self.modelMatrix.scale(self.buttonSize)
            self.mvpMatrix = self.projViewMatrix * self.modelMatrix
            self.program.setUniformValue(self.uMvpMatrixLocation, self.mvpMatrix)
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)

            pixels = np.array([0, 0, 0], dtype=np.ubyte)
            glReadPixels(self.mouseX, self.mouseY, 1, 1, GL_RGB, GL_UNSIGNED_BYTE, pixels)
            r = pixels[0]
            g = pixels[1]
            b = pixels[2]
            # print(r, g, b)
            if r == 255 and g == 0 and b == 0:
                print("clicked")
                self.pressed = True

            self.program.setUniformValue(self.uClickLocation, False)

        glClear(GL_COLOR_BUFFER_BIT)
        self.program.bind()
        self.texture.bind()

        self.modelMatrix.setToIdentity()
        self.modelMatrix.translate(self.buttonPosition)
        self.modelMatrix.rotate(0, QVector3D(0, 0, 1))
        self.modelMatrix.scale(self.buttonSize)
        self.mvpMatrix = self.projViewMatrix * self.modelMatrix
        self.program.setUniformValue(self.uMvpMatrixLocation, self.mvpMatrix)
        if not self.pressed:
            glDrawArrays(GL_TRIANGLE_STRIP, 0, 4)
        else:
            glDrawArrays(GL_TRIANGLE_STRIP, 4, 4)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouseX = event.pos().x()
            self.mouseY = self.width() - event.pos().y() - 1
            self.clicked = True

    def mouseReleaseEvent(self, event):
        self.pressed = False

    def closeEvent(self, event):
        self.texture.destroy()
