import sys
import os
import threading
import time
from PyQt5 import QtWidgets, uic, QtGui, QtCore
import ctypes
import xml.etree.ElementTree as ET
import openpyxl
import ethernet_scanner_ctypes as esc
from settings_window import SettingsWindow
from cimage import CImage

# 用宏定义替代魔数，保持和C++头文件同步
ETHERNETSCANNER_SCANXMAX = esc.ETHERNETSCANNER_SCANXMAX
ETHERNETSCANNER_PEAKSPERCMOSSCANLINEMAX = esc.ETHERNETSCANNER_PEAKSPERCMOSSCANLINEMAX
BUFFLEN = esc.BUFFLEN

CONNECTED = 3  # 连接成功状态码


class MainWindow(QtWidgets.QMainWindow):
    updatePixmap = QtCore.pyqtSignal(QtGui.QPixmap)

    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(os.path.dirname(__file__), "mainwindow.ui"), self)
        self.dll = esc.dll

        # 设备句柄与线程控制
        self.hScanner = None
        self.imgThread = None
        self.imgThreadExit = threading.Event()
        self.bScannerConnectStatus = False

        # 数据缓存（修正为8192，与C++一致）
        self.dScannerBufferX = (ctypes.c_double * BUFFLEN)()
        self.dScannerBufferZ = (ctypes.c_double * BUFFLEN)()
        self.iScannerBufferI = (ctypes.c_int * BUFFLEN)()
        self.iScannerBufferPeakWidth = (ctypes.c_int * BUFFLEN)()
        self.uScannerEncoder = ctypes.c_uint(0)
        self.ucScannerDigitalInputs = ctypes.c_ubyte(0)
        self.usPicCnt = ctypes.c_int(0)
        self.iLengthReceivedData = 0

        # 设备信息
        self.strOrderNumber = "...."
        self.strProductVersion = "...."
        self.strProducer = "...."
        self.strDescriptor = "...."
        self.strHardwareVersion = "...."
        self.strFWVersion = "...."
        self.strMAC = "...."
        self.strSerialNummber = "...."
        self.strZstart = "...."
        self.strZrange = "...."
        self.strXRangeAtStart = "...."
        self.strXRangeAtEnd = "...."
        self.strWidthX = "...."
        self.strHeightZ = "...."

        # 状态
        self.iPicCntErr = 0
        self.iCnt = 0
        self.dwScanner_Frequency = 0
        self.freq_lock = threading.Lock()
        self.cpu_fifo_value = "..."
        self.dll_fifo_value = "..."
        self.htl_encoder = "..."
        self.ttl_encoder = "..."

        self.last_pic_cnt = None  # 初始化last_pic_cnt

        self.cimage = None  # 图像对象，延迟初始化

        # self.pSettings = SettingsWindow(self)  # 实例化设置弹窗 自动直接弹窗

        self.init_ui()
        self.get_versions()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(1000)

    def init_ui(self):
        self.pushButtonConnect.clicked.connect(self.scanner_connect)
        self.pushButtonDisconnect.clicked.connect(self.scanner_disconnect)
        self.pushButtonSettings.clicked.connect(self.show_settings_window)
        self.pushButtonResetPicCnt.clicked.connect(self.reset_picture_counter)
        self.pushButtonDLLFifoReset.clicked.connect(self.reset_dll_fifo)
        self.pushButtonSaveProfiles.clicked.connect(self.save_profiles)
        self.pushButtonGetPropertyValue.clicked.connect(self.get_property_value)
        self.pushButtonSetMeasuringRate.clicked.connect(self.set_measuring_rate)
        self.pushButtonSaveExcel.clicked.connect(self.save_profiles_as_excel)
        self.pushButtonScreenshot.clicked.connect(self.on_screenshot)
        self.pushButtonReboot.clicked.connect(self.reboot_camera)
        self.pushButtonSetMode.clicked.connect(self.set_mode)
        self.updatePixmap.connect(self.refresh_pixmap)

        self.comboBoxPropertyName.clear()
        self.comboBoxPropertyName.addItem("温度", "GetTemperature")
        self.comboBoxPropertyName.addItem("模式", "GetCameraMode")
        self.comboBoxPropertyName.addItem("触发源", "GetTriggerSource")
        self.comboBoxPropertyName.addItem("采集线时间", "GetAcquisitionLineTime")
        self.comboBoxPropertyName.addItem("曝光时间", "GetExposureTime")
        self.comboBoxPropertyName.addItem("扫描仪状态", "GetScannerState")
        self.comboBoxPropertyName.addItem("固件版本", "GetFirmwareVersion")
        self.comboBoxPropertyName.addItem("序列码", "GetSerialNumber")
        self.comboBoxPropertyName.addItem("MAC地址", "GetMAC")
        self.comboBoxPropertyName.addItem("Z起始值", "GetWorkingRangeZStart")
        self.comboBoxPropertyName.addItem("Z结束值", "GetWorkingRangeZEnd")
        self.comboBoxPropertyName.addItem("X起始值", "GetFieldWidthXStart")
        self.comboBoxPropertyName.addItem("X结束值", "GetFieldWidthXEnd")
        self.comboBoxPropertyName.addItem("摄像头运行", "GetCameraRunning")
        self.comboBoxPropertyName.addItem("IO状态", "GetIOState")
        self.comboBoxPropertyName.setCurrentIndex(0)
        self.comboBoxMode.clear()
        self.comboBoxMode.addItem("Profile 轮廓", 0)
        self.comboBoxMode.addItem("Camera images 图像", 1)
        self.comboBoxMode.setCurrentIndex(0)

        self.checkBoxActivateDisplay.setChecked(True)
        self.lineEditVersion.setText("TODO: DLL版本")
        self.lineEditGuiVersion.setText("1.8.4")

    def get_versions(self):
        buf = ctypes.create_string_buffer(1024)
        try:
            self.dll.EthernetScanner_GetVersion(buf, 1024)
            dll_version = buf.value.decode(errors="ignore")
            self.lineEditVersion.setText(dll_version)
        except Exception as e:
            self.lineEditVersion.setText("未知")
        self.lineEditGuiVersion.setText("1.8.4")

    def scanner_connect(self):
        if self.hScanner:
            QtWidgets.QMessageBox.warning(self, "已连接", "设备已连接")
            return
        ip = self.lineEditIp.text().strip()
        timeout = int(self.lineEditTimeOut.text().strip())
        port = "32001"
        h = self.dll.EthernetScanner_Connect(ip.encode(), port.encode(), timeout)
        if h:
            status = ctypes.c_int(0)
            t_start = time.time()
            while status.value != CONNECTED:
                self.dll.EthernetScanner_GetConnectStatus(h, ctypes.byref(status))
                if time.time() - t_start > 2:
                    self.dll.EthernetScanner_Disconnect(h)
                    self.hScanner = None
                    QtWidgets.QMessageBox.critical(
                        self, "连接超时", "设备未响应或未上线"
                    )
                    return
                time.sleep(0.05)
            self.hScanner = h
            self.bScannerConnectStatus = True
            self.lineEditStatus.setText("连接")
            self.lineEditStatus.setStyleSheet("QLineEdit {background: green;}")
            self.get_device_info()
            # 关键：启动采集
            self.dll.EthernetScanner_WriteData(self.hScanner, b"SetAcquisitionStart\r", len(b"SetAcquisitionStart\r"))
            self.imgThreadExit.clear()
            self.imgThread = threading.Thread(target=self.get_image_thread, daemon=True)
            self.imgThread.start()
            self.sync_camera_mode_from_device()
            QtWidgets.QMessageBox.information(self, "连接成功", "设备已连接并同步信息")
        else:
            QtWidgets.QMessageBox.critical(self, "连接失败", "DLL接口返回空句柄")

    def scanner_disconnect(self):
        self.imgThreadExit.set()
        if self.imgThread:
            self.imgThread.join()
        if self.hScanner:
            self.dll.EthernetScanner_Disconnect(self.hScanner)
            self.hScanner = None
        self.bScannerConnectStatus = False
        self.lineEditStatus.setText("已断开")
        self.lineEditStatus.setStyleSheet("QLineEdit {background: red;}")
        self.lineEditMeasureRate.setText("...")
        self.lineEditMeasureRate.setStyleSheet("QLineEdit {background: rgb(240, 240, 240);  }")
        self.labelImage.clear()
        self.labelImage.setText("Scanner Image")
        self.labelImage.setAlignment(QtCore.Qt.AlignCenter)

    def get_device_info(self):
        buf = ctypes.create_string_buffer(128 * 1024)
        res = self.dll.EthernetScanner_GetInfo(self.hScanner, buf, 128 * 1024, b"xml")
        if res > 0:
            self.parse_and_fill_info(buf.value.decode(errors="ignore"))
        else:
            QtWidgets.QMessageBox.warning(self, "警告", "未能获取设备信息")

    def parse_and_fill_info(self, xml_str):
        try:
            root = ET.fromstring(xml_str)
            general = root.find(".//general")
            if general is not None:
                self.strOrderNumber = general.findtext("ordernumber", "....")
                self.strProductVersion = general.findtext("productversion", "....")
                hw = general.find("hardwareversion")
                fw = general.find("firmwareversion")
                self.strHardwareVersion = hw.findtext("general", "....") if hw is not None else "...."
                self.strFWVersion = fw.findtext("general", "....") if fw is not None else "...."
                self.strProducer = general.findtext("producer", "....")
                self.strDescriptor = general.findtext("description", "....")
                self.strSerialNummber = general.findtext("serialnumber", "....")
                self.strMAC = general.findtext("mac", "....")
                self.strZstart = general.findtext("workingrange_z_start", "....")
                self.strZrange = general.findtext("measuringrange_z", "....")
                self.strXRangeAtStart = general.findtext("fieldwidth_x_start", "....")
                self.strXRangeAtEnd = general.findtext("fieldwidth_x_end", "....")
                self.strWidthX = general.findtext("pixel_x_max", "....")
                self.strHeightZ = general.findtext("pixel_z_max", "....")
                self.lineEditSerial1.setText(
                    f"{self.strOrderNumber} {self.strSerialNummber} {self.strDescriptor} {self.strProducer}"
                )
                self.lineEditSerial2.setText(
                    f"Product version: {self.strProductVersion}  HW: {self.strHardwareVersion}  FW: {self.strFWVersion}"
                )
                self.lineEditSerial3.setText(
                    f"Working range Z start: {self.strZstart}  Working range: {self.strZrange}  Field width X start: {self.strXRangeAtStart}  Field width X end: {self.strXRangeAtEnd}"
                )
        except Exception as e:
            print("解析设备信息出错:", e)

    def sync_camera_mode_from_device(self):
        if not self.hScanner:
            return
        buf = ctypes.create_string_buffer(128)
        res = self.dll.EthernetScanner_ReadData(
            self.hScanner, b"GetCameraMode", buf, 128, 1000
        )
        if res == 0:
            try:
                mode = int(buf.value.decode(errors="ignore").strip())
                idx = self.comboBoxMode.findData(mode)
                if idx >= 0:
                    self.comboBoxMode.setCurrentIndex(idx)
            except Exception:
                pass

    def get_image_thread(self):
        last_draw = time.time()
        while not self.imgThreadExit.is_set() and self.hScanner:
            try:
                dataLength = self.dll.EthernetScanner_GetXZIExtended(
                    self.hScanner,
                    self.dScannerBufferX,
                    self.dScannerBufferZ,
                    self.iScannerBufferI,
                    self.iScannerBufferPeakWidth,
                    BUFFLEN,
                    ctypes.byref(self.uScannerEncoder),
                    ctypes.byref(self.ucScannerDigitalInputs),
                    1000,
                    None,
                    0,
                    ctypes.byref(self.usPicCnt),
                )
                if dataLength > 0:
                    self.iLengthReceivedData = dataLength
                    with self.freq_lock:
                        self.dwScanner_Frequency += 1
                        # PicCntErr累加
                        cur_pic_cnt = self.usPicCnt.value
                        if self.last_pic_cnt is not None:
                            if (cur_pic_cnt - self.last_pic_cnt != 1) and (self.last_pic_cnt != 0) and (
                                    self.last_pic_cnt != 0xFFFF):
                                self.iPicCntErr += 1
                        self.last_pic_cnt = cur_pic_cnt

                    # 100ms刷新一次画面
                    if time.time() - last_draw > 0.1:
                        self.draw_profile()
                        last_draw = time.time()

                    # 实时读取状态
                    result = self.read_property("CPUFiFo")
                    if result is not None:
                        self.cpu_fifo_value = result
                    self.dll_fifo_value = str(self.dll.EthernetScanner_GetDllFiFoState(self.hScanner))
                    self.htl_encoder = self.read_property("EncoderHTL")
                    self.ttl_encoder = self.read_property("EncoderTTL")
                else:
                    print("[DEBUG] 未采集到有效数据，dataLength=", dataLength)
            except Exception as e:
                print("采集线程异常:", e)

    def draw_profile(self):
        w, h = self.labelImage.width(), self.labelImage.height()
        if w <= 0 or h <= 0:
            w, h = 640, 480

        # 只初始化一次CImage，尺寸变化时重新创建
        if self.cimage is None or self.cimage.width() != w or self.cimage.height() != h:
            self.cimage = CImage(w, h)

        # 设置参数（确保参数为float或str，CImage内部会转float）
        self.cimage.setImageParameters(
            self.strZstart,
            self.strZrange,
            self.strXRangeAtStart,
            self.strXRangeAtEnd,
            self.strWidthX,
            self.strHeightZ
        )

        if self.iLengthReceivedData > 1:
            x_vals = self.dScannerBufferX[:self.iLengthReceivedData]
            z_vals = self.dScannerBufferZ[:self.iLengthReceivedData]
            i_vals = self.iScannerBufferI[:self.iLengthReceivedData]
            self.cimage.drawImage(x_vals, z_vals, i_vals, self.iLengthReceivedData)

        self.updatePixmap.emit(self.cimage)

    def refresh_pixmap(self, pixmap):
        self.labelImage.setPixmap(pixmap)
        self.labelImage.show()

    def reset_picture_counter(self):
        self.iPicCntErr = 0
        self.iCnt = 0

    def reset_dll_fifo(self):
        if self.hScanner:
            self.dll.EthernetScanner_ResetDllFiFo(self.hScanner)

    def save_profiles(self):
        if not self.hScanner:
            QtWidgets.QMessageBox.warning(self, "disconnected", "请先连接设备")
            return
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "保存为TXT", "", "文本文件 (*.txt)"
        )
        if not fname:
            return
        if not fname.endswith(".txt"):
            fname += ".txt"
        width = 12  # 每列宽度
        with open(fname, "w", encoding="utf-8") as f:
            # 表头
            f.write(f"{'X':>{width}}{'Y':>{width}}{'Z':>{width}}{'I':>{width}}\n")
            for i in range(self.iLengthReceivedData):
                f.write(
                    f"{self.dScannerBufferX[i]:{width}.4f}"
                    f"{self.uScannerEncoder.value:{width}d}"
                    f"{self.dScannerBufferZ[i]:{width}.4f}"
                    f"{self.iScannerBufferI[i]:{width}d}\n"
                )
        QtWidgets.QMessageBox.information(self, "保存成功", "数据已保存")

    def save_profiles_as_excel(self):
        if not self.hScanner:
            QtWidgets.QMessageBox.warning(self, "disconnected", "请先连接设备")
            return
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["X", "Y", "Z", "I"])
        for i in range(self.iLengthReceivedData):
            ws.append(
                [
                    self.dScannerBufferX[i],
                    self.uScannerEncoder.value,
                    self.dScannerBufferZ[i],
                    self.iScannerBufferI[i],
                ]
            )
        fname, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "保存为Excel", "", "Excel 文件 (*.xlsx)"
        )
        if fname:
            if not fname.endswith(".xlsx"):
                fname += ".xlsx"
            wb.save(fname)
            QtWidgets.QMessageBox.information(self, "success", "Excel Success")

    def on_screenshot(self):
        try:
            if not hasattr(self, "labelImage") or self.labelImage is None:
                QtWidgets.QMessageBox.warning(self, "failed", "没有图片控件")
                return

            pixmap = self.labelImage.pixmap()
            if not pixmap or pixmap.isNull():
                QtWidgets.QMessageBox.warning(self, "failed", "没有图片内容")
                return

            safe_pixmap = QtGui.QPixmap(pixmap)

            default_path = os.path.join(os.getcwd(), "screenshot.png")
            fname, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "保存截图",
                default_path,
                "PNG 图片 (*.png);;所有文件 (*)"
            )
            if not fname:
                return
            if not fname.lower().endswith(".png"):
                fname += ".png"

            ok = safe_pixmap.save(fname, "PNG")
            if ok:
                QtWidgets.QMessageBox.information(self, "成功", f"截图已保存到:\n{fname}")
            else:
                QtWidgets.QMessageBox.critical(self, "保存失败", "图片保存失败，请检查路径权限")

        except Exception as e:
            import traceback
            QtWidgets.QMessageBox.critical(
                self, "异常", f"截图保存时发生异常：\n{e}\n{traceback.format_exc()}"
            )

    def get_property_value(self):
        if not self.hScanner:
            QtWidgets.QMessageBox.warning(self, "disconnected", "请先连接设备")
            return
        cmd = self.comboBoxPropertyName.currentData()
        timeout = (
            int(self.lineEditCashTime.text())
            if hasattr(self, "lineEditCashTime")
            else 1000
        )
        chRetBuf = ctypes.create_string_buffer(1024)
        res = self.dll.EthernetScanner_ReadData(
            self.hScanner, cmd.encode(), chRetBuf, 1024, timeout
        )
        if res == 0:
            self.lineEditPropertyValue.setText(chRetBuf.value.decode(errors="ignore"))
        else:
            self.lineEditPropertyValue.setText(str(res))

    def set_measuring_rate(self):
        hzStr = self.lineEditHzNumber.text().strip()
        if not hzStr.isdigit():
            QtWidgets.QMessageBox.warning(self, "输入错误", "请输入频率(Hz)")
            return
        hz = int(hzStr)
        if hz <= 0:
            QtWidgets.QMessageBox.warning(self, "输入错误", "请输入有效的正数频率")
            return
        lineTime = 1000000 // hz
        cmd = f"SetAcquisitionLineTime={lineTime}\r"
        self.dll.EthernetScanner_WriteData(self.hScanner, cmd.encode(), len(cmd))
        QtWidgets.QMessageBox.information(
            self, "成功", f"已设置采集线时间: {lineTime} us\n对应频率: {hz} Hz"
        )

    def reboot_camera(self):
        if not self.hScanner:
            QtWidgets.QMessageBox.warning(self, "未连接", "请先连接设备")
            return
        confirm = QtWidgets.QMessageBox.question(
            self,
            "确认重启",
            "确定要重启设备吗？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
        )
        if confirm == QtWidgets.QMessageBox.No:
            return
        cmd = "SetReboot\r"
        self.dll.EthernetScanner_WriteData(self.hScanner, cmd.encode(), len(cmd))
        QtWidgets.QMessageBox.information(self, "命令已发送", "设备正在重启...")

    def set_mode(self):
        if not self.hScanner:
            QtWidgets.QMessageBox.warning(self, "未连接", "请先连接设备")
            return
        modeValue = self.comboBoxMode.currentData()
        cmd = f"SetCameraMode={modeValue}\r"
        self.dll.EthernetScanner_WriteData(self.hScanner, cmd.encode(), len(cmd))
        QtWidgets.QMessageBox.information(
            self, "成功", f"已设置相机模式为: {modeValue}"
        )

    def read_property(self, prop_name, timeout=1000):
        buf = ctypes.create_string_buffer(128)
        ret = self.dll.EthernetScanner_ReadData(self.hScanner, prop_name.encode(), buf, 128, timeout)
        if ret == 0:  # 头文件定义，只有0是OK
            try:
                return buf.value.decode(errors="ignore").strip()
            except Exception as e:
                return "decode error"
        return None

    def on_timer(self):
        if self.hScanner:
            status = ctypes.c_int(0)
            self.dll.EthernetScanner_GetConnectStatus(self.hScanner, ctypes.byref(status))
            if status.value == CONNECTED:
                self.bScannerConnectStatus = True
                self.lineEditStatus.setText("连接")
                self.lineEditStatus.setStyleSheet("QLineEdit {background: green; color: white;}")
            else:
                self.bScannerConnectStatus = False
                self.lineEditStatus.setText("已断开")
                self.lineEditStatus.setStyleSheet("QLineEdit {background: red;}")

            with self.freq_lock:
                freq = self.dwScanner_Frequency
                self.dwScanner_Frequency = 0
                self.iCnt += freq
            self.lineEditFrequency.setText(f"{freq} Hz  PicCntErr: {self.iPicCntErr}  Cnt: {self.iCnt}")
            self.lineEditFiFo.setText(f"CPU FiFo: {self.cpu_fifo_value}   DLL FiFo: {self.dll_fifo_value}")
            self.labelHTLEncoder.setText(str(self.htl_encoder))
            self.labelTTLEncoder.setText(str(self.ttl_encoder))
            scanner_state = self.read_property("ScannerState")
            try:
                state_int = int(scanner_state)
                if (state_int & (1 << 5)):
                    self.lineEditMeasureRate.setText("Too fast")
                    self.lineEditMeasureRate.setStyleSheet("QLineEdit {background: red;}")
                else:
                    self.lineEditMeasureRate.setText("Ok")
                    self.lineEditMeasureRate.setStyleSheet("QLineEdit {background: green; color: white;}")
            except Exception:
                self.lineEditMeasureRate.setText("未知")
                self.lineEditMeasureRate.setStyleSheet("QLineEdit {background: gray; color: white;}")
        else:
            self.lineEditStatus.setText("未连接")
            self.lineEditStatus.setStyleSheet("")

    def show_settings_window(self):
        if self.bScannerConnectStatus:
            if not hasattr(self, 'pSettings') or self.pSettings is None:
                self.pSettings = SettingsWindow(self)
            self.pSettings.exchange_data(self.hScanner, self.strOrderNumber, self.lineEditIp.text().strip())
            self.pSettings.show()
            self.pSettings.raise_()
            self.pSettings.activateWindow()
        else:
            QtWidgets.QMessageBox.critical(self, "Error", "Sensor should be connected")


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())