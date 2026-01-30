import sys
from PyQt5.QtWidgets import (QWidget, QPushButton, QLineEdit, 
    QInputDialog, QApplication)
 
 
class Dialog(QWidget):
    
    def __init__(self,title,tips,password):
        super().__init__()
        self.move(600,400)
        t = QInputDialog(self)
        if password:
            mode = QLineEdit.Password
        else:
            mode = QLineEdit.Normal
        self.result = t.getText(self, title,tips,echo=mode)
        
    # def get_text(self):
def main(title='输入',tips='请输入',password=False):
    app = QApplication(sys.argv)
    rr = Dialog(title=title,tips=tips,password=password).result
    return rr
if __name__ == '__main__':
    main()
    