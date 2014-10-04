blender-woodworking
===================

Blender extensions for woodworking

All operators are available in 3D view area, Tool Shelf panel ('T'), in the category tab "woodworking".

# How to install

## Beginners
In this repository, select and download the zip file containing all needed python files for the blender extension (press the "raw" button).
In blender, choose "File" menu then select the "User preferences..." item.
Choose the "Addons" tab in the dialog window, then press "Install from file..." button.
Select the zip file you just downloaded and check the checkbox to activate it.

## Advanced users
To get the latest available sources, clone the git repository or download all python files in the woodwork folder.

# Joints

## Tenon

![Sample rendered tenon](/screenshots/sample_tenon.png)

### Description
This operator will generate a new tenon on the selected quad face in edit mode.

### Requirements
Object should be in edit mode, a **quad** face should be selected and it must be planar and _rectangular_.

### Usage

![Tenon panel](/screenshots/tenon_panel.blend.png)

The tenon panel is organized in three parts :

1. Width side

  On this box, you set tenon **thickness** and position along _width axis_.

  In the thickness type box, you choose the way you want to give _tenon thickness value_:
  * By value
  * By percentage (of width size length)
  * Max value (size of width size)

  You can control tenon position on width size by either checking/unchecking the _centered_ button.
  If unchecked, you gain access to several more options to control _shoulder_ on width side :
  * _Shoulder size_ (using the type, you specify size in value or percentage)
  * _Reverse shoulder_ checkbox if you want to give the shoulder size for the other side 

2. Length side

  ![Detail for length side](/screenshots/tenon_panel_height_details.blend.png)

  On this box, you set tenon **height** and position along _length axis_.

  The same parameters as the width side are all available to control height and position.

  Another parameter is available to add strength and rigidity to the tenon : the **haunched** checkbox.
  Using it, you could make an haunched join, specifying the height in value or percentage of tenon depth.

3. Depth

  Sets the tenon depth value.

## Mortise

![Sample rendered mortise](/screenshots/sample_mortise.png)

### Description
This operator will generate a new mortise on the selected quad face in edit mode.
Haunched mortise make holes in adjacent faces.
![Haunched mortise](/screenshots/sample_mortise_with_haunch.png)

### Requirements
Object should be in edit mode, a **quad** face should be selected and it must be planar and _rectangular_.

### Usage

The mortise panel is organized as the tenon panel, in three parts. Check tenon panel usage for more information.

# Units
In blender, you can change the default "blender unit" to **metric units** in the scene properties. 

# Translation
This extension is available in French : to use it, just make sure to change Blender language in "User Preferences..."
