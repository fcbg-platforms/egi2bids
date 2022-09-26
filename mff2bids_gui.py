import sys
from mff2bids import mff2bids
from pathlib import Path
from mne_bids import BIDSPath
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

class bidsToEgiGui(QWidget):
	def __init__(self, parent = None):
		super(bidsToEgiGui, self).__init__(parent)
		
		self.EGIfile = None
		self.rootDir = None
		self.form = {'Task Name': None,
					'Subject ID': None,
					'Session': None,
					'Run': None}
		self.formLabel = {}
		self.formLineEdit = {}
		self.current_BIDSPath = None
		
		# main window layout
		layout = QVBoxLayout()
		
		# data file to be converted
		# layoutEGIFile = QHBoxLayout()
		layoutInputBrowesable = QGridLayout()
		self.labelEGIFile = QLabel('EGI file to be converted:')
		self.contentEGIFile = QLineEdit()
		self.contentEGIFile.editingFinished.connect(self.checkEGIFile)
		self.btnBrowseEGIFile = QPushButton("...")
		self.btnBrowseEGIFile.clicked.connect(self.getEGIFile)
		
		layoutInputBrowesable.addWidget(self.labelEGIFile,0,0)
		layoutInputBrowesable.addWidget(self.contentEGIFile,0,1)
		layoutInputBrowesable.addWidget(self.btnBrowseEGIFile,0,2)
		
		# root directory layout
		# layoutRootDir = QHBoxLayout()
		self.labelRootDir = QLabel('BIDS root directory:')
		self.contentRootDir = QLineEdit()
		self.contentRootDir.editingFinished.connect(self.checkRootDir)
		self.btnBrowseRootDir = QPushButton("...")
		self.btnBrowseRootDir.clicked.connect(self.getRootDir)
		
		layoutInputBrowesable.addWidget(self.labelRootDir,1,0)
		layoutInputBrowesable.addWidget(self.contentRootDir,1,1)
		layoutInputBrowesable.addWidget(self.btnBrowseRootDir,1,2)
		
		# form layout for all other entries
		layoutForm = QFormLayout()
		
		# form widgets
		for key,val in self.form.items():
			self.formLabel[key] = QLabel(key + ':')
			# self.labelForm[key].keyname = key
			self.formLineEdit[key] = QLineEdit()
			self.formLineEdit[key].keyname = key
			self.formLineEdit[key].editingFinished.connect(self.checkForm)
			layoutForm.addRow(self.formLabel[key],self.formLineEdit[key])
		
		# self.contentTask.setToolTip("Input the name of your task.")
		
		# current BIDS path
		self.labelCurrentBIDSPath = QLabel('Current BIDS Path: ')
		
		
		# write button
		self.btnWriteBIDS = QPushButton("Write BIDS")
		self.btnWriteBIDS.setFixedSize(120,30)
		self.btnWriteBIDS.clicked.connect(self.onClickWriteBIDS)
		
		# log box
		self.logBox = QTextEdit()
		self.logBox.setReadOnly(True)
		
		# credits
		urlCredits = "<a href=\'https://github.com/fcbg-hnp/bids'>https://github.com/fcbg-hnp/bids</a>"
		self.labelCredits = QLabel(urlCredits)
		
		# 
		layout.addLayout(layoutInputBrowesable)		
		layout.addSpacing(25)
		layout.addLayout(layoutForm)
		layout.addSpacing(10)
		layout.addWidget(self.labelCurrentBIDSPath)
		layout.addSpacing(15)
		layout.addWidget(self.btnWriteBIDS,alignment=Qt.AlignmentFlag.AlignHCenter)
		layout.addSpacing(15)
		layout.addWidget(self.logBox)
		layout.addWidget(self.labelCredits)
		self.setLayout(layout)
		
		self.setWindowTitle("EGI to BIDS converter")
	
	def getRootDir(self):
		pname = QFileDialog.getExistingDirectory(parent=self, caption='Pick directory...',directory='./')
		self.contentRootDir.setText(pname)
		self.checkRootDir()
		
	def checkRootDir(self):
		pname = self.contentRootDir.text()
		self.pushLog('BIDS root directory set to ' + pname)
		self.rootDir = pname
		if not Path(pname).exists():
			self.pushLog('BIDS root directory does not exist. New directory will be created.',flag='warning')
		self.updateCurrentBIDSPath()
		
	def getEGIFile(self):
		pname = QFileDialog.getExistingDirectory(parent=self, caption='Pick directory...',directory='./')
		self.contentEGIFile.setText(pname)
		self.checkEGIFile()
		# self.pushLog('file to be converted set to ' + pname)
		# ext = Path(pname).suffix
		# if ext.lower() != '.mff':
			# self.pushLog('EGI folder has no .mff extension',flag='warning')	
		
	def checkEGIFile(self):
		fname = self.contentEGIFile.text()
		self.pushLog('EGI folder set to ' + fname)
		ext = Path(fname).suffix
		if fname == '':
			self.EGIfile = None
		elif not Path(fname).exists():
			self.pushLog('EGI folder does not exist',flag='warning')
		else:
			if ext.lower() != '.mff':
				self.pushLog('EGI folder has no .mff extension',flag='warning')
		self.EGIfile = fname
	
	def checkForm(self):
		target = self.sender()
		input = target.text()
		self.form[target.keyname] = input
		self.updateCurrentBIDSPath()
		self.pushLog('parameter ' + target.keyname + ' set to ' + input)
	
	def updateCurrentBIDSPath(self):
		if self.rootDir is not None:
			self.current_BIDSPath = BIDSPath(root=self.rootDir)
			self.current_BIDSPath.update(subject=self.form['Subject ID'])
			self.current_BIDSPath.update(session=self.form['Session'])
			self.current_BIDSPath.update(task=self.form['Task Name'])
			self.current_BIDSPath.update(run=self.form['Run'])
			self.current_BIDSPath.update(datatype='eeg')
			self.current_BIDSPath.update(extension='.eeg')
			
			self.labelCurrentBIDSPath.setText(str(self.current_BIDSPath.directory) + '\\' + self.current_BIDSPath.basename + '_*')
		else:
			self.current_BIDSPath = None
			self.labelCurrentBIDSPath.setText(None)
			
	
	def onClickWriteBIDS(self):
		status = True
		
		if self.EGIfile is None:
			self.pushLog('EGI file must be defined',flag='error')
			status = False
		
		if self.rootDir is None:
			self.pushLog('BIDS root directory must be defined',flag='error')
			status = False
		
		if self.form['Subject ID'] is None:
			self.pushLog('subject ID must be defined',flag='error')
			status = False
		
		if status:
			self.writeBIDS()
		
	def writeBIDS(self):
		self.pushLog('writting BIDS...')
		mff2bids(self.EGIfile, self.rootDir,
					subject = self.form['Subject ID'],
					task=self.form['Task Name'],
					session=self.form['Session'],
					run=self.form['Run'])
					
		self.pushLog('BIDS written successfuly')
	
	def pushLog(self,text,flag=None):
		if flag == 'warning':
			self.logBox.append(">> [WARNING] " + text)
		elif flag == 'error':
			self.logBox.append(">> [ERROR] " + text)
		else:
			self.logBox.append(">> " + text)
			

def main():
	app = QApplication(sys.argv)
	ex = bidsToEgiGui()
	ex.resize(800, 500)
	ex.show()
	sys.exit(app.exec())
	
if __name__ == '__main__':
	main()
	