# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'c:\dev\pynta\pynta\view\GUI\designer\line_plot.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(400, 300)
        self.formLayout = QtWidgets.QFormLayout(Form)
        self.formLayout.setObjectName("formLayout")
        self.plot = PlotWidget(Form)
        self.plot.setObjectName("plot")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.plot)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
from pyqtgraph import PlotWidget
