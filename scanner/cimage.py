from PyQt5 import QtGui, QtCore

class CImage(QtGui.QPixmap):
    def __init__(self, width, height):
        super().__init__(width, height)
        # 默认参数初始化
        self.setImageParameters(0, 0, 0, 0, 0, 0)

    def setImageParameters(self, Zstart, Zrange, XRangeAtStart, XRangeAtEnd, WidthX, HeightZ):
        """
        设置图像参数，全部转为float类型，兼容字符串或数值输入
        """
        self.m_dZstart = float(Zstart)
        self.m_dZrange = float(Zrange)
        self.m_dXRangeAtStart = float(XRangeAtStart)
        self.m_dXRangeAtEnd = float(XRangeAtEnd)
        self.m_dWidthX = float(WidthX)
        self.m_dHeightZ = float(HeightZ)

    def drawImage(self, X, Z, I, count):
        """
        绘制数据点分布到当前pixmap。
        X, Z, I: 数组类型，长度为count
        """
        self.fill(QtCore.Qt.black)
        painter = QtGui.QPainter(self)
        # 画Z分布（白色点）
        painter.setPen(QtCore.Qt.white)
        if Z is not None and len(Z) >= count:
            scaleX = self.width() / self.m_dXRangeAtEnd if self.m_dXRangeAtEnd else 1
            scaleY = self.height() / self.m_dZrange if self.m_dZrange else 1
            for i in range(count):
                x = self.width() - int(scaleX * (X[i] + self.m_dXRangeAtEnd / 2))
                if (Z[i] - self.m_dZstart) > 0:
                    z = self.height() - int(scaleY * (Z[i] - self.m_dZstart))
                    if 0 <= x < self.width() and 0 <= z < self.height():
                        painter.drawPoint(x, z)
        # 画强度分布（黄色点）
        painter.setPen(QtCore.Qt.yellow)
        if I is not None and len(I) >= count:
            scaleX = self.width() / self.m_dXRangeAtEnd if self.m_dXRangeAtEnd else 1
            for i in range(count):
                x = self.width() - int(scaleX * (X[i] + self.m_dXRangeAtEnd / 2))
                z = int(self.height() * (1 - I[i] / 1023))
                if 0 <= x < self.width() and 0 <= z < self.height():
                    painter.drawPoint(x, z)
        painter.end()