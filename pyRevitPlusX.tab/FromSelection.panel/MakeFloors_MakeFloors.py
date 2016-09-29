"""
Make Floors
Create Floors from Selected Rooms
TESTED REVIT API: 2015

Gui Talarico
github.com/gtalarico

"""

__doc__ = 'Makes Floor objects from selected rooms.'
__author__ = '@gtalarico'

import sys
import os
import logging
from functools import wraps
from collections import namedtuple

from Autodesk.Revit.UI import TaskDialog
from Autodesk.Revit.DB import Element, XYZ, CurveArray
from Autodesk.Revit.DB import Transaction
from Autodesk.Revit.DB import FilteredElementCollector, BuiltInCategory
from Autodesk.Revit.DB import SpatialElementBoundaryOptions, Options
from Autodesk.Revit.DB.Architecture import Room

sys.path.append(os.path.dirname(__file__))
from winforms import SelectViewTypeForm, DialogResult
# from .winforms import SelectViewTypeForm

doc = __revit__.ActiveUIDocument.Document
uidoc = __revit__.ActiveUIDocument

VERBOSE = True  # True to Keep Window Open
VERBOSE = False

LOG_LEVEL = logging.ERROR
LOG_LEVEL = logging.INFO
if VERBOSE:
    LOG_LEVEL = logging.DEBUG
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger('MakePlan')


def get_selected_elements():
    """ Add Doc """
    selection = uidoc.Selection
    selection_ids = selection.GetElementIds()
    selection_size = selection_ids.Count
    logger.debug('selection_size: {}'.format(selection_size))
    # selection = uidoc.Selection.Elements  # Revit 2015
    if not selection_ids:
        TaskDialog.Show('MakeFloors', 'No Elements Selected.')
        # logger.error('No Elements Selected')
        __window__.Close()
        sys.exit(0)
    elements = []
    for element_id in selection_ids:
        elements.append(doc.GetElement(element_id))
    return elements


def revit_transaction(transaction_name):
    def wrap(f):
        @wraps(f)
        def wrapped_f(*args, **kwargs):
            try:
                t = Transaction(doc, transaction_name)
                t.Start()
            except InvalidOperationException as errmsg:
                print('Transaciton Error: {}'.format(errmsg))
                return_value = f(*args, **kwargs)
            else:
                return_value = f(*args, **kwargs)
                t.Commit()
            return return_value
        return wrapped_f
    return wrap


def get_floor_types():
    types = {} # {'name':'id'}
    floor_types = FilteredElementCollector(doc).OfCategory(
                                                BuiltInCategory.OST_Floors
                                                ).WhereElementIsElementType()
    for floor_type in floor_types:
        types[Element.Name.GetValue(floor_type)] = floor_type.Id
    return types


@revit_transaction('Create Floor')
def make_floor(new_floor):
    floor_curves = CurveArray()
    for boundary_segment in new_floor.boundary:
        floor_curves.Append(boundary_segment.Curve)

    floorType = doc.GetElement(new_floor.type_id)
    level = doc.GetElement(new_floor.level_id)
    normal = XYZ.BasisZ
    doc.Create.NewFloor( floor_curves,
                         floorType, level, False, normal );


elements = get_selected_elements()
floor_types = get_floor_types()
#
form = SelectViewTypeForm(floor_types.keys())
form.ShowDialog()

if form.DialogResult == DialogResult.OK:
    chosen_type_name = form.selected

type_id = floor_types[chosen_type_name]

NewFloor = namedtuple('NewFloor', ['type_id', 'boundary', 'level_id'])
new_floors = []
room_boundary_options = SpatialElementBoundaryOptions()

for element in elements:
    if isinstance(element, Room):
        room = element
        room_level_id = room.Level.Id
        # List of Boundary Segment comes in an array by itself.
        room_boundary = room.GetBoundarySegments(room_boundary_options)[0]
        new_floor = NewFloor(type_id=type_id, boundary=room_boundary,
                             level_id=room_level_id)
        new_floors.append(new_floor)

if not new_floors:
    TaskDialog.Show('MakeFloors', 'You need to select at least one room.')
    __window__.Close()
    sys.exit(0)

for new_floor in new_floors:
    view = make_floor(new_floor)
