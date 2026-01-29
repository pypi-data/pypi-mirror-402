def getdtapath():
      """ path of Ptsdata"""
      import os
      import sys
      import PythonTsa 
      dtapath=os.path.dirname(PythonTsa.__file__)
      try:
          newdtapath=dtapath+'/Ptsadata/'
      except:
          print('Sorry, your platform should be Windows, Mac or Linux !')
            
      return newdtapath
