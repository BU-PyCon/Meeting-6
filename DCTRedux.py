import abc
import copy
import numpy as np
import re
import sys
from astropy.io import fits
import astropy.visualization as vis
import matplotlib.pyplot as plt

###----------------------------------------------
#
# Name:     DataEnc
#
# Purpose:  This is an abstract class designed to
#           encapsulate all the data in a fits
#           file obtained from the DCT. This class
#           keeps track of header information,
#           accessible through various properties,
#           as well as the actual image data.
#           This class can also defines methods of
#           operating on and analyzing the image
#           such as adding multiple files together
#           or doing photometry.
#
###----------------------------------------------

class DataEnc(metaclass = abc.ABCMeta):
    
    ### Constructor ###
    
    def __init__(self, path, subtractOverscans, removeCosmicRays):
        """
        Contains all the data from the input fits file.
        
        This constructor reads in a fits file from the DCT
        and separates out certain header information as well
        as the actual image data.
        
        Keywords:
        subtractOverscans   Boolean determining whether to subtract
                            the mean of the prescan and overscan.
                            Defaults to true.
        removeCosmicRays    Boolean determining whether to remove
                            anomalously high points which result
                            from cosmic rays. Defaults to true.
        
        Properties:
        airmass         The airmass of the observation
        date            The UTC date and time of the observation in
                        the format YYYY-MM-DD   HH:MM:SS.SS
        dec             The declination of the observation in the
                        format +DD:(AM)(AM):(AS)(AS).(AS)(AS)
        dim             Dimensions of the image as a tuple, returned
                        as width, then height, in pixels.
        expTime         The total exposure time, in seconds.
        filter          The filter used on the image, if any.
        gain            The gain used in reading out the CCD.
        height          The height of the image, in pixels.
        hourAngle       The hour angle of the point of observation.
        image           The actual 2D numpy array of the image in the
                        fits file. This has already had the prescan and
                        overscan removed.
        plateScale      The plateScale of the device.
        obsType         The type of observation of the image, e.g., bias,
                        flat, object, etc.
        overscan        A numpy 2D array of the overscan region from the image.
        overscanPix     The pixel width of the overscan region.
        prescan         A numpy 3D array of the prescan region from the image.
        prescanPix      The pixel width of the prescan region.
        ra              The right ascension of the observation in the format
                        HH:MM:SS.SS
        width           The width of the image, in pixels
        """
        try:
            #Get a name for this image from the path
            try:
                self.name = [re.split('[\\,/]', path)[-1][:-5]]
            except:
                self.name = [path]
            
            #Read in the image
            fitsData = fits.open(path)
            
            #Extract the header and data
            self.__header = [fitsData[0].header]
            data = np.transpose(fitsData[0].data)
            
            #Extract the prescan, image, and overscan
            self.__prescan     = data[0:self.__header[0]['PRESCAN']]
            self.__image       = np.transpose(data[self.__header[0]['PRESCAN']:self.__header[0]['NAXIS1']-self.__header[0]['POSTSCAN']])
            self.__postscan    = data[self.__header[0]['NAXIS1']-self.__header[0]['POSTSCAN']:]
            
            #Correct the image
            self.__correctImage(subtractOverscans, removeCosmicRays)

            #Keep an original copy of the image, in case we have to revert back to it
            self.__original = self.__image
            
        except FileNotFoundError:
            print('FileNotFoundError: Could not find "'+path+'"')
            sys.exit()
        
        except OSError:
            print('OSError: Incorrect file type')
            sys.exit()
    
    ### Utility Methods ###
    
    def __correctImage(self, subtractOverscans, removeCosmicRays):
        """
        Name: __correctImage

        Description:
        Internal "private" method to correct images for various
        factors such as overscan biases and cosmic rays.

        Parameters:
        subtractOverscans    This is a boolean indicating whether the overscans
                             should be used to correct the image.
        removeCosmicRays     This is a boolean indicating whether anomalously
                             high values, i.e., cosmic rays, should be smoothed out
        """
        if (subtractOverscans):
            #Fine the mean of both the pre and post scan regions and subtract that value
            #from each element of the image.
            overscanMean = np.mean(np.concatenate((self.prescan, self.postscan)))
            self.__image -= overscanMean

        if (removeCosmicRays):
            #This component removes anomalously high values within the image by setting it
            #to the average of the surrounding values instead.
            pass
    
    def scale(self, scale = 'linear', power = 1.0, min_cut = None, max_cut = None):
        """
        Name: scale

        Description:
        Allows for rescaling the image. This will always scale the original
        image so calling scale a second time on the image will overwrite
        a previous scaling.

        Parameters:
        scale
        power
        min_cut
        max_cut
        """
        self.__image = vis.scale_image(self.__original,
                                       scale = scale,
                                       power = power,
                                       min_cut = min_cut,
                                       max_cut = max_cut)
    
    ### Class Methods ###
    
    @classmethod
    def avg(cls, *args):
        """
        Name: avg
        
        Description:
        Averages a bunch of fits files together. This is acheived by
        simply adding them all together, then dividing the prescan,
        image, and overscan arrays by the number of images combined.
        Since the images were all added together, the header info
        contains the info of all those averaged together.

        This is a class method and thus must be called from the class
        rather than from a specific instance.
        
        Parameters:
        *args    A list of arguments which should include instances
                 of DataEnc that can be added together.
        
        Returns:
        A new instance of DataEnc which is the average of all those
        input as arguments.
        
        """
        result = sum(args)
        result.__prescan  /= self.numbImagesCombined
        result.__image    /= self.numbImagesCombined
        result.__original /= self.numbImagesCombined
        result.__postscan /= self.numbImagesCombined
        
        return result
    
    ### Magic Methods ###
    
    def __add__(self, other):
        """
        Name: __add__
        
        Description:
        Overrides the add method to allow for adding multiple
        images together, resulting in a new image which is the sum of the
        two. The headers and name of the individual images are appended
        together into an array.
        
        Parameters:
        other   The other instance of this class which is being added to
                this instance.
        
        Returns:
        A new instance which is the sum of this instance and the input instance.
        The new header will be a list containing the header of both individual
        instances while the actual data arrays will simply be summed element-wise.
        This method will make sure to only add instances together if they have
        the same conditions.
        """
        try:
            result = copy.deepcopy(self)    #Create a deep copy so as to not change this instance
            result.name.append(other.name[0])
            result.__header.append(other.__header[0])
            result.__prescan  += other.__prescan
            result.__image    += other.__image
            result.__original += other.__original
            result.__postscan += other.__postscan
            
            return result
        except ValueError:
            print('ValueError: Could not add images together. Improper sizes')
            return
    
    def __div__(self, other):
        """
        Name: __div__
        
        Description:
        Overrides the divide method to allow for dividing multiple
        images together, resulting in a new image which is the first divided by the
        second. The headers and name of the individual images are appended
        together into an array.
        
        Parameters:
        other   The other instance of this class which is being divided from
                this instance.
        
        Returns:
        A new instance which is the division of this instance and the input instance.
        The new header will be a list containing the header of both individual
        instances while the actual data arrays will simply be summed element-wise.
        This method will make sure to only add instances together if they have
        the same conditions.
        """
        try:
            result = copy.deepcopy(self)    #Create a deep copy so as to not change this instance
            result.name.append(other.name[0])
            result.__header.append(other.__header[0])
            result.__prescan  /= other.__prescan
            result.__image    /= other.__image
            result.__original /= other.__original
            result.__postscan /= other.__postscan
            
            return result
        except ValueError:
            print('ValueError: Could not divide the images. Improper sizes')
            return
    
    def __sub__(self, other):
        """
        Name: __sub__
        
        Description:
        Subtracts the input instance from this instance. See documentation
        for __add__ for specifics.
        
        Parameters:
        other    The other instance of this class which is being subtracted
                 from this instance

        Returns:
        A new instance which is the distance of this instance and the input
        instance. See __add__ for more information.
        
        """
        try:
            result = copy.deepcopy(self)    #Create a deep copy so as to not change this instance
            result.name.append(other.name[0])
            result.__header.append(other.__header[0])
            result.__prescan  -= other.__prescan
            result.__image    -= other.__image
            result.__original -= other.__original
            result.__postscan -= other.__postscan
            
            return result
        except ValueError:
            print('ValueError: Could not subtract images. Improper sizes')
    
    def __str__(self):
        if self.numbImagesCombined == 1:
            str =  'SUMMARY FOR     ' + self.name + '\n' + \
                   'Obs Type:       ' + self.obsType + '\n' + \
                   'Filter:         ' + self.filter + '\n' + \
                   'RA/DEC:         ' + self.ra + '   ' + self.dec[i] + '\n' + \
                   'UTC Obs Time:   ' + self.date + '\n' + \
                   'Hour Angle:     ' + self.hourAngle + '\n' + \
                   'Exposure Time:  ' + str(self.expTime) + ' seconds\n' + \
                   'Airmass:        ' + str(self.airmass) + '\n' + \
                   'Image Size:     ' + str(self.width) + ' x ' + str(self.height[i]) + '\n' + \
                   'Plate Scale:    ' + str(self.plateScale) + ' arcsec/pix\n\n'
        else:
            str = 'This image is the combination of ' + str(self.numbImagesCombined) + ' images.\n\n'
            for i in range(self.numbImagesCombined):
                str += 'SUMMARY FOR     ' + self.name[i] + '\n' + \
                       'Obs Type:       ' + self.obsType[i] + '\n' + \
                       'Filter:         ' + self.filter[i] + '\n' + \
                       'RA/DEC:         ' + self.ra[i] + '   ' + self.dec[i] + '\n' + \
                       'UTC Obs Time:   ' + self.date[i] + '\n' + \
                       'Hour Angle:     ' + self.hourAngle[i] + '\n' + \
                       'Exposure Time:  ' + str(self.expTime[i]) + ' seconds\n' + \
                       'Airmass:        ' + str(self.airmass[i]) + '\n' + \
                       'Image Size:     ' + str(self.width[i]) + ' x ' + str(self.height[i]) + '\n' + \
                       'Plate Scale:    ' + str(self.plateScale[i]) + ' arcsec/pix\n\n'
    
    def __repr__(self):
        return self.__str__()
        
    ### Property Methods ###
    
    @property
    def airmass(self):
        if (self.numbImagesCombined == 1):
            return self.__header[0]['AIRMASS']
        elif (self.numbImagesCombined > 1):
            return [self.__header[i]['AIRMASS'] for i in range(self.numbImagesCombined)]
        
        raise(IndexError('No header files found'))
    
    @property
    def date(self):
        if (self.numbImagesCombined == 1):
            return self.__header[0]['DATE-OBS'].replace('T', '  ')
        elif (self.numbImagesCombined > 1):
            return [self.__header[i]['DATE-OBS'].replace('T', '  ') for i in range(self.numbImagesCombined)]
        
        raise(IndexError('No header files found'))
    
    @property
    def dec(self):
        if (self.numbImagesCombined == 1):
            return self.__header[0]['TELDEC']
        elif (self.numbImagesCombined > 1):
            return [self.__header[i]['TELDEC'] for i in range(self.numbImagesCombined)]
        
        raise(IndexError('No header files found'))
        
    @property
    def dim(self):
        return (self.width, self.height)
    
    @property
    def expTime(self):
        if (self.numbImagesCombined == 1):
            return self.__header[0]['EXPTIME']
        elif (self.numbImagesCombined > 1):
            return [self.__header[i]['EXPTIME'] for i in range(self.numbImagesCombined)]
        
        raise(IndexError('No header files found'))
    
    @property
    def filter(self):
        if (self.numbImagesCombined == 1):
            return self.__header[0]['FILTERS']
        elif (self.numbImagesCombined > 1):
            return [self.__header[i]['FILTERS'] for i in range(self.numbImagesCombined)]
        
        raise(IndexError('No header files found'))
    
    @property
    def gain(self):
        if (self.numbImagesCombined == 1):
            return self.__header[0]['GAIN']
        elif (self.numbImagesCombined > 1):
            return [self.__header[i]['GAIN'] for i in range(self.numbImagesCombined)]
        
        raise(IndexError('No header files found'))
    
    @property
    def height(self):
        return self.__header[0]['NAXIS2']
    
    @property
    def hourAngle(self):
        if (self.numbImagesCombined == 1):
            return self.__header[0]['HA']
        elif (self.numbImagesCombined > 1):
            return [self.__header[i]['HA'] for i in range(self.numbImagesCombined)]
        
        raise(IndexError('No header files found'))
    
    @property
    def image(self):
        return self.__image
    
    @property
    def numbImagesCombined(self):
        return len(self.__header)
    
    @property
    def plateScale(self):
        if (self.numbImagesCombined == 1):
            return self.__header[0]['SCALE']
        elif (self.numbImagesCombined > 1):
            return [self.__header[i]['SCALE'] for i in range(self.numbImagesCombined)]
        
        raise(IndexError('No header files found'))
    
    @property
    def obsType(self):
        if (self.numbImagesCombined == 1):
            return self.__header[0]['OBSTYPE']
        elif (self.numbImagesCombined > 1):
            return [self.__header[i]['OBSTYPE'] for i in range(self.numbImagesCombined)]
        
        raise(IndexError('No header files found'))
    
    @property
    def postscan(self):
        return self.__postscan
    
    @property
    def postscanPix(self):
        return self.__header[0]['POSTSCAN']
    
    @property
    def prescan(self):
        return self.__prescan
    
    @property
    def prescanPix(self):
        return self.__header[0]['PRESCAN']
    
    @property
    def ra(self):
        if (self.numbImagesCombined == 1):
            return self.__header[0]['TELRA']
        elif (self.numbImagesCombined > 1):
            return [self.__header[i]['TELRA'] for i in range(self.numbImagesCombined)]
        
        raise(IndexError('No header files found'))
    
    @property
    def width(self):
        return self.__header[0]['NAXIS1']-self.__header[0]['PRESCAN']-self.__header[0]['POSTSCAN']


###----------------------------------------------
#
# Name:     Bias
#
# Purpose:  This class extends from the DataEnc
#           class and is meant for specifically
#           creating Bias images. This class has
#           a static member which keeps track of
#           how many total bias images have been
#           created.
#
###----------------------------------------------

class Bias(DataEnc):
    
    __numbBias = 0
    
    ### Constructor ###
    
    def __init__(self, path, subtractOverscans = True, removeCosmicRays = True):
        super().__init__(path, subtractOverscans, removeCosmicRays)
        Bias.__numbBias += 1
    
    ### Destructor ###
    
    def __del__(self):
        Bias.__numbBias -= 1
    
    ### Utility Methods ###
    
    
    
    ### Static Methods ###
    
    @staticmethod
    def getNumbBias():
        return Bias.__numbBias
    
    ### Property Methods ###


###----------------------------------------------
#
# Name:     Flat
#
# Purpose:  This class extends from the DataEnc
#           class and is meant for specifically
#           creating Flat images. This class has
#           a static member which keeps track of
#           how many total flat images have been
#           created.
#
###----------------------------------------------

class Flat(DataEnc):
    
    __numbFlat = 0
    
    ### Constructor ###
    
    def __init__(self, path, subtractOverscans = True, removeCosmicRays = True):
        super().__init__(path, subtractOverscans, removeCosmicRays)
        Flat.__numbFlat += 1

        self.isBiasCorrected = False
    
    ### Destructor ###
    
    def __del__(self):
        Flat.__numbFlat -= 1
    
    ### Utility Methods ###
    
    def subtractBias(self, biasFrame):
        """
        Method to subtract the input bias image from
        this instance.
        """
        self -= biasFrame
        self._isBiasCorrected = True
    
    ### Static Methods ###
    
    @staticmethod
    def getNumbFlat():
        return Flat.__numbFlat
    
    ### Property Methods ###

    @property
    def isBiasCorrected(self):
        return self._isBiasCorrected
    

###----------------------------------------------
#
# Name:     Image
#
# Purpose:  This class extends from the DataEnc
#           class and is meant for specifically
#           creating actual images. This class has
#           a static member which keeps track of
#           how many total images have been
#           created. Within this class are specific
#           methods for processing and analyzing
#           the image.
#
###----------------------------------------------

class Image(DataEnc):
    
    __numbImages = 0
    
    ### Constructor ###
    
    def __init__(self, path, subtractOverscans = True, removeCosmicRays = True):
        super().__init__(path, subtractOverscans, removeCosmicRays)
        Image.__numbImages += 1

        self._isBiasCorrected = False
        self._isFlatCorrected = False
        
    
    ### Destructor ###
    
    def __del__(self):
        Image.__numbImages -= 1
    
    ### Utility Methods ###
    
    def subtractBias(self, biasFrame):
        """
        Method to subtract the input bias image from
        this instance.
        """
        self -= biasFrame
        self._isBiasCorrected = True
    
    def divideFlat(self, flatFrame):
        """
        Method to subtract the input flat image from
        this instance.
        """
        self /= flatFrame
        self._isFlatCorrected = True
    
    def findCentroid(self):
        """
        Gives the x,y coordinate position of the centroid
        of a chosen star.
        """
        pass
    
    def show(self, cmap = 'jet'):
        """
        Plots the image so it can be seen visually.

        Parameters
        cmap    The colormap used to plot the image. The default is 'jet' which
                is a rainbow color map. Other potential maps include 'Blues',
                'Reds', 'rainbow', 'gray', 'brg', or 'gist_rainbow'. For a full
                list of possible colormaps, see
                http://matplotlib.org/examples/color/colormaps_reference.html
        """
        plt.imshow(self.image, cmap = cmap)
        plt.show(block = False)
    
    ### Static Methods ###
    
    @staticmethod
    def getNumbImagesOpened():
        return Image.__numbImages
    
    ### Property Methods ###
    
    @property
    def isBiasCorrected(self):
        return self._isBiasCorrected

    @property
    def isFlatCorrected(self):
        return self._isFlatCorrected
