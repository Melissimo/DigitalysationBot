# -*- coding: utf-8 -*-
from PyQt5 import QtCore, QtGui, QtWidgets
import ProxiesModule  
import Custom_Logger  # Importazione del logger personalizzato
import AccountsModule

class Ui_DigitalysationTelegramBot(object):
    def setupUi(self, DigitalysationTelegramBot):
        Custom_Logger.setup_logger("GUI", "Inizio configurazione UI.")  # Log dell'inizio della configurazione dell'UI

        DigitalysationTelegramBot.setObjectName("DigitalysationTelegramBot")
        DigitalysationTelegramBot.resize(800, 600)
        self.centralwidget = QtWidgets.QWidget(DigitalysationTelegramBot)
        self.centralwidget.setObjectName("centralwidget")
        
        self.Proxies = QtWidgets.QPushButton(self.centralwidget)
        self.Proxies.setGeometry(QtCore.QRect(20, 20, 131, 51))
        self.Proxies.setObjectName("Proxies")
        self.Proxies.clicked.connect(lambda: ProxiesModule.handle_proxies(self))  # Connette il segnale clicked al modulo esterno
        Custom_Logger.setup_logger("GUI", "Pulsante Proxies inizializzato.")  # Log per il pulsante Proxies

        self.Accounts = QtWidgets.QPushButton(self.centralwidget)
        self.Accounts.setGeometry(QtCore.QRect(20, 80, 131, 51))
        self.Accounts.setObjectName("Accounts")
        self.Accounts.clicked.connect(lambda: AccountsModule.handle_accounts(self))  # Nuova linea
        Custom_Logger.setup_logger("GUI", "Pulsante Accounts inizializzato.")  # Log pre-esistente
    
        self.Adder = QtWidgets.QPushButton(self.centralwidget)
        self.Adder.setGeometry(QtCore.QRect(20, 140, 131, 51))
        self.Adder.setObjectName("Adder")
        Custom_Logger.setup_logger("GUI", "Pulsante Adder inizializzato.")  # Log per il pulsante Adder

        self.tableView = QtWidgets.QTableView(self.centralwidget)
        self.tableView.setGeometry(QtCore.QRect(210, 20, 461, 201))
        self.tableView.setObjectName("tableView")
        Custom_Logger.setup_logger("GUI", "TableView inizializzato.")  # Log per la TableView

        self.textEdit = QtWidgets.QTextEdit(self.centralwidget)
        self.textEdit.setGeometry(QtCore.QRect(210, 340, 461, 151))
        self.textEdit.setObjectName("textEdit")
        self.textEdit.setDisabled(True)  # Disabilita il textEdit
        Custom_Logger.setup_logger("GUI", "TextEdit inizializzato e disabilitato.")  # Log per il TextEdit

        self.MessageLabel = QtWidgets.QLabel(self.centralwidget)
        self.MessageLabel.setGeometry(QtCore.QRect(210, 240, 461, 61))
        self.MessageLabel.setObjectName("MessageLabel")
        self.MessageLabel.setText("Benvenuto nel bot di Digitalysation per Telegram")  # Inizializza la label
        self.MessageLabel.setAlignment(QtCore.Qt.AlignCenter)  # Centra il testo
        self.MessageLabel.setWordWrap(True)  # Abilita il ritorno a capo automatico
        Custom_Logger.setup_logger("GUI", "Label del messaggio inizializzata e configurata.")  # Log per la MessageLabel

        self.Invio = QtWidgets.QPushButton(self.centralwidget)
        self.Invio.setGeometry(QtCore.QRect(380, 500, 131, 51))
        self.Invio.setObjectName("Invio")
        self.Invio.setDisabled(True)  # Disabilita il pulsante Invio
        Custom_Logger.setup_logger("GUI", "Pulsante Invio inizializzato e disabilitato.")  # Log per il pulsante Invio

        DigitalysationTelegramBot.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(DigitalysationTelegramBot)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        Custom_Logger.setup_logger("GUI", "MenuBar inizializzato.")  # Log per la MenuBar

        DigitalysationTelegramBot.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(DigitalysationTelegramBot)
        self.statusbar.setObjectName("statusbar")
        DigitalysationTelegramBot.setStatusBar(self.statusbar)
        Custom_Logger.setup_logger("GUI", "StatusBar inizializzato.")  # Log per la StatusBar

        self.retranslateUi(DigitalysationTelegramBot)
        QtCore.QMetaObject.connectSlotsByName(DigitalysationTelegramBot)
        Custom_Logger.setup_logger("GUI", "Configurazione UI completata.")  # Log per la fine della configurazione dell'UI

    def retranslateUi(self, DigitalysationTelegramBot):
        _translate = QtCore.QCoreApplication.translate
        DigitalysationTelegramBot.setWindowTitle(_translate("DigitalysationTelegramBot", "Digitalisation Telegram Bot"))
        self.Proxies.setText(_translate("DigitalysationTelegramBot", "Proxies"))
        self.Accounts.setText(_translate("DigitalysationTelegramBot", "Accounts"))
        self.Adder.setText(_translate("DigitalysationTelegramBot", "Adder"))
        self.Invio.setText(_translate("DigitalysationTelegramBot", "Invio"))

if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    DigitalysationTelegramBot = QtWidgets.QMainWindow()
    ui = Ui_DigitalysationTelegramBot()
    ui.setupUi(DigitalysationTelegramBot)
    DigitalysationTelegramBot.show()
    sys.exit(app.exec_())
