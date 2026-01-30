# Исходный код автомата
SOURCE_CODE = r"""import sys
import random
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QMainWindow, QFrame, QGridLayout, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QStackedWidget, QDialog, QFormLayout, 
                             QComboBox, QDialogButtonBox, QScrollArea, QProgressBar)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPalette, QColor

class MachineCard(QFrame):
    def __init__(self, data):
        super().__init__()
        self.setFrameShape(QFrame.Shape.Box)
        layout = QHBoxLayout()
        
        # Цветной статус (Квадрат)
        status = QLabel()
        status.setFixedSize(20, 20)
        status.setAutoFillBackground(True)
        pal = status.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor("green" if data['status']=='work' else "red"))
        status.setPalette(pal)
        layout.addWidget(status)

        # Инфо
        info = QVBoxLayout()
        info.addWidget(QLabel(f"#{data['id']}"))
        info.addWidget(QLabel(data['name']))
        info.addWidget(QLabel(data['address']))
        layout.addLayout(info)

        # Деньги и Прогресс
        stats = QVBoxLayout()
        stats.addWidget(QLabel(f"Наличные: {data['cash']} ₽"))
        pbar = QProgressBar()
        pbar.setValue(data['stock_coffee'])
        pbar.setFixedHeight(10)
        pbar.setTextVisible(False)
        stats.addWidget(QLabel("Кофе:"))
        stats.addWidget(pbar)
        layout.addLayout(stats)
        self.setLayout(layout)

class MonitorPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.slayout = QVBoxLayout()
        content.setLayout(self.slayout)
        scroll.setWidget(content)
        layout.addWidget(scroll)
        self.setLayout(layout)
        
        data = [
            {"id": "901", "name": "ТЦ Плаза", "address": "Ленина 1", "status": "work", "cash": 5000, "stock_coffee": 80},
            {"id": "902", "name": "Вокзал", "address": "Мира 5", "status": "error", "cash": 1200, "stock_coffee": 10}
        ]
        for d in data: self.slayout.addWidget(MachineCard(d))

class AddDialog(QDialog):
    def __init__(self, data=None):
        super().__init__()
        self.setWindowTitle("Автомат")
        layout = QFormLayout()
        self.n = QLineEdit(data['name'] if data else "")
        layout.addRow("Название:", self.n)
        self.m = QComboBox()
        self.m.addItems(["Necta", "Unicum"])
        if data: self.m.setCurrentText(data['maker'])
        layout.addRow("Модель:", self.m)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)
        self.setLayout(layout)
    def get(self): return {"name": self.n.text(), "maker": self.m.currentText()}

class TablePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        btns = QHBoxLayout()
        for t, f in [("Добавить", self.add), ("Изменить", self.edit), ("Удалить", self.delete)]:
            b = QPushButton(t)
            b.clicked.connect(f)
            btns.addWidget(b)
        layout.addLayout(btns)
        
        self.tab = QTableWidget(0, 3)
        self.tab.setHorizontalHeaderLabels(["ID", "Название", "Модель"])
        self.tab.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tab.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tab.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.tab)
        self.setLayout(layout)
        self.add_row("101", "Офис Яндекс", "Necta")

    def add_row(self, i, n, m):
        r = self.tab.rowCount()
        self.tab.insertRow(r)
        self.tab.setItem(r, 0, QTableWidgetItem(i))
        self.tab.setItem(r, 1, QTableWidgetItem(n))
        self.tab.setItem(r, 2, QTableWidgetItem(m))

    def add(self):
        if (d := AddDialog()).exec(): 
            res = d.get()
            self.add_row(str(random.randint(100,999)), res['name'], res['maker'])

    def edit(self):
        if (r := self.tab.currentRow()) != -1:
            d = AddDialog({"name": self.tab.item(r, 1).text(), "maker": self.tab.item(r, 2).text()})
            if d.exec():
                res = d.get()
                self.tab.item(r, 1).setText(res['name'])
                self.tab.item(r, 2).setText(res['maker'])

    def delete(self):
        if (r := self.tab.currentRow()) != -1:
            self.tab.removeRow(r)

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        layout = QGridLayout()
        # Цветные квадраты через QPalette
        for i, (txt, col) in enumerate([("Эффективность\n100%", "green"), ("Ошибки\n2 шт", "red"), ("Выручка\n15000", "gray")]):
            fr = QFrame()
            fr.setAutoFillBackground(True)
            pal = fr.palette()
            pal.setColor(QPalette.ColorRole.Window, QColor(col))
            fr.setPalette(pal)
            l = QVBoxLayout()
            lbl = QLabel(txt)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # Белый текст на цветном фоне
            p_lbl = lbl.palette()
            p_lbl.setColor(QPalette.ColorRole.WindowText, QColor("white"))
            lbl.setPalette(p_lbl)
            l.addWidget(lbl)
            fr.setLayout(l)
            layout.addWidget(fr, 0, i)
        self.setLayout(layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(800, 600)
        cw = QWidget()
        self.setCentralWidget(cw)
        layout = QHBoxLayout(cw)

        # Меню
        menu = QFrame()
        menu.setFixedWidth(150)
        menu.setAutoFillBackground(True)
        pal = menu.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor("#2c3e50")) # Темно-синий фон
        menu.setPalette(pal)
        
        mlayout = QVBoxLayout(menu)
        self.stack = QStackedWidget()
        
        for name, idx in [("Главная", 0), ("Таблица", 1), ("Монитор", 2)]:
            btn = QPushButton(name)
            p = btn.palette()
            p.setColor(QPalette.ColorRole.ButtonText, QColor("white")) # Белый текст
            btn.setPalette(p)
            btn.clicked.connect(lambda _, i=idx: self.stack.setCurrentIndex(i))
            mlayout.addWidget(btn)
        mlayout.addStretch()
        layout.addWidget(menu)

        self.stack.addWidget(Dashboard())
        self.stack.addWidget(TablePage())
        self.stack.addWidget(MonitorPage())
        layout.addWidget(self.stack)

class Login(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(300, 200)
        l = QVBoxLayout()
        l.addWidget(QLabel("Логин: (admin)"))
        self.u = QLineEdit()
        l.addWidget(self.u)
        l.addWidget(QLabel("Пароль: (123)"))
        self.p = QLineEdit()
        self.p.setEchoMode(QLineEdit.EchoMode.Password)
        l.addWidget(self.p)
        b = QPushButton("Войти")
        b.clicked.connect(self.check)
        l.addWidget(b)
        self.setLayout(l)

    def check(self):
        if self.u.text() == "admin" and self.p.text() == "123":
            self.win = MainWindow()
            self.win.show()
            self.close()
        else: QMessageBox.warning(self, "Ошибка", "Неверно")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = Login()
    w.show()
    sys.exit(app.exec())
"""