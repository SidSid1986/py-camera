import os
import ctypes
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.QtGui import QIcon  # 正确导入QIcon
import xml.etree.ElementTree as ET

class SettingsWindow(QtWidgets.QDialog):
    signalStopResetStart = QtCore.pyqtSignal()  # 槽信号

    def __init__(self, parent=None):
        super().__init__(parent)


        UI_PATH = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "ui", "settingswindow.ui"
        )
        uic.loadUi(UI_PATH, self)

        self.setWindowIcon(QIcon("wenglor.ico"))
        self.hScanner = None
        self.orderNumber = ""
        self.ip = ""

        # 检查控件是否存在，避免属性None导致崩溃
        required_controls = [
            "setTriggerSource", "setAcquisitionLineTime", "setExposureTime",
            "setSyncOut", "setSyncOutDelay", "comboBoxSignalEnable",
            "setSignalSelection", "setSignalWidthMin", "setSignalWidthMax",
            "setSignalStrengthMin", "setHeightZ", "setOffsetZ", "setWidthX",
            "setOffsetX", "setStepX", "sendRawCommand",
            "pushButtonTriggerSource", "pushButtonExposureTime",
            "pushButtonAcquisitionLineTime", "pushButtonSync",
            "pushButtonSyncDelay", "pushButtonHeightZ", "pushButtonOffsetZ",
            "pushButtonWidthX", "pushButtonOffsetX", "pushButtonStepX",
            "pushButtonSignalEnable", "pushButtonSignalSelection",
            "pushButtonSignalWidthMin", "pushButtonSignalWidthMax",
            "pushButtonSignalStrengthMin", "pushButtonResetEncoder",
            "pushButtonResetPicCnt", "pushButtonresetBaseTime",
            "pushButtonResetSettings", "pushButtonSetAcquisitionStart",
            "pushButtonSetAcquisitionStop", "pushButtonSendASCIICommand",
            "pushButtonStopResetStart", "pushButtonUpdate", "pushButtonSaveXML"
        ]
        for ctrl in required_controls:
            assert hasattr(self, ctrl), f"UI控件 {ctrl} 缺失或拼写错误"

        # 设置默认值
        self.setTriggerSource.setText("0")
        self.setAcquisitionLineTime.setText("5000")
        self.setExposureTime.setText("100")
        self.setSyncOut.setText("0")
        self.setSyncOutDelay.setText("0")

        self.comboBoxSignalEnable.clear()
        self.comboBoxSignalEnable.addItem("Profile 1", 1)
        self.comboBoxSignalEnable.addItem("Profile 2", 2)
        self.comboBoxSignalEnable.addItem("Profile 1 + Profile 2", 3)

        self.setSignalSelection.setText("1")
        self.setSignalWidthMin.setText("0")
        self.setSignalWidthMax.setText("63")
        self.setSignalStrengthMin.setText("0")

        self.setHeightZ.setText("2048")
        self.setOffsetZ.setText("0")
        self.setWidthX.setText("2048")
        self.setOffsetX.setText("0")
        self.setStepX.setText("0")

        self.sendRawCommand.setText("SetExposureTime=50")

        # 绑定事件
        self.pushButtonTriggerSource.clicked.connect(self.set_trigger_source)
        self.pushButtonExposureTime.clicked.connect(self.set_exposure_time)
        self.pushButtonAcquisitionLineTime.clicked.connect(self.set_acquisition_line_time)
        self.pushButtonSync.clicked.connect(self.set_sync_out)
        self.pushButtonSyncDelay.clicked.connect(self.set_sync_out_delay)
        self.pushButtonHeightZ.clicked.connect(self.set_height_z)
        self.pushButtonOffsetZ.clicked.connect(self.set_offset_z)
        self.pushButtonWidthX.clicked.connect(self.set_width_x)
        self.pushButtonOffsetX.clicked.connect(self.set_offset_x)
        self.pushButtonStepX.clicked.connect(self.set_step_x)
        self.pushButtonSignalEnable.clicked.connect(self.set_signal_enable)
        self.pushButtonSignalSelection.clicked.connect(self.set_signal_selection)
        self.pushButtonSignalWidthMin.clicked.connect(self.set_signal_width_min)
        self.pushButtonSignalWidthMax.clicked.connect(self.set_signal_width_max)
        self.pushButtonSignalStrengthMin.clicked.connect(self.set_signal_strength_min)
        self.pushButtonResetEncoder.clicked.connect(self.reset_encoder)
        self.pushButtonResetPicCnt.clicked.connect(self.reset_pic_cnt)
        self.pushButtonresetBaseTime.clicked.connect(self.reset_base_time)
        self.pushButtonResetSettings.clicked.connect(self.reset_settings)
        self.pushButtonSetAcquisitionStart.clicked.connect(self.set_acquisition_start)
        self.pushButtonSetAcquisitionStop.clicked.connect(self.set_acquisition_stop)
        self.pushButtonSendASCIICommand.clicked.connect(self.send_ascii_command)
        self.pushButtonStopResetStart.clicked.connect(self.signalStopResetStart.emit)
        self.pushButtonUpdate.clicked.connect(self.refresh_current_values)
        self.pushButtonSaveXML.clicked.connect(self.save_xml)

    def showEvent(self, event):
        super().showEvent(event)
        if self.hScanner:
            self.on_push_button_update_clicked()

    def exchange_data(self, hScanner, orderNumber, ip):
        self.hScanner = hScanner
        self.orderNumber = orderNumber
        self.ip = ip

    # 下面每个set_*方法都调用dll发送命令
    def set_trigger_source(self):
        cmd = f"SetTriggerSource={self.setTriggerSource.toPlainText()}\r"
        self._write_command(cmd)

    def set_exposure_time(self):
        cmd = f"SetExposureTime={self.setExposureTime.toPlainText()}\r"
        self._write_command(cmd)

    def set_acquisition_line_time(self):
        cmd = f"SetAcquisitionLineTime={self.setAcquisitionLineTime.toPlainText()}\r"
        self._write_command(cmd)

    def set_sync_out(self):
        cmd = f"SetSyncOut={self.setSyncOut.toPlainText()}\r"
        self._write_command(cmd)

    def set_sync_out_delay(self):
        cmd = f"SetSyncOutDelay={self.setSyncOutDelay.toPlainText()}\r"
        self._write_command(cmd)

    def set_height_z(self):
        cmd = f"SetROI1HeightZ={self.setHeightZ.toPlainText()}\r"
        self._write_command(cmd)

    def set_offset_z(self):
        cmd = f"SetROI1OffsetZ={self.setOffsetZ.toPlainText()}\r"
        self._write_command(cmd)

    def set_width_x(self):
        cmd = f"SetROI1WidthX={self.setWidthX.toPlainText()}\r"
        self._write_command(cmd)

    def set_offset_x(self):
        cmd = f"SetROI1OffsetX={self.setOffsetX.toPlainText()}\r"
        self._write_command(cmd)

    def set_step_x(self):
        cmd = f"SetROI1StepX={self.setStepX.toPlainText()}\r"
        self._write_command(cmd)

    def set_signal_enable(self):
        value = self.comboBoxSignalEnable.currentData()
        cmd = f"SetSignalEnable={value}\r"
        self._write_command(cmd)

    def set_signal_selection(self):
        cmd = f"SetSignalSelection={self.setSignalSelection.toPlainText()}\r"
        self._write_command(cmd)

    def set_signal_width_min(self):
        cmd = f"SetSignalWidthMin={self.setSignalWidthMin.toPlainText()}\r"
        self._write_command(cmd)

    def set_signal_width_max(self):
        cmd = f"SetSignalWidthMax={self.setSignalWidthMax.toPlainText()}\r"
        self._write_command(cmd)

    def set_signal_strength_min(self):
        cmd = f"SetSignalStrengthMin={self.setSignalStrengthMin.toPlainText()}\r"
        self._write_command(cmd)

    def send_ascii_command(self):
        cmd = self.sendRawCommand.toPlainText().replace('\n', '\r')
        self._write_command(cmd)

    def reset_encoder(self):
        self._write_command("SetResetEncoder\r")

    def reset_pic_cnt(self):
        self._write_command("SetResetPictureCounter\r")

    def reset_base_time(self):
        self._write_command("SetResetBaseTimeCounter\r")

    def reset_settings(self):
        if QtWidgets.QMessageBox.question(self, "确认重置", "确定要恢复默认设置吗？所有自定义配置将被清除。",
                                          QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
            self._write_command("SetResetSettings\r")

    def set_acquisition_start(self):
        self._write_command("SetAcquisitionStart\r")

    def set_acquisition_stop(self):
        self._write_command("SetAcquisitionStop\r")

    def _write_command(self, cmd):
        from .ethernet_scanner_ctypes import dll
        if self.hScanner:
            try:
                dll.EthernetScanner_WriteData(self.hScanner, cmd.encode(), len(cmd))
                QtCore.QTimer.singleShot(200, self.refresh_current_values)
            except Exception as e:
                print(f"DLL写命令异常: {e}")

    def refresh_current_values(self):
        from .ethernet_scanner_ctypes import dll
        if not self.hScanner:
            return
        buf = ctypes.create_string_buffer(65536)
        try:
            res = dll.EthernetScanner_GetInfo(self.hScanner, buf, 65536, b"xml")
        except Exception as e:
            print(f"调用DLL异常: {e}")
            return
        if res > 0:
            try:
                root = ET.fromstring(buf.value.decode(errors="ignore"))
                settings = root.find(".//settings")
                self.getTriggersource.setText(settings.findtext("triggersource/current", ""))
                self.getExposureTime.setText(settings.findtext("exposuretime/current", ""))
                self.getAcquisitionLineTime.setText(settings.findtext("acquisitionlinetime/current", ""))
                roi_x = settings.find(".//roi/x1")
                if roi_x is not None:
                    self.getWidthX.setText(roi_x.findtext("width/current", ""))
                    self.getOffsetX.setText(roi_x.findtext("offset/current", ""))
                    self.getStepX.setText(roi_x.findtext("step/current", ""))
                roi_z = settings.find(".//roi/z1")
                if roi_z is not None:
                    self.getHeightZ.setText(roi_z.findtext("height/current", ""))
                    self.getOffsetZ.setText(roi_z.findtext("offset/current", ""))
                self.getSyncOut.setText(settings.findtext("syncout/current", ""))
                self.getSyncOutDelay.setText(settings.findtext("syncoutdelay/current", ""))
                proto = settings.find(".//protocol/profile/signal/enable/current")
                signal_enable = proto.text if proto is not None else ""
                self.getSignalEnable.setText(self.signal_enable_to_text(signal_enable))
                idx = self.comboBoxSignalEnable.findData(int(signal_enable)) if signal_enable.isdigit() else -1
                if idx >= 0:
                    self.comboBoxSignalEnable.setCurrentIndex(idx)
                self.getSignalSelection.setText(settings.findtext("signalselection/current", ""))
                self.getSignalWidthMin.setText(settings.findtext("signalwidthmin/current", ""))
                self.getSignalWidthMax.setText(settings.findtext("signalwidthmax/current", ""))
                self.getSignalStrengthMin.setText(settings.findtext("signalstrengthmin/current", ""))
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Warning", f"Error parsing XML: {e}")
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "No Valid XML-Packet!!!")

    def on_push_button_update_clicked(self):
        self.refresh_current_values()

    def save_xml(self):
        from .ethernet_scanner_ctypes import dll
        if not self.hScanner:
            return
        file_name = f"{self.orderNumber}_{self.ip}.xml"
        buf = ctypes.create_string_buffer(65536)
        res = dll.EthernetScanner_GetInfo(self.hScanner, buf, 65536, b"xml")
        if res > 0:
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(buf.value.decode(errors="ignore"))
            QtWidgets.QMessageBox.information(self, "成功", f"XML已保存到: {file_name}")
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "No Valid XML-Packet!!!")

    def signal_enable_to_text(self, value):
        if value == "1":
            return "Profile 1"
        if value == "2":
            return "Profile 2"
        if value == "3":
            return "Profile 1 + Profile 2"
        return value