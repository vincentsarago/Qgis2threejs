# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Qgis2threejs
                                 A QGIS plugin
 export terrain data, map canvas image and vector data to web browser
                             -------------------
        begin                : 2014-01-06
        copyright            : (C) 2014 Minoru Akagi
        email                : akaginch@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os

from PyQt4.QtCore import QDir, QVariant
from PyQt4.QtGui import QWidget, QColor, QColorDialog, QFileDialog
from qgis.core import QGis, QgsProject

from ui.ui_widgetComboEdit import Ui_ComboEditWidget

class WidgetFuncBase:
  FIRST_ATTRIBUTE = 100

  def __init__(self, widget):
    self.widget = widget

  def setup(self):
    # initialize widgets
    self.widget.lineEdit.setPlaceholderText("")
    self.widget.lineEdit.setVisible(True)

  def resetDefault(self):
    pass

  def comboBoxSelectionChanged(self, index):
    pass

  def toolButtonClicked(self):
    pass

  def values(self):
    return {"type": self.widget.funcType,
            "comboData": self.widget.comboBox.itemData(self.widget.comboBox.currentIndex()),
            "comboText": self.widget.comboBox.currentText(),
            "editText": self.widget.lineEdit.text()}

  def setValues(self, vals):
    index = self.widget.comboBox.findData(vals["comboData"])
    if index != -1:
      self.widget.comboBox.setCurrentIndex(index)
    self.widget.lineEdit.setText(vals["editText"])

  @classmethod
  def fields(cls, layer):
    return [[i, field.name()] for i, field in enumerate(layer.pendingFields())]

  @classmethod
  def numericalFields(cls, layer):
    numeric_fields = []
    for i, field in enumerate(layer.pendingFields()):
      if field.type() in [QVariant.Double, QVariant.Int, QVariant.LongLong, QVariant.UInt, QVariant.ULongLong]:
        numeric_fields.append([i, field.name()])
    return numeric_fields

  @classmethod
  def stringFields(cls, layer):
    string_fields = []
    for i, field in enumerate(layer.pendingFields()):
      if field.type() == QVariant.String:
        string_fields.append([i, field.name()])
    return string_fields


class FieldValueWidgetFunc(WidgetFuncBase):
  ABSOLUTE = 1

  def setup(self, options=None):
    """ options: name, label, defaultValue, layer """
    WidgetFuncBase.setup(self)
    options = options or {}
    self.widget.label_1.setText(options.get("name", ""))
    self.widget.toolButton.setVisible(False)

    self.label_absolute = options.get("label", "Value")
    self.label_field = options.get("label_field", "Multiplier")
    self.defaultValue = options.get("defaultValue", 0)

    self.widget.comboBox.clear()
    self.widget.comboBox.addItem("Fixed value", FieldValueWidgetFunc.ABSOLUTE)

    layer = options.get("layer")
    if layer:
      self.widget.addFieldNames(layer)

  def comboBoxSelectionChanged(self, index):
    itemData = self.widget.comboBox.itemData(index)
    if itemData == FieldValueWidgetFunc.ABSOLUTE:
      defaultValue = self.defaultValue
      label = self.label_absolute
    else:
      defaultValue = 1
      label = self.label_field

    self.widget.lineEdit.setText(unicode(defaultValue))
    if label:
      self.widget.label_2.setText(label)
    self.widget.label_2.setVisible(bool(label))
    self.widget.lineEdit.setVisible(bool(label))

class ColorWidgetFunc(WidgetFuncBase):
  FEATURE = 1
  RANDOM = 2
  RGB = 3

  def setup(self, options=None):
    """ options: defaultValue """
    options = options or {}
    self.widget.label_1.setText("Color")
    self.widget.label_2.setText("Value")
    self.widget.lineEdit.setVisible(False)
    self.widget.lineEdit.setPlaceholderText("0xrrggbb")
    self.widget.toolButton.setVisible(False)

    self.widget.comboBox.clear()
    self.widget.comboBox.addItem("Feature style", ColorWidgetFunc.FEATURE)
    self.widget.comboBox.addItem("Random", ColorWidgetFunc.RANDOM)
    self.widget.comboBox.addItem("RGB value", ColorWidgetFunc.RGB)

    self.widget.lineEdit.setText(options.get("defaultValue", ""))

  def comboBoxSelectionChanged(self, index):
    itemData = self.widget.comboBox.itemData(index)
    isRGB = itemData == ColorWidgetFunc.RGB
    self.widget.label_2.setVisible(isRGB)
    self.widget.lineEdit.setVisible(isRGB)
    self.widget.toolButton.setVisible(isRGB)

  def toolButtonClicked(self):
    color = QColorDialog.getColor(QColor(self.widget.lineEdit.text().replace("0x", "#")))
    if color.isValid():
      self.widget.lineEdit.setText(color.name().replace("#", "0x"))

  def setValues(self, vals):
    index = self.widget.comboBox.findData(vals["comboData"])
    if index != -1:
      self.widget.comboBox.setCurrentIndex(index)
      self.widget.comboBoxSelectionChanged(index)  # make sure to update visibility
    self.widget.lineEdit.setText(vals["editText"])

class FilePathWidgetFunc(WidgetFuncBase):
  FILEPATH = 1

  def setup(self, options=None):
    """ options: name, label, defaultValue, filterString """
    WidgetFuncBase.setup(self)
    options = options or {}
    self.widget.label_1.setText(options.get("name", ""))
    self.lineEditLabel = options.get("label", "Path")
    self.widget.label_2.setText(self.lineEditLabel)
    self.widget.lineEdit.setText(unicode(options.get("defaultValue", "")))
    self.widget.toolButton.setVisible(True)

    self.widget.comboBox.clear()
    self.widget.comboBox.addItem("File path", FilePathWidgetFunc.FILEPATH)

    layer = options.get("layer")
    if layer:
      self.widget.addFieldNames(layer, StyleWidget.FIELDTYPE_STRING)

    self.filterString = options.get("filterString", "")

  def comboBoxSelectionChanged(self, index):
    if self.widget.comboBox.itemData(index) == FilePathWidgetFunc.FILEPATH:
      label = self.lineEditLabel
    else:
      label = "Prefix"
    self.widget.label_2.setText(label)

  def toolButtonClicked(self):
    workdir = os.path.split(self.widget.lineEdit.text())[0]
    if not workdir:
      workdir = QgsProject.instance().homePath()
    if not workdir:
      workdir = QDir.homePath()

    comboBox = self.widget.comboBox
    if comboBox.itemData(comboBox.currentIndex()) == FilePathWidgetFunc.FILEPATH:
      filepath = QFileDialog.getOpenFileName(None, "Select a file", workdir, self.filterString)
      if filepath:
        self.widget.lineEdit.setText(filepath)
    else:
      directory = QFileDialog.getExistingDirectory(None, "Select a directory", workdir)
      if directory:
        if directory[-1] not in ["/", "\\"]:
          directory += os.sep
        self.widget.lineEdit.setText(directory)

class HeightWidgetFunc(WidgetFuncBase):
  ABSOLUTE = 1
  RELATIVE = 2
  Z_VALUE = 3
  FIRST_ATTR_ABS = WidgetFuncBase.FIRST_ATTRIBUTE
  FIRST_ATTR_REL = FIRST_ATTR_ABS + 100

  def setup(self, options=None):
    """ options: defaultValue, layer """
    WidgetFuncBase.setup(self)
    options = options or {}
    self.widget.label_1.setText("Mode")
    self.widget.toolButton.setVisible(False)
    self.defaultValue = options.get("defaultValue", 0)
    layer = options.get("layer")

    comboBox = self.widget.comboBox
    comboBox.clear()

    # z value if layer has
    if layer and layer.wkbType() in [QGis.WKBPoint25D, QGis.WKBLineString25D, QGis.WKBMultiPoint25D, QGis.WKBMultiLineString25D]:
      comboBox.addItem("Z value", HeightWidgetFunc.Z_VALUE)
      comboBox.insertSeparator(1)

    # relative to DEM
    comboBox.addItem("Relative to DEM", HeightWidgetFunc.RELATIVE)
    if layer:
      index_fieldName = self.numericalFields(layer)
      for index, fieldName in index_fieldName:
        comboBox.addItem(u'+"{0}"'.format(fieldName), HeightWidgetFunc.FIRST_ATTR_REL + index)
            # note: VectorPropertyReader.relativeHeight() uses item name to get field name

      if index_fieldName:
        comboBox.insertSeparator(comboBox.count())

    # absolute
    comboBox.addItem("Absolute value", HeightWidgetFunc.ABSOLUTE)
    if layer:
      for index, fieldName in index_fieldName:
        comboBox.addItem(u' "{0}"'.format(fieldName), HeightWidgetFunc.FIRST_ATTR_ABS + index)
            # note: VectorPropertyReader.relativeHeight() uses item name to get field name

  def comboBoxSelectionChanged(self, index):
    itemData = self.widget.comboBox.itemData(index)
    if itemData in [HeightWidgetFunc.ABSOLUTE, HeightWidgetFunc.RELATIVE]:
      label = "Height"
      defaultValue = self.defaultValue
    else:
      label = "Addend"
      defaultValue = 0
    self.widget.label_2.setText(label)
    self.widget.lineEdit.setText(unicode(defaultValue))

class LabelHeightWidgetFunc(WidgetFuncBase):
  ABSOLUTE = 1
  RELATIVE = 2
  RELATIVE_TO_TOP = 3

  def setup(self, options=None):
    """ options: defaultValue, layer """
    WidgetFuncBase.setup(self)
    options = options or {}
    self.widget.label_1.setText("Label height")
    self.widget.toolButton.setVisible(False)
    self.defaultValue = options.get("defaultValue", 0)

    layer = options.get("layer")

    self.widget.comboBox.clear()
    if layer and layer.geometryType() != QGis.Point:
      return  # Will be initialized in obj_mod.setupWidgets() if polygon. Line layer cannot have labels.
    self.widget.comboBox.addItem("Height from point", LabelHeightWidgetFunc.RELATIVE)
    self.widget.comboBox.addItem("Fixed value", LabelHeightWidgetFunc.ABSOLUTE)

    if layer:
      self.widget.addFieldNames(layer)

  def comboBoxSelectionChanged(self, index):
    if self.widget.comboBox.itemData(index) < LabelHeightWidgetFunc.FIRST_ATTRIBUTE:
      label = "Value"
      defaultValue = self.defaultValue
    else:
      label = "Addend"
      defaultValue = 0
    self.widget.label_2.setText(label)
    self.widget.lineEdit.setText(unicode(defaultValue))

class TransparencyWidgetFunc(WidgetFuncBase):
  FEATURE = 1
  VALUE = 2

  def setup(self, options=None):
    self.widget.label_1.setText("Transparency")
    self.widget.label_2.setText("Value (%)")
    self.widget.lineEdit.setVisible(False)
    self.widget.lineEdit.setPlaceholderText("0 - 100")
    self.widget.toolButton.setVisible(False)

    self.widget.comboBox.clear()
    self.widget.comboBox.addItem("Feature style", TransparencyWidgetFunc.FEATURE)
    self.widget.comboBox.addItem("Fixed value", TransparencyWidgetFunc.VALUE)

  def comboBoxSelectionChanged(self, index):
    itemData = self.widget.comboBox.itemData(index)
    isValue = itemData == TransparencyWidgetFunc.VALUE
    self.widget.label_2.setVisible(isValue)
    self.widget.lineEdit.setVisible(isValue)

  def setValues(self, vals):
    index = self.widget.comboBox.findData(vals["comboData"])
    if index != -1:
      self.widget.comboBox.setCurrentIndex(index)
      self.widget.comboBoxSelectionChanged(index)  # make sure to update visibility
    self.widget.lineEdit.setText(vals["editText"])

class BorderColorWidgetFunc(ColorWidgetFunc):
  NO_BORDER = 0

  def setup(self, options=None):
    ColorWidgetFunc.setup(self, options)
    self.widget.label_1.setText("Border color")

    self.widget.comboBox.insertItem(0, "(No border)", BorderColorWidgetFunc.NO_BORDER)


class StyleWidget(QWidget, Ui_ComboEditWidget):
  # function types
  FIELD_VALUE = 1
  COLOR = 2
  FILEPATH = 3
  HEIGHT = 4
  TRANSPARENCY = 5
  LABEL_HEIGHT = 6
  BORDER_COLOR = 7

  type2funcClass = {FIELD_VALUE: FieldValueWidgetFunc,
                    COLOR: ColorWidgetFunc,
                    FILEPATH: FilePathWidgetFunc,
                    HEIGHT: HeightWidgetFunc,
                    LABEL_HEIGHT: LabelHeightWidgetFunc,
                    TRANSPARENCY: TransparencyWidgetFunc,
                    BORDER_COLOR: BorderColorWidgetFunc}

  FIELDTYPE_ALL = 0
  FIELDTYPE_NUMBER = 1
  FIELDTYPE_STRING = 2

  def __init__(self, funcType=None, parent=None):
    QWidget.__init__(self, parent)
    self.setupUi(self)
    self.comboBox.currentIndexChanged.connect(self.comboBoxSelectionChanged)
    self.toolButton.clicked.connect(self.toolButtonClicked)
    self.funcType = funcType
    self.func = None
    self.hasValues = False

  def setup(self, funcType=None, options=None):
    if funcType is None:
      # use the function type passed to __init__
      funcType = self.funcType

    if self.func:
      self.func.resetDefault()

    if self.func is None or self.funcType != funcType:
      funcClass = self.type2funcClass.get(funcType)
      if funcClass is None:
        self.funcType = None
        self.func = None
        self.setVisible(False)
        self.hasValues = False
        return
      self.func = funcClass(self)

    self.funcType = funcType
    self.func.setup(options)
    self.setVisible(True)
    self.hasValues = True

  def comboBoxSelectionChanged(self, index):
    if self.func:
      self.func.comboBoxSelectionChanged(index)

  def toolButtonClicked(self):
    if self.func:
      self.func.toolButtonClicked()

  def hide(self):
    self.hasValues = False
    QWidget.hide(self)

  def values(self):
    if self.func and self.hasValues:
      return self.func.values()
    else:
      return {}

  def setValues(self, vals):
    if self.func:
      self.func.setValues(vals)

  def addFieldNames(self, layer, fieldType=FIELDTYPE_NUMBER):
    if fieldType == StyleWidget.FIELDTYPE_NUMBER:
      index_fieldName = WidgetFuncBase.numericalFields(layer)
    elif fieldType == StyleWidget.FIELDTYPE_STRING:
      index_fieldName = WidgetFuncBase.stringFields(layer)
    else:
      index_fieldName = WidgetFuncBase.fields(layer)

    for index, fieldName in index_fieldName:
      self.comboBox.addItem(u'"{0}"'.format(fieldName), WidgetFuncBase.FIRST_ATTRIBUTE + index)
          # note: VectorPropertyReader.values() uses item name to get field name
