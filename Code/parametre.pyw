from tkinter import filedialog
from tkinter import *
import serial
import json

#http://apprendre-python.com/page-tkinter-interface-graphique-python-tutoriel


class HoverButton(Button):
    def __init__(self, master, **kw):
        Button.__init__(self,master=master,**kw)
        self.defaultBackground = self["background"]
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, e):
        self['background'] = self['activebackground']

    def on_leave(self, e):
        self['background'] = self.defaultBackground

class InputNumber:
    def __init__(self, master, name, bind=None, default="0", **kw):
        var = StringVar(master)
        var.set(default)

        number = len(inputList)

        self.name = name
        self.label = Label(master, text=name)
        self.label.grid(row=number, sticky=W, padx=10)
        self.spinBox = Spinbox(master, from_=1, to=50, command=bind, textvariable=var, **kw)
        self.spinBox.grid(row=number, column=1, sticky=E, padx=10)
        
    def value(self):
        try:
            return float(self.spinBox.get())
        except:
            return 0
        

def intToTime(intTime):
    totalTime = intTime
    hours = (intTime-intTime%3600)/3600
    totalTime -= 3600*hours
    minutes = (intTime-intTime%60)/60
    totalTime -= 60*minutes

    returnString = ""

    if hours != 0:
        returnString += str(hours) + "h "
    if minutes != 0:
        returnString += str(minutes) + "m "
    if totalTime != 0:
        returnString += str(totalTime) + "s"

    return returnString


def saveJson():
    path = filedialog.asksaveasfilename(initialdir = "/",title = "Select file",filetypes = (("json files","*.json"),("all files","*.*")))

    data = {}
    data['dimensions'] = []
    data['dimensions'].append({  
        'pNumber': inputList[0].value(),
        'pSize': inputList[1].value(),
        'pTime': inputList[2].value()
    })
    
    with open(path, 'w') as outfile:  
        json.dump(data, outfile, indent=2)


def loadJson():
    path = filedialog.askopenfilename(initialdir = "/",title = "Select file",filetypes = (("json files","*.json"),("all files","*.*")))
    
    with open(path) as json_file:  
        data = json.load(json_file)
        inputList[0].spinBox.delete(0, END)
        inputList[1].spinBox.delete(0, END)
        inputList[2].spinBox.delete(0, END)
        inputList[0].spinBox.insert(END, str(data['dimensions'][0]['pNumber']))
        inputList[1].spinBox.insert(END, str(data['dimensions'][0]['pSize']))
        inputList[2].spinBox.insert(END, str(data['dimensions'][0]['pTime']))


# Check wether it is imported or not, if not then run this
if __name__ == '__main__':

    #Global variables
    pipeSpacing = 30
    width = 100
    height = 100

    app = Tk()
    app.title('DaphnieMaton')
    app.geometry("640x360")
    app.minsize(640, 360)
    app.iconbitmap('C:\\Users\\Administrateur\\Desktop\\DaphniMaton\\Images\\logo.ico')

    # Declare frames
    Inputs = Frame(app)
    Drawing = Frame(app)
    Bottom = Frame(app)

    #region Menu
    menubar = Menu(app)
    menubar.add_command(label="Sauvegarder", command=saveJson)
    menubar.add_command(label="Ouvrir", command=loadJson)

    app.config(menu=menubar)
    #endregion

    #region Drawing
    def onResize(event):
        global width
        global height
        width, height = event.width, event.height
        drawPipes()

    def drawPipes():
        global width
        global height
        canvas.delete("all")

        pipeNb = int(inputList[0].value())

        if pipeNb != 0:
            pipeLength = inputList[1].value()
            pipSize = max(height/2 - 100, 50)
            pipeTime = inputList[2].value()

            y = height/2
            maxLeft = width/2 - (pipeNb/2)*pipeSpacing - 25

            for n in range(pipeNb):
                x = width/2 + (n - pipeNb/2)*pipeSpacing
                canvas.create_rectangle(x-5, y+pipSize, x+5, y-pipSize, fill="#425ff4")

            canvas.create_line(maxLeft, y+pipSize+5, maxLeft, y-pipSize-5, fill="#476042", width=3)
            canvas.create_line(maxLeft-1, y+pipSize+5, maxLeft+5, y+pipSize+5, fill="#476042", width=3)
            canvas.create_line(maxLeft-1, y-pipSize-5, maxLeft+5, y-pipSize-5, fill="#476042", width=3)
            canvas.create_text(maxLeft-25, y, text=str(pipeLength))

            canvas.create_text(width-5, height-5, text="Total length: " + str(pipeLength*pipeNb) + "m", anchor="se")
            # pretify this shit please
            canvas.create_text(width-5, height-20, text="Total time: " + intToTime(pipeTime*pipeNb), anchor="se")


    
    canvas = Canvas(Drawing, width=width, height=height, background='yellow')
    canvas.bind("<Configure>", onResize)
    
    #endregion

    #region Inputs

    inputList = []

    inputList.append(InputNumber(Inputs, "Nombre de tuyeau", bind=drawPipes, default="2"))
    inputList.append(InputNumber(Inputs, "Taille de tuyeau (m)", bind=drawPipes, default="1.2", increment=0.1))
    inputList.append(InputNumber(Inputs, "Temps pour un tuyeau (sec)", bind=drawPipes, default="10"))

    # To auto-extend the cells on the Y axes
    Grid.columnconfigure(Inputs, 0, weight=1)
    Grid.columnconfigure(Inputs, 1, weight=1)

    #endregion

    #region UpdateFlash
    def update():
        for inputs in inputList:
            print(inputs.value())

    def flash():
        print("not implemented yet")

    HoverButton(Bottom, text="UPDATE", relief=FLAT, activebackground='grey', command=update).pack(side=RIGHT, padx=10, pady=10)
    HoverButton(Bottom, text="FLASH", relief=FLAT, activebackground='grey', command=flash).pack(side=LEFT, padx=10, pady=10)
    #endregion

    # Pack everything
    canvas.pack(fill=BOTH, expand=True)

    Bottom.pack(side=BOTTOM, fill=X)
    Inputs.pack(expand=NO, fill=X)
    Drawing.pack(expand=YES, fill=BOTH)

    # Update canvas for none handled events (manually changing a spinbox)
    def lateUpdateCanvas():
        drawPipes()
        app.after(100, lateUpdateCanvas)

    lateUpdateCanvas()
    app.mainloop()