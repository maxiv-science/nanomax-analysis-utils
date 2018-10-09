# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'design.ui'
#
# Created by: PyQt4 UI code generator 4.11.4
#
# WARNING! All changes made in this file will be lost!

#from PyQt4 import QtCore, QtGui
from silx.gui import qt as QtCore
QtGui = QtCore
QtWidgets = QtCore

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
        self.tabWidget = QtGui.QTabWidget(self.centralwidget)
        self.tabWidget.setFocusPolicy(QtCore.Qt.TabFocus)
        self.tabWidget.setObjectName(_fromUtf8("tabWidget"))
        self.tab = QtGui.QWidget()
        self.tab.setObjectName(_fromUtf8("tab"))
        self.optionsGrid = QtGui.QGridLayout(self.tab)
        self.optionsGrid.setObjectName(_fromUtf8("optionsGrid"))
        self.tabWidget.addTab(self.tab, _fromUtf8(""))
        self.roi = QtGui.QWidget()
        self.roi.setObjectName(_fromUtf8("roi"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.roi)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.xrdWidget = XrdWidget(self.roi)
        self.xrdWidget.setObjectName(_fromUtf8("xrdWidget"))
        self.horizontalLayout.addWidget(self.xrdWidget)
        self.tabWidget.addTab(self.roi, _fromUtf8(""))
        self.com = QtGui.QWidget()
        self.com.setObjectName(_fromUtf8("com"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.com)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.comWidget = ComWidget(self.com)
        self.comWidget.setObjectName(_fromUtf8("comWidget"))
        self.horizontalLayout_2.addWidget(self.comWidget)
        self.tabWidget.addTab(self.com, _fromUtf8(""))
        self.xrf = QtGui.QWidget()
        self.xrf.setObjectName(_fromUtf8("xrf"))
        self.horizontalLayout_3 = QtGui.QHBoxLayout(self.xrf)
        self.horizontalLayout_3.setObjectName(_fromUtf8("horizontalLayout_3"))
        self.xrfWidget = XrfWidget(self.xrf)
        self.xrfWidget.setObjectName(_fromUtf8("xrfWidget"))
        self.horizontalLayout_3.addWidget(self.xrfWidget)
        self.tabWidget.addTab(self.xrf, _fromUtf8(""))
        self.gridLayout_2.addWidget(self.tabWidget, 1, 0, 1, 1)
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.scanClassBox = QtGui.QComboBox(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scanClassBox.sizePolicy().hasHeightForWidth())
        self.scanClassBox.setSizePolicy(sizePolicy)
        self.scanClassBox.setMinimumSize(QtCore.QSize(100, 0))
        self.scanClassBox.setBaseSize(QtCore.QSize(200, 0))
        self.scanClassBox.setMaxVisibleItems(100)
        self.scanClassBox.setSizeAdjustPolicy(QtGui.QComboBox.AdjustToContents)
        self.scanClassBox.setObjectName(_fromUtf8("scanClassBox"))
        self.gridLayout.addWidget(self.scanClassBox, 0, 1, 1, 1)
        self.logoLabel = QtGui.QLabel(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.logoLabel.sizePolicy().hasHeightForWidth())
        self.logoLabel.setSizePolicy(sizePolicy)
        self.logoLabel.setMinimumSize(QtCore.QSize(260, 0))
        self.logoLabel.setText(_fromUtf8(""))
        self.logoLabel.setPixmap(QtGui.QPixmap(_fromUtf8(":/logos/nanomax.png")))
        self.logoLabel.setObjectName(_fromUtf8("logoLabel"))
        self.gridLayout.addWidget(self.logoLabel, 0, 0, 3, 1)
        self.loadButton = QtGui.QPushButton(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.loadButton.sizePolicy().hasHeightForWidth())
        self.loadButton.setSizePolicy(sizePolicy)
        self.loadButton.setMaximumSize(QtCore.QSize(10000, 16777215))
        self.loadButton.setAutoDefault(True)
        self.loadButton.setDefault(True)
        self.loadButton.setObjectName(_fromUtf8("loadButton"))
        self.gridLayout.addWidget(self.loadButton, 1, 4, 1, 1)
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
        self.gridLayout.addWidget(self.filenameBox, 1, 1, 1, 1)
        self.browseButton = QtGui.QPushButton(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.browseButton.sizePolicy().hasHeightForWidth())
        self.browseButton.setSizePolicy(sizePolicy)
        self.browseButton.setMaximumSize(QtCore.QSize(1000000, 16777215))
        self.browseButton.setObjectName(_fromUtf8("browseButton"))
        self.gridLayout.addWidget(self.browseButton, 1, 3, 1, 1)
        self.appendBox = QtGui.QCheckBox(self.centralwidget)
        self.appendBox.setObjectName(_fromUtf8("appendBox"))
        self.gridLayout.addWidget(self.appendBox, 1, 2, 1, 1)
        self.scanNumberBox = QtGui.QSpinBox(self.centralwidget)
        self.scanNumberBox.setMaximum(999999)
        self.scanNumberBox.setObjectName(_fromUtf8("scanNumberBox"))
        self.gridLayout.addWidget(self.scanNumberBox, 0, 2, 1, 3)
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
        self.tabWidget.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        MainWindow.setTabOrder(self.scanClassBox, self.scanNumberBox)
        MainWindow.setTabOrder(self.scanNumberBox, self.filenameBox)
        MainWindow.setTabOrder(self.filenameBox, self.browseButton)
        MainWindow.setTabOrder(self.browseButton, self.loadButton)
        MainWindow.setTabOrder(self.loadButton, self.tabWidget)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "NanoMAX Scan Viewer", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("MainWindow", "Scan options", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.roi), _translate("MainWindow", "XRD region of interest", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.com), _translate("MainWindow", "XRD center of mass", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.xrf), _translate("MainWindow", "XRF region of interest", None))
        self.scanClassBox.setToolTip(_translate("MainWindow", "<html><head/><body><p>Available Scan subclasses</p></body></html>", None))
        self.loadButton.setToolTip(_translate("MainWindow", "<html><head/><body><p>Go!</p></body></html>", None))
        self.loadButton.setText(_translate("MainWindow", "Load", None))
        self.filenameBox.setText(_translate("MainWindow", "<input file>", None))
        self.browseButton.setToolTip(_translate("MainWindow", "<html><head/><body><p>Browse for data files</p></body></html>", None))
        self.browseButton.setText(_translate("MainWindow", "Browse...", None))
        self.appendBox.setText(_translate("MainWindow", "Append", None))

from widgets.ComWidget import ComWidget
from widgets.XrdWidget import XrdWidget
from widgets.XrfWidget import XrfWidget
import design_rc
