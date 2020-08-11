"""
Restore Levels

Restore the view dependant properties of the saved levels
Only single segment (i.e. non-split) levles are supported yet
Levle leaders are added as needed, but there is no API to restore them

Only saved levels will be restored. If there are preselected levels, 
  only they will be restored.
Handy to fine-tune separate parts of the drawing


TESTED REVIT API: 2020

@ejs-ejs
This script is part of PyRevitPlus: Extensions for PyRevit
github.com/ejs-ejs | @ejs-ejs

--------------------------------------------------------
RevitPythonWrapper: revitpythonwrapper.readthedocs.io
pyRevit: github.com/eirannejad/pyRevit

"""

import os
import pickle
from tempfile import gettempdir
from collections import namedtuple

import rpw
from rpw import doc, uidoc, DB, UI

Point = namedtuple('Point', ['X', 'Y','Z'])

tempfile = os.path.join(gettempdir(), 'LevelPlacement')

cView = doc.ActiveView
Axes = rpw.ui.Selection()


if not(cView.ViewType == DB.ViewType.Section or cView == DB.ViewType.Elevation):
    UI.TaskDialog.Show('pyRevitPlus', 'View type \'{}\' not supported'.format(cView.ViewType))
else:
    experimental = True
    UI.TaskDialog.Show('pyRevitPlus', 'Support for \'{}\' view type is experimental!'.format(cView.ViewType))

    if len(Axes) < 1:
        Axes = rpw.db.Collector(view=cView, of_class='Level').get_elements(wrapped=False)

    try:
        with open(tempfile, 'rb') as fp:
            GridLines = pickle.load(fp)
    except IOError:
        UI.TaskDialog.Show('pyRevitPlus', 'Could not find saved placementof the level.\nSave placement first.')

    n=0

    for cAxis in Axes:
            #axis = cAxis.unwrap()
            if not(isinstance(cAxis, DB.Level)):
                cAxis = cAxis.unwrap()
            
            if isinstance(cAxis, DB.Level):
               # UI.TaskDialog.Show('pyRevitPlus', 'Levle element \'{}\''.format(cAxis.Name))

                if cAxis.Name in GridLines:
                    #UI.TaskDialog.Show('pyRevitPlus', 'Found saved level element \'{}\''.format(cAxis.Name))
                    curves=cAxis.GetCurvesInView(DB.DatumExtentType.ViewSpecific, cView)
                    if len(curves) <> 1:
                        UI.TaskDialog.Show('pyRevitPlus', 'The level line is defind by {} curves, unable to proceed', len(curves))
                    else:
                        cCurve = curves[0]
                        cGridData = GridLines[cAxis.Name]

                        tmp = cCurve.GetEndPoint(0)
                        if abs(cView.ViewDirection.X) > abs(cView.ViewDirection.Y):
                            pt0 = DB.XYZ(tmp.X, cGridData['Start'].Y, tmp.Z)
                        else:
                            pt0 = DB.XYZ(cGridData['Start'].X, tmp.Y, tmp.Z)


                        tmp1 = cCurve.GetEndPoint(1)
                        if abs(cView.ViewDirection.X) > abs(cView.ViewDirection.Y):
                            pt1 = DB.XYZ(tmp.X, cGridData['End'].Y, tmp.Z)
                        else:
                            pt1 = DB.XYZ(cGridData['End'].X, tmp.Y, tmp.Z)
                        #pt1 = DB.XYZ(cGridData['End'].X, cGridData['End'].Y, tmp1.Z)
                        
                        #if isinstance(cCurve, DB.Arc):
                        #    #ptc = DB.XYZ(cGridData['Center'].X, cGridData['Center'].Y, tmp1.Z)
                        #    # take mid-point of the exixting curve as reference. Will cause trouble.
                        #    # should't, if the grid is not extremelly modified, eg, reversed
                        #    ptRef = cCurve.Evaluate(0.5, True) 
                        #    gridline = DB.Arc.Create(pt0, pt1, ptRef)
                        #else:
                        
                        
                        if DB.XYZ.DistanceTo(pt0, pt1) > 0.1:
                            
                            gridline = DB.Line.CreateBound(pt0, pt1)

                          #  UI.TaskDialog.Show('pyRevitPlus','Restoring endpoints of the level \'{}\''.format(cAxis.Name))
                            if cAxis.IsCurveValidInView(DB.DatumExtentType.ViewSpecific, cView, gridline):
                                with rpw.db.Transaction('Restoring view-dependant endpoints if the level \'{}\''.format(cAxis.Name)):
                                    cAxis.SetCurveInView(DB.DatumExtentType.ViewSpecific, cView, gridline)

                            #UI.TaskDialog.Show('pyRevitPlus','Restoring level \'{}\' placement'.format(cAxis.Name))

                            with rpw.db.Transaction('Restoring view-dependant placement of the level \'{}\''.format(cAxis.Name)):
                                if cGridData['StartBubble'] and cGridData['StartBubbleVisible']:
                                    cAxis.ShowBubbleInView(DB.DatumEnds.End0, cView)
                                    if 'Leader0Anchor' in cGridData:
                                        if not cAxis.GetLeader(DB.DatumEnds.End0, cView):
                                            cLeader = cAxis.AddLeader(DB.DatumEnds.End0, cView)
                                    #        cLeader = cAxis.GetLeader(DB.DatumEnds.End0, cView)
                                    #        cLeader.Anchor = DB.XYZ(cGridData['Leader0Anchor'].X, cGridData['Leader0Anchor'].Y, cGridData['Leader0Anchor'].Z)
                                    #        cLeader.Elbow = DB.XYZ(cGridData['Leader0Elbow'].X, cGridData['Leader0Elbow'].Y, cGridData['Leader0Elbow'].Z)
                                    #        cLeader.End = DB.XYZ(cGridData['Leader0End'].X, cGridData['Leader0End'].Y, cGridData['Leader0End'].Z)
                                            
                                        
                                else:
                                    cAxis.HideBubbleInView(DB.DatumEnds.End0, cView)

                                if cGridData['EndBubble'] and cGridData['EndBubbleVisible']:
                                    cAxis.ShowBubbleInView(DB.DatumEnds.End1, cView)
                                    if 'Leader1Anchor' in cGridData:
                                        if not cAxis.GetLeader(DB.DatumEnds.End1, cView):
                                            cLeader = cAxis.AddLeader(DB.DatumEnds.End1, cView)
                                    #        cLeader = cAxis.GetLeader(DB.DatumEnds.End1, cView)
                                    #        cLeader.Anchor = DB.XYZ(cGridData['Leader1Anchor'].X, cGridData['Leader1Anchor'].Y, cGridData['Leader1Anchor'].Z)
                                    #        cLeader.Elbow = DB.XYZ(cGridData['Leader1Elbow'].X, cGridData['Leader1Elbow'].Y, cGridData['Leader1Elbow'].Z)
                                    #        cLeader.End = DB.XYZ(cGridData['Leader1End'].X, cGridData['Leader1End'].Y, cGridData['Leader1End'].Z)
                                            
                                else:
                                    cAxis.HideBubbleInView(DB.DatumEnds.End1, cView)
                            n += 1
                        else:
                         UI.TaskDialog.Show('pyRevitPlus','Zero lenght segment for Level \'{}\'. \n Probably the level is saved in the perpendicular view. \nSkipping.'.format(cAxis.Name) )
    if n<>1:
        msg = 'Restored placement for {} levels'.format(n)
    else:
        msg = 'Restored placement of the level \'{}\''.format(cAxis.Name)
    UI.TaskDialog.Show('pyRevitPlus',msg)
