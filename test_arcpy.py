import arcpy
print("ArcPy version :", arcpy.GetInstallInfo()["Version"])
print("Spatial Analyst :", arcpy.CheckExtension("Spatial"))