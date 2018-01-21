from progress.bar import Bar

bar = Bar('Processing', max=20)
for i in range(20):
    # Do some work
    bar.next()
bar.finish()
'''pckPath = "C:\ProgramData\Anaconda3\envs\py33\Lib\site-packages"
sys.path.append(pckPath)

Page=PyOrigin.ActivePage()
CurPageName = Page.GetName()
wks=PyOrigin.WorksheetPages(CurPageName).Layers(0)
Col=wks.Columns(0)
Col.SetComments('Comments')'''

'''def window():
    sys.argv = ['']
    app = QApplication(sys.argv)
    widget = QWidget()
    list_box = QComboBox(widget)
    for it in items:
        list_box.addItem(it)
    list_box.currentIndexChanged.connect(selectionchange)
    list_box.move(50, 50)
    widget.setWindowTitle("Choose script")
    widget.show()
    app.exec_()'''