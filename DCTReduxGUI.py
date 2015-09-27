import tkinter as tk
from tkinter import ttk
from DCTRedux import *
import os
import fnmatch
import pdb

class DCTReduxGUI(object):

    ### Constructor ###
    
    def __init__(self):

        #Define empty lists which will contain the loaded in
        #images that are input through the input tab
        self._bias = []
        self._flat = []
        self._image = []
        self._processedImage = None

        #Define the main GUI frame and the innter Notebook structure
        self.root = tk.Tk()
        self.root.title('DCT Reduction Pipleline')
        self.note = ttk.Notebook(self.root)

        #Call the methods to create components of the GUI incluidng
        #the menubar, tabs in the Notebook, and help windows
        self.__createMenubar()
        self.greetingsTab     = self.__createGreetingsTab()
        self.inputTab         = self.__createInputTab()
        self.analysisTab      = self.__createAnalysisTab()
        

        #Set the size of the GUI and begin running it
        self.note.pack()
        self.root.mainloop()


    ### GUI Creation Methods ###
    
    def __createMenubar(self):
        """
        A "private" method for defining the menubar in the GUI.
        """

        #Define the menubar
        menubar = tk.Menu(self.root)

        #Defines the file menu which contains choices related to
        #working with the gui or the files in the gui
        fileMenu = tk.Menu(menubar, tearoff = 0)
        fileMenu.add_command(label = 'Quit', command = lambda: self.root.destroy())
        menubar.add_cascade(label = 'File', menu = fileMenu)

        #Defines the options menu which contains choices related to
        #various options in processing and analysis
        optionsMenu = tk.Menu(menubar, tearoff = 0)
        loadOptions = tk.Menu(optionsMenu, tearoff = 0)
        self.subtractOverscan = tk.BooleanVar()
        self.subtractOverscan.set(True)
        loadOptions.add_checkbutton(label = 'Correct for overscans', onvalue = 1, offvalue = 1, variable = self.subtractOverscan)
        self.removeCosmicRays = tk.BooleanVar()
        self.removeCosmicRays.set(True)
        loadOptions.add_checkbutton(label = 'Remove cosmic rays', onvalue = 1, offvalue = 1, variable = self.removeCosmicRays)
        optionsMenu.add_cascade(label = 'Load Options', menu = loadOptions)
        optionsMenu.add_command(label = 'Clear Loaded Images', command = lambda: self.clearLoadedImages())
        
        menubar.add_cascade(label = 'Options', menu = optionsMenu)

        #Add the menubar to the GUI
        self.root.config(menu = menubar)

    def __createGreetingsTab(self):
        """
        This is a "private" method designed to create all the components
        of the greetings tab in the notebook. This mainly contains a text
        of greeting and a button for starting (which switches to the input
        tab) and a button for exiting which closes the GUI.

        This method returns the actual tab object.
        """

        #Define the tab itself and add it to the notebook
        greetingsTab = ttk.Frame(self.note)
        self.note.add(greetingsTab, text = 'Greeting')

        #Define the greeting that will appear
        greeting = \
        'Welcome to the DCT Reduction Pipeline\n' \
        'GUI. This program was created by the BU\n' \
        'PyCon team and is designed for reducing\n' \
        'and analyzing images specifically from\n' \
        'the 4.3 m Discovery Channel Telescope.'

        #Place the greeting as a label and create two buttons, the configure the layout
        ttk.Label(greetingsTab, text = greeting, font = ('Century Gothic', 14, 'bold'), anchor = 'w', justify = 'left').grid(row = 0, column = 0, columnspan = 2, padx = 20, pady = 20)
        ttk.Button(greetingsTab, text = 'START', command = lambda: self.note.select(self.inputTab)).grid(row = 1, column = 0, sticky = 'nswe', padx = 5, pady = 5)
        ttk.Button(greetingsTab, text = 'EXIT', command = lambda: self.root.destroy()).grid(row = 1, column = 1, sticky = 'nswe', padx = 5, pady = 5)
        greetingsTab.rowconfigure(1, minsize = 50)
        greetingsTab.columnconfigure(0, weight = 10)
        greetingsTab.columnconfigure(1, weight = 1)

        return greetingsTab

    def __createInputTab(self):
        """
        Method for defining the components of the Input tab. This sets up a few
        text fields allowing for input of file names and paths.
        """

        #Define an empty dict which will contain refernces to the StringVar
        #objects associated with each text field
        self.inputEntryTxt = {}
        
        #Define the tab itself and add it to the notebook
        inputTab = ttk.Frame(self.note)
        self.note.add(inputTab, text = 'Input')

        #The label and help button at the top
        ttk.Label(inputTab, text = 'Enter the relevant information below', font = ('Century Gothic', 10, 'bold')).grid(row = 0, column = 0, columnspan = 2, sticky = 'W', padx = (2,0), pady = 2)
        ttk.Button(inputTab, text = '?', command = lambda: self.showInputHelp(), width = 2).grid(row = 0, column = 2, sticky = 'E', pady = 2)

        #The input path label and entry box
        ttk.Label(inputTab, text = 'Input Path', font = ('Cenutry Gothic', 9)).grid(row = 1, column = 0, stick = 'w', padx = (2,8), pady = 4)
        self.inputEntryTxt['Input Path'] = tk.StringVar()
        ttk.Entry(inputTab, textvariable = self.inputEntryTxt['Input Path'], width = 50).grid(row = 1, column = 1, columnspan = 2)

        #The input bias filenames label and entry box
        ttk.Label(inputTab, text = 'Bias Filenames', font = ('Cenutry Gothic', 9)).grid(row = 2, column = 0, stick = 'w', padx = (2,8), pady = 4)
        self.inputEntryTxt['Bias Filenames'] = tk.StringVar()
        ttk.Entry(inputTab, textvariable = self.inputEntryTxt['Bias Filenames'], width = 50).grid(row = 2, column = 1, columnspan = 2)

        #The input flat filenames label and entry box
        ttk.Label(inputTab, text = 'Flat Filenames', font = ('Cenutry Gothic', 9)).grid(row = 3, column = 0, stick = 'w', padx = (2,8), pady = 4)
        self.inputEntryTxt['Flat Filenames'] = tk.StringVar()
        ttk.Entry(inputTab, textvariable = self.inputEntryTxt['Flat Filenames'], width = 50).grid(row = 3, column = 1, columnspan = 2)

        #The input image filenames label and entry box
        ttk.Label(inputTab, text = 'Image Filenames', font = ('Cenutry Gothic', 9)).grid(row = 4, column = 0, stick = 'w', padx = (2,8), pady = 4)
        self.inputEntryTxt['Image Filenames'] = tk.StringVar()
        ttk.Entry(inputTab, textvariable = self.inputEntryTxt['Image Filenames'], width = 50).grid(row = 4, column = 1, columnspan = 2)

        #The load images button
        ttk.Button(inputTab, text = 'LOAD IMAGES', command = lambda: self.loadImages()).grid(row = 5, column = 0, columnspan = 3, stick = 'nswe', padx = (2,0), pady = 10)
        inputTab.rowconfigure(5, minsize = 55)
        
        return inputTab

    def __createAnalysisTab(self):
        analysisTab = ttk.Frame(self.note)
        self.note.add(analysisTab, text = 'Analysis')

        return analysisTab

    
    ### Utility Methods ###

    def showInputHelp(self):
        inputHelpWindow = tk.Toplevel(self.root)

        inputHelpText = \
        'On this screen you can enter the paths and filenames for images you want to\n' \
        'load into the program.\n\n' \
        'Filenames, which can include parts of a path, can be entered in several formats.\n' \
        'Extensions do not need to be included in the names. It is assumed they are .fits\n' \
        'files. Each of these input types is mutually exclusive and cannot be mixed with\n' \
        'another input type.\n' \
        '--  A single file can be input, with or without an exension.\n' \
        '--  Multiple files can be input, separated by commas (spaces are allowed).\n' \
        '--  If all the files have a common pre-fix, the prefix can be listed, then the\n' \
        '    signifying components can be listed in square brackets. E.g., if the files\n' \
        '    bias_01.fits, bias_02.fits, and bias_03.fits exist, you can enter them as\n' \
        '    bias_0[1,2,3].fits\n' \
        '--  You can also use the * wildcard character to match anything of any length.\n' \
        '    E.g., to load all bias images you can input "bias_*.fits"'
        ttk.Label(inputHelpWindow, text = inputHelpText, font = '-size 12').grid(row = 0, column = 0, padx = 2, pady = 2)
        ttk.Button(inputHelpWindow, text = 'OK', command = lambda: inputHelpWindow.destroy()).grid(row = 1, column = 0, sticky = 'nsew', padx = 2, pady = 5)
        inputHelpWindow.rowconfigure(1, minsize = 50)
    
    def loadImages(self):
        #Define the path where all files exist
        PATH = self.inputEntryTxt['Input Path'].get()
        if (PATH[-1] != '\\' and PATH[-1] != '/'): PATH += '/'
        
        #Load in bias images
        BIAS_PATH, files = self.__getFiles(PATH, self.inputEntryTxt['Bias Filenames'].get())
        for file in files:
            self._bias.append(Bias(BIAS_PATH + file,
                                   subtractOverscans = self.subtractOverscans.get(),
                                   removeCosmicRays = self.removeCosmicRays.get()))

        #Load in flat images
        FLAT_PATH, files = self.__getFiles(PATH, self.inputEntryTxt['Flat Filenames'].get())
        for file in files:
            self._bias.append(Flat(FLAT_PATH + file,
                                   subtractOverscans = self.subtractOverscans.get(),
                                   removeCosmicRays = self.removeCosmicRays.get()))

        #Load the the actual images
        IMAGE_PATH, files = self.__getFiles(PATH, self.inputEntryTxt['Image Filenames'].get())
        for file in files:
            self._bias.append(Image(IMAGE_PATH + file,
                                   subtractOverscans = self.subtractOverscans.get(),
                                   removeCosmicRays = self.removeCosmicRays.get()))

    def __getFiles(self, PATH, filenames):
        if ('.fits' in filenames):
            filenames = filenames.replace('.fits', '')
            
        files = []
        if ('*' in filenames):
            if ('\\' in filenames):
                PATH += filenames[0:filenames.rfind('\\')] + '\\'
                filenames = filenames[filenames.rfind('\\')+1:]
            if ('/' in filenames):
                PATH += filenames[0:filenames.rfind('/')] + '/'
                filenames = filenames[filenames.rfind('/')+1:]
            for f in os.listdir(PATH):
                if fnmatch.fnmatch(f, filenames+'.fits'):
                    files.append(f)
        elif ('[' in filenames and ']' in filenames):
            prefix, postfix = filenames.split('[')
            postfix = postfix[:-1].replace(' ','').split(',')
            files = [prefix + p + '.fits' for p in postfix]
        elif (',' in filenames):
            files = filenames.replace(' ','').split(',')
            files = [file + '.fits' for file in files]

        if (len(files) == 0):
            files = [filenames + '.fits']
        
        return PATH, files
    
    def clearLoadedImages(self):
        self._bias = []
        self._flat = []
        self._image = []
        self._processedImage = None

#This if statement is outside and apart from the class definition. In effect, this
#if statement says run an instance of the DCTReduxGUI if the call to this class was
#direct rather than being imported from another class.
if __name__ == '__main__':
    DCTReduxGUI()
