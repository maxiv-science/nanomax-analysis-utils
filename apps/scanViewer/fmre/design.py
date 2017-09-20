# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'design.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(1082, 678)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/logos/N.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.gridLayout_2 = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout_2.setObjectName(_fromUtf8("gridLayout_2"))
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.plotWidget = FmrePlot(self.centralwidget)
        self.plotWidget.setObjectName(_fromUtf8("plotWidget"))
        self.gridLayout.addWidget(self.plotWidget, 2, 0, 1, 3)
        self.runButton = QtGui.QPushButton(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.runButton.sizePolicy().hasHeightForWidth())
        self.runButton.setSizePolicy(sizePolicy)
        self.runButton.setMaximumSize(QtCore.QSize(10000, 16777215))
        self.runButton.setAutoDefault(True)
        self.runButton.setDefault(True)
        self.runButton.setObjectName(_fromUtf8("runButton"))
        self.gridLayout.addWidget(self.runButton, 1, 2, 1, 1)
        self.browseButton = QtGui.QPushButton(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.browseButton.sizePolicy().hasHeightForWidth())
        self.browseButton.setSizePolicy(sizePolicy)
        self.browseButton.setMaximumSize(QtCore.QSize(1000000, 16777215))
        self.browseButton.setObjectName(_fromUtf8("browseButton"))
        self.gridLayout.addWidget(self.browseButton, 1, 1, 1, 1)
        self.filenameBox = QtGui.QLineEdit(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.filenameBox.sizePolicy().hasHeightForWidth())
        self.filenameBox.setSizePolicy(sizePolicy)
        self.filenameBox.setMinimumSize(QtCore.QSize(100, 0))
        self.filenameBox.setBaseSize(QtCore.QSize(200, 0))
        self.filenameBox.setPlaceholderText(_fromUtf8(""))
        self.filenameBox.setObjectName(_fromUtf8("filenameBox"))
        self.gridLayout.addWidget(self.filenameBox, 1, 0, 1, 1)
        self.optionsGrid = QtGui.QGridLayout()
        self.optionsGrid.setObjectName(_fromUtf8("optionsGrid"))
        self.gridLayout.addLayout(self.optionsGrid, 0, 0, 1, 3)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1082, 27))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        MainWindow.setTabOrder(self.filenameBox, self.browseButton)
        MainWindow.setTabOrder(self.browseButton, self.runButton)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "NanoMAX Scan Viewer", None))
        self.runButton.setToolTip(_translate("MainWindow", "<html><head/><body><p>Go!</p></body></html>", None))
        self.runButton.setText(_translate("MainWindow", "Run", None))
        self.browseButton.setToolTip(_translate("MainWindow", "<html><head/><body><p>Browse for data files</p></body></html>", None))
        self.browseButton.setText(_translate("MainWindow", "Browse...", None))
        self.filenameBox.setText(_translate("MainWindow", "<input ptyr file>", None))

from fmre_plot import FmrePlot
