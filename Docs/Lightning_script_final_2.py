#Lightning plug-in project: creating a code that generates one procedural lightning at a time
#This program utilises the Space Colonization Algorithm, usually used to make trees, and adapts it to create bolts procedurally. Various attractors are placed in a determined space 
#and the origin of the bolt is created. The code then loops through the attractors and finds the closest lightning segment, wich will then be attracted. The bolt grows until all of the attractors 
#are reached and removed. The GUI allows the user to change the appearence, size, orientation, colour and brightness of the lightning. This code should be used to create a lightning 
#mesh that can then be exported into the users scene where its needed.
#
#Main reference: Runions, A., Lane, B., Prusinkiewicz, P. (2007) "Modelling Trees with a Space Colonization Algorithm". Canada: University of Calgary

import maya.cmds as cmds
import random
from maya.OpenMaya import MVector, MPoint

class Point: #this class is used to create the attractors
    def __init__(self, area):
        ''' Initialises the objects attributes
        
        self              : the instance of the class
        area              : the area in which to spawn the attractors, from the GUI
        On exit           : the attributes have been set
        '''
        self.pos = MPoint(random.uniform(-area,area), random.uniform(0,40), random.uniform(-area,area)) #the position of each point is randomly generated in an area decided by the user
        self.reached = False #the reached flag signals if a point has been reached by a segment   
        
class Line: #this class is used to create bolt segments
    def __init__(self, pos, father, dir):
        ''' Initialises the objects attributes
        
        pos               : the position in the 3D space of the segment
        father            : a reference to the previous segment
        dir               : the segments direction
        On exit           : the attributes have been set
        '''
        self.pos = pos
        self.father = father
        self.dir = dir
        self.count = 0 #used to average the direction
        self.originalDir = MVector(self.dir.x, self.dir.y, self.dir.z) #the original direction is stored
        self.length = 1 #the length of the segment
        self.shown = False #a flag to keep count of which segments have been shown
        self.frame = 0 #the frame at which each segment becomes visible
        
        '''Source: reference from The Coding Train''' 
    def resetFunc(self):
        '''  Resets the count and direction after the count is used to average the direction of a new segment
        
        On exit           : the count and direction have been reset                
        '''
        self.dir = MVector(self.originalDir.x, self.originalDir.y, self.originalDir.z)
        self.count = 0
                
    def next(self):
        ''' Creates the various segments, which are instances of the Line class
        
        return           : returns the created segment
        '''
        nextDir = (self.dir * self.length)
        nextPos = (self.pos + nextDir) #the position of the next segment is found by adding the direction vector
        nextSegm = Line(nextPos, self, MVector(self.dir.x, self.dir.y, self.dir.z)) #the Line class is used for a new instance
        return nextSegm 
        '''End of referenced code'''
               
    def showMesh(self, iter, cylinderNumber, newThickness, segmFalloff):
        ''' Shows a small cylinder for every lightning segment, except for the origin, and is also responsable for the animation
        
        iter             : the current number of iterations, used to set the correct frame
        cylinderNumber   : the number of each segment, assigned when the cylinder is renamed
        newThickness     : the initial radius of the lightning segments, from the GUI
        segmFalloff      : boolean that decides if the radius decreases as the lightning grows, from the GUI
        On exit          : the cylinders are placed and are animated being created
        '''
        if (self.father is not None): #this line makes sure the origin segment is not shown
            if (self.shown == False): #this line makes sure to only show the new segments created in the frame
                p1 = self.pos
                p2 = self.father.pos
                midpointX = (p1.x + p2.x)/2
                midpointY = (p1.y + p2.y)/2
                midpointZ = (p1.z + p2.z)/2 #these operations find the position of where to place the cylinder by keeping count of the parent
                radiusDecrease = iter*0.001 #based on the frame number, the radius decreases by a certain amount
                if (segmFalloff == False): #the radius decrease can also be turned off by the user: segmFalloff comes from the GUI
                    radiusDecrease=0
                radius = (0.1 - (radiusDecrease))
                if (radius <= 0): #Error checking: if the radius gets smaller than zero, it gets set to a positive value
                    radius = 0.0001
                cmds.polyCylinder(r=radius*newThickness, h=p1.distanceTo(p2), ax=[self.dir.x, self.dir.y, self.dir.z], sx=12) #the cylinder is created with a thickness multiplier from the GUI that controls the radius of the segments
                cmds.rename('segment_'+(str(cylinderNumber))) #each cylinder is renamed based on its number and then moved to its location
                cmds.move(midpointX, midpointY, midpointZ)
                
                self.frame = iter #this section creates the animation by manipulating the visibility attribute of the segments. Each segment has a frame attribute for when it will be made visible
                cmds.setKeyframe('segment_'+(str(cylinderNumber)), attribute='visibility', value=0, time=self.frame-1)
                cmds.setKeyframe('segment_'+(str(cylinderNumber)), attribute='visibility', value=1, time=self.frame)
                self.shown = True #the new segment is flagged as shown so that it won't be considered in the next iteration
                           
    def unshowMesh(self, minIter, cylinderNumber):
        '''  Hides the segments later in the animation, so that the sequence loops
        
        minIter          : the first frame at which the lightning starts disappearing
        cylinderNumber   : the number of each segment
        return           : returns the value of the frame, but only the last one is used
        '''
        if (self.father is not None):
            self.frame += minIter #the animation is practically reversed. The segments disappear with an offset of minIter from when they were initially made visible
            cmds.setKeyframe('segment_'+(str(cylinderNumber)), attribute='visibility', value=1, time=self.frame-1)
            cmds.setKeyframe('segment_'+(str(cylinderNumber)), attribute='visibility', value=0, time=self.frame)
            return(self.frame) #returning the frame is necessary so that the last one is used to set the end of the animation
                  
    def setMaterial(self, iter, cylinderNumber, colour, brightnessDivider, brFalloff, colFalloff, materialType='surfaceShader'):
        ''' Sets the colour and glow of each segment using nodes and surface shaders
            
        iter             : the current number of iterations, used to set colour and brightness decrease
        cylinderNumber   : the number of each segment
        colour           : the colour decided by the user, from the GUI
        brightnessDivider: the brightness value, from the GUI
        brFalloff        : boolean that decides if the brightness decreases as the lightning grows, from the GUI
        colFalloff       : boolean that decides if the colour value decreases as the lightning grows, from the GUI 
        materialType     : the type of shader used
        On exit          : for each segment a different surface shader is assigned         
        '''
        if (self.father is not None):
            colourChange = iter*0.003 #similarly to the radius, the colour and glow values decrease as the lightning grows
            brightnessChange = colourChange
            setName = cmds.sets(name='_MaterialGroup_', renderable=True, empty=True) #creates a new shading node
            shaderName = cmds.shadingNode(materialType, asShader=True)
            if (colFalloff == False): #the colour decrease can also be turned off by the user: colFalloff comes from the GUI 
                colourChange=0
            cmds.setAttr(shaderName+'.outColor', colour[0]-colourChange, colour[1]-colourChange, colour[2]-colourChange, type='double3') #changes the colour
            if (brightnessDivider == 0.0):  #if the brightness from the GUI is zero, then don't set the glow attribute
                cmds.surfaceShaderList(shaderName, add=setName)
                cmds.sets('segment_'+(str(cylinderNumber)), edit=True, forceElement=setName)
            else:
                brightnessValue = 75/brightnessDivider #brightnessDivider comes from the GUI: it can be used to increase and decrease the brightness
                percentage = brightnessValue/100
                glowSubtract = (colour[0]*percentage, colour[1]*percentage, colour[2]*percentage)
                glowColour = (colour[0]-glowSubtract[0], colour[1]-glowSubtract[1], colour[2]-glowSubtract[2])  #these operations calculate the glow by making the colour of the segments lighter
                if (brFalloff == False): #the brightness decrease can also be turned off by the user: brFalloff comes from the GUI
                    brightnessChange=0
                '''Source: reference from Xiaosong Yangs L-system code'''
                cmds.setAttr(shaderName+'.outGlowColor', glowColour[0]-brightnessChange, glowColour[1]-brightnessChange, glowColour[2]-brightnessChange, type='double3') #sets the glow attribute
                cmds.surfaceShaderList(shaderName, add=setName) #add to the list of surface shaders
                cmds.sets('segment_'+(str(cylinderNumber)), edit=True, forceElement=setName) #assign the material to the object
                '''End of referenced code'''
                          
class Bolt: #this class contains the main methods used to create the lightning
    def __init__(self, newAttrNumber, newArea, height):
        ''' Initialises the objects attributes
        
        newAttrNumber    : the number of attractors, from the GUI
        newArea          : the area in which to spawn the attractors, from the GUI
        height           : the y value of the origin, from the GUI
        On exit          : the attractors and origin segment are created and put in their list 
        '''
        self.attrList = []
        self.segmList = [] #the attractor and segment lists contain all the attractor and segment objects
        self.maxDist = 100
        self.minDist = 5 #these distances reppresent the area of influence of an attractor: the segments in between these distances are attracted to the points
        
        '''This part creates a certain number of attractors, which are instances of the Point class, and adds them in the attractors list. The number of attractors and the area 
           they are created in are decided by the user from the GUI'''        
        for i in range (newAttrNumber):
            attr = Point(newArea)
            self.attrList.append(attr)
      
        '''This part determines the position and direction of the origin segment and adds it to the segments list. The height of the origin is decided by the user from the GUI'''            
        p = MPoint(0,height+40,0)
        d = MVector(0,-1,0)
        origin = Line(p, None, d) #the origin is an instance of the Line class with no father
        self.segmList.append(origin)
                           
    def grow(self, newThickness, newSize, newRotation, newColour, newBrightness, brFalloff, colFalloff, newSegmFalloff, newAnimationContr):
        ''' The heart of the program. It loops through the attractors and segments and determines which ones are to be attracted: in other words, the ones between the minimum and maximum distance(the attractors influence)
        
        newThickness     : the initial radius of the lightning segments, from the GUI
        newSize          : the value for which the lightning should be scaled, from the GUI
        newRotation      : the value for which the lightning should be rotated, from the GUI
        newColour        : the colour decided by the user, from the GUI
        newBrightness    : the brightness value, from the GUI
        brFalloff        : boolean that decides if the brightness decreases as the lightning grows, from the GUI
        colFalloff       : boolean that decides if the colour value decreases as the lightning grows, from the GUI
        newSegmFalloff   : boolean that decides if the radius decreases as the lightning grows, from the GUI
        newAnimationContr: boolean that decides if the animation should play when the lightning is created, from the GUI 
        On exit          : once this function has finished looping the lightning is created    
        '''
        iterations = 0
        while (len(self.attrList) is not 0): #the loop stops only when all of the attractors are reached
            iterations += 1 #multiple segments can be created for each iteration of the loop: this line keeps track of that value so it can be used later to create the frames of animation  
            '''Source: reference from The Coding Train'''
            for i in range(len(self.attrList)): #the code loops through all of the attractors and finds the closest segment, unlike the L-system which works from the segments
                currentAttr = self.attrList[i]
                closestSegm = None
                record = 100000
                for j in range(len(self.segmList)): #to find the closest segment, the code loops through all of the segments and calculates the distance from the current attractor
                    currentSegm = self.segmList[j]
                    d = currentAttr.pos.distanceTo(currentSegm.pos)
                    if (d < self.minDist): #if the distance is less than minDist the attractor will get flagged as reached
                        currentAttr.reached = True 
                        closestSegm = None
                        break
                    elif (d > self.maxDist): #if the distance is bigger than maxDistance nothing happens
                        something = 1     
                    elif (closestSegm == None or d < record): #record keeps track of which segment is the closest
                        closestSegm = currentSegm
                        record = d
                if (closestSegm != None): #when the closest segment is found at the end of the inner loop, this section plays out
                    newDir = (currentAttr.pos - closestSegm.pos) #the new direction is towards the current attractor
                    newDir.normalize() #the direction gets normalized
                    closestSegm.dir += newDir 
                    closestSegm.count = closestSegm.count + 1 #the new direction is added and count increases: it will be used later to average the directions
                    '''End of referenced code'''
            '''This part removes the reached attractors from the attractors list'''
            i = len(self.attrList) - 1 #removing objects from the back of an array is generally safer
            while i >= 0:
                if(self.attrList[i].reached):
                    attrToRemove = self.attrList[i]
                    self.attrList.remove(attrToRemove)
                i -= 1
                
            '''This part averages the directions of a segment to the attractors, and also adds an extra random 
               factor to make it resemble a bolt more
               Source: reference from The Coding Train'''
            i = len(self.segmList) - 1
            while i >= 0:
                currentSegm = self.segmList[i]
                if (currentSegm.count > 0): #if the segment has at least one attractor its attracted to, continue with code
                    currentSegm.dir /= currentSegm.count #one segment can be attracted to several attractors: this line avareges all of the found directions 
                    rand = MVector(random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5), random.uniform(-0.5, 0.5))
                    currentSegm.dir += rand #a random factor is added to make it look more jaggered
                    currentSegm.dir.normalize()
                    self.segmList.append(currentSegm.next()) #the next() function is called: the newly calculated segment will become an instance of the Line class and be added to the segment list
                    currentSegm.resetFunc() #the resetFunc() is called: the direction and count will be reset
                i -= 1
                '''End of referenced code'''
                
            '''This loop calls the showMesh function for every segment'''          
            for i in range (len(self.segmList)):
                self.segmList[i].showMesh(iterations, i, newThickness, newSegmFalloff) #the showMesh function creates the mesh and the first half of the animation
        
        '''This loop calls the setMaterial and unshowMesh for every segment'''        
        minIterations = iterations+20 #minIterations is the first frame of the second half of the animation
        for i in range (len(self.segmList)):
            self.segmList[i].setMaterial(self.segmList[i].frame, i, newColour, newBrightness, brFalloff, colFalloff) #the setMaterial function assigns colour and brightness to the segments
            endFrame=self.segmList[i].unshowMesh(minIterations, i) #the unshowMesh function creates the second half of the animation, where the lightning disappears
        
        '''This part groups all the segments together'''
        for i in range(len(self.segmList)): 
            if (self.segmList[i].father is not None):          
                cmds.select("segment_"+str(i), add=True) #Error checking: this part is coded in a way as to not include other objects in the scene wich should not be added to the group
        cmds.group(name='Lightning')
        
        '''This section rotates and scales the fineshed Lightning mesh based on imput from the GUI'''
        cmds.select('Lightning')
        cmds.rotate(0, 0, -newRotation, p=(0,25,0))
        cmds.scale(newSize, newSize, newSize, p=(0,25,0)) 
        cmds.select(deselect=True)
        
        '''This part sets the length of the animation and plays the animation'''
        cmds.playbackOptions(minTime=0, maxTime=endFrame+15) #the endFrame is the last frame in wich a segment disappeared
        cmds.play()
        if(newAnimationContr == False): #if the 'Play animation' checkbox in the GUI is not checked, don't play the animation on creation
            cmds.play(state=False)


def actionProc(winID, attractorsNumber, thicknessControl, heightControl, areaControl, rotationControl, scalingControl, segmSizeFalloff, brightnessControl, colourControl, brightnessFalloff, colourFalloff, animationControl, *pArgs):
    ''' Assignes the values retrieved from the GUI to new variables, deletes the previous iteration of the lightning and calls the main methods
    
    imput           : all of the values retrieved from the GUI
    On exit         : all of the values retrieved from the GUI are assigned to variables
    '''
    newAttrNumber = cmds.intSliderGrp(attractorsNumber, query=True, value=True) #the number of initial attractors in the scene
    newThickness = cmds.floatSliderGrp(thicknessControl, query=True, value=True) #the radius of the lightning segments
    newHeight = cmds.floatSliderGrp(heightControl, query=True, value=True) #the height at which the origin segment is placed
    newArea = cmds.intSliderGrp(areaControl, query=True, value=True) #the area in which the attractors are placed
    newRotation = cmds.intSliderGrp(rotationControl, query=True, value=True) #the value for which the lightning should be rotated
    newSize = cmds.floatSliderGrp(scalingControl, query=True, value=True) #the value for which the lightning should be scaled
    newSegmFalloff = cmds.checkBoxGrp(segmSizeFalloff, query=True, value1=True) #a boolean that establishes if the radius decreases as the lightning grows
    newBrightness = cmds.floatSliderGrp(brightnessControl, query=True, value=True) #the value of the lightnings brightness
    newColour = cmds.colorSliderGrp(colourControl, query=True, rgbValue=True) #the lightnings colour
    newBrFalloff = cmds.checkBoxGrp(brightnessFalloff, query=True, value1=True) #a boolean that establishes if the brightness decreases as the lightning grows
    newColFalloff = cmds.checkBoxGrp(colourFalloff, query=True, value1=True) #a boolean that establishes if the colour gets darker as the lightning grows  
    newAnimationContr = cmds.checkBoxGrp(animationControl, query=True, value1=True) #a boolean that establishes if the animation should get played upon the creation of the segment    
    
    '''This section deletes the previous iteration of the lightning if it exists'''
    if cmds.objExists('Lightning'):
        cmds.delete('Lightning') #the name of the group should not be changed manually, as doing so will create segments with the same name
        
    '''This section creates the only instance of the bolt class and calls the grow function. All of the variables are values retrieved from the GUI'''    
    lightning = Bolt(newAttrNumber, newArea, newHeight)
    lightning.grow(newThickness, newSize, newRotation, newColour, newBrightness, newBrFalloff, newColFalloff, newSegmFalloff, newAnimationContr)
    
def cancelProc(winID,*pArgs):
    ''' Deletes the GUI if the 'Cancel' button is pressed
    '''
    cmds.deleteUI(winID)
    
def renderFunc(winID, *pArgs):
    ''' Renders the current frame if the 'Render frame in current path' button is pressed. Maya software should be used for rendering
    '''
    cmds.render()
 
def batchRenderFunc(winID, *pArgs):
    ''' Batch renders the animation if the 'Batch render in current path' button is pressed. Maya software should be used for rendering
    '''
    lastFrame= cmds.playbackOptions(q=True, max=True)
    lastFrameInt= int(lastFrame)
    for i in range(lastFrameInt+1): #this part loops through the frames and renders them until the last frame is reached
        cmds.currentTime(i)
        cmds.render()
            
def createUI():
    ''' Prompts the user with values that will change the appearance of the lightning mesh
    
    On exit          : the GUI is created
    '''
    winID="LightningPlugin"
    if cmds.window(winID,exists=True): #if the window already exists it deletes it
        cmds.deleteUI(winID)    
    
    winID = cmds.window(winID, title="LightningPlugin", resizeToFitChildren=True, sizeable=False)
    cmds.columnLayout(adjustableColumn=True) #the setup for the window
    
    imgFileName = "H:\PYTHON\lightningProjectFINAL2\Docs\Lightning_GUI2.tif" #this image path should be changed by the user if it cannot be found
    if cmds.file(imgFileName, query=True, exists=True):
        cmds.image(image=imgFileName, width=500, height=200)
    else:
        print("Picture doesn't exist or path is not correct") #Error checking: if the path is wrong, this message gets printed
    
    '''These following sections contains the information on how the GUI will function and look, together with the various parametres that can be changed by the user'''      
    cmds.frameLayout(borderVisible=True, label="Control Parametres") #subsection for the appearence
    attractorsNumber = cmds.intSliderGrp(label="Lightning concentration", minValue=10, maxValue=200, value=40, step=1, field=True) #slider for the number of attractors
    thicknessControl = cmds.floatSliderGrp(label="Segment thickness", minValue=1, maxValue=5, value=1, step=0.01, field=True) #slider for the radius value
    heightControl = cmds.floatSliderGrp(label='Starting height', minValue=1, maxValue=20, value=10, step=0.1, field=True) #slider for the initial height value
    areaControl = cmds.intSliderGrp(label="Area size", minValue=5, maxValue=50, value=7, step=1, field=True) #slider for the size of the area
    rotationControl = cmds.intSliderGrp(label="Rotation angle", minValue=0, maxValue=360, value=315, field=True) #slider for the rotation value
    scalingControl = cmds.floatSliderGrp(label="Scaling value", minValue=0.1, maxValue=10, value=1, step=0.01, field=True) #slider for the scale value
    segmSizeFalloff = cmds.checkBoxGrp(label="Segment size falloff", value1=True) #checkbox for the radius getting smaller as the lightning grows
    cmds.setParent("..")
    
    cmds.frameLayout(borderVisible=True, label="Shader") #subsection for the material
    brightnessControl = cmds.floatSliderGrp(label="Brightness", minValue=0.0, maxValue=10, value=1, step=0.01, field=True) #slider for the brightness value
    colourControl = cmds.colorSliderGrp(label="Colour", rgb=[0.550, 0.550, 1]) #slider for the colour value
    brightnessFalloff = cmds.checkBoxGrp(label="Brightness falloff", value1=True) #checkbox for the brighness decreasing as the lightning grows   
    colourFalloff = cmds.checkBoxGrp(label="Colour falloff", value1=True) #checkbox for the colour decreasing as the lightning grows 
    cmds.setParent("..")
    
    cmds.frameLayout(borderVisible=True, label="Rendering") #subsection for rendering 
    cmds.button(label = 'Render frame in current path', command = lambda *args: renderFunc(winID)) #button to render the current frame
    cmds.button(label = 'Batch render in current path', command = lambda *args: batchRenderFunc(winID)) #button to batch render
    animationControl = cmds.checkBoxGrp(label="Play animation", value1=True) #checkbox to play the animation upon creation of the lightning
    cmds.setParent("..")
    
    '''Source: reference from Xiaosong Yang'''
    cmds.frameLayout(borderVisible=True, labelVisible=False, h=35)
    cmds.rowLayout(numberOfColumns=2, columnWidth2=[250,250], columnAttach=[(1, "both", 10),(2, "both", 10)])
    #the apply button calls the actionProc() function, thus starting the algorithm
    cmds.button(label = "Apply", command = lambda *args: actionProc(winID, attractorsNumber, thicknessControl, heightControl, areaControl, rotationControl, scalingControl, segmSizeFalloff, brightnessControl, colourControl, brightnessFalloff, colourFalloff, animationControl))
    cmds.button(label = "Cancel", command = lambda *args: cancelProc(winID)) #the cancel button calls the cancelProc() function, thus deleting the window
    cmds.setParent("..")
    '''End of referenced code'''
    
    cmds.showWindow(winID)
    
if __name__== "__main__":
    createUI()