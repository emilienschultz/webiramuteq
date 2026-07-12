# -*- coding: utf-8 -*-
"""
Blender script. Draws a node-and-edge network in blender, randomly distributed
spherically.

14 Sept 2011: Added collision detection between nodes

30 Nov 2012: Rewrote. Switched to JSON, and large Blender speed boosts.

Written by Patrick Fuller, patrickfuller@gmail.com, 11 Sept 11

modifications by Pierre Ratinaud Feb 2014
"""
#------------------------------------
# import des modules python
#------------------------------------
import bpy
from math import acos, degrees, pi
from mathutils import Vector
from copy import copy

import json
from random import choice
import sys


# Colors to turn into materials
#colors = {"purple": (178, 132, 234), "gray": (11, 11, 11),
#          "green": (114, 195, 0), "red": (255, 0, 75),
#          "blue": (0, 131, 255), "clear": (0, 131, 255),
#          "yellow": (255, 187, 0), "light_gray": (118, 118, 118)}


# Normalize to [0,1] and make blender materials
def make_colors(colors):
    for key, value in list(colors.items()):
        value = [x / 255.0 for x in value]
        bpy.data.materials.new(name=key)
        bpy.data.materials[key].diffuse_color = value
        bpy.data.materials[key].specular_intensity = 0.5
        # Don't specify more parameters if these colors
        if key == "gray" or key == "light_gray":
            bpy.data.materials[key].use_transparency = True
            bpy.data.materials[key].transparency_method = "Z_TRANSPARENCY"
            bpy.data.materials[key].alpha = 0.2
        # Transparency parameters
        else :
            bpy.data.materials[key].use_transparency = True
            bpy.data.materials[key].transparency_method = "Z_TRANSPARENCY"
            bpy.data.materials[key].alpha = 0.6 if key == "clear" else 0.8
            bpy.data.materials.new(name = key + 'sphere')
            bpy.data.materials[key + 'sphere'].diffuse_color = value
            bpy.data.materials[key + 'sphere'].specular_intensity = 0.1
            bpy.data.materials[key + 'sphere'].use_transparency = True
            bpy.data.materials[key + 'sphere'].transparency_method = "Z_TRANSPARENCY"
            bpy.data.materials[key + 'sphere'].alpha = 0.1
        #bpy.data.materials[key].raytrace_transparency.fresnel = 0.1
        #bpy.data.materials[key].raytrace_transparency.ior = 1.15

def draw_network(network, edge_thickness=0.25, node_size=3, directed=False, spheres = True):
    """ Takes assembled network/molecule data and draws to blender """
    colors = [tuple(network["nodes"][node]['color']) for node in network["nodes"]]
    cols = list(set(colors))
    colors = dict(list(zip([str(col) for col in cols],cols)))
    colors.update({"light_gray": (118, 118, 118), "gray": (11, 11, 11)})
    make_colors(colors)
    # Add some mesh primitives
    bpy.ops.object.select_all(action='DESELECT')
    #bpy.ops.mesh.primitive_uv_sphere_add()
    bpy.ops.mesh.primitive_uv_sphere_add(segments = 64, ring_count = 32)
    sphere = bpy.context.object
    bpy.ops.mesh.primitive_cylinder_add()
    cylinder = bpy.context.object
    cylinder.active_material = bpy.data.materials["light_gray"]
    bpy.ops.mesh.primitive_cone_add()
    cone = bpy.context.object
    cone.active_material = bpy.data.materials["light_gray"]
    #bpy.ops.object.text_add(view_align=True)
    # Keep references to all nodes and edges
    shapes = []
    # Keep separate references to shapes to be smoothed
    shapes_to_smooth = []
    #val to div coordonnate
    divval = 0.05
    # Draw nodes
    for key, node in list(network["nodes"].items()):
        # Coloring rule for nodes. Edit this to suit your needs!
        col = str(tuple(node.get("color", choice(list(colors.keys())))))
        # Copy mesh primitive and edit to make node
        # (You can change the shape of drawn nodes here)
        if spheres :
            node_sphere = sphere.copy()
            node_sphere.data = sphere.data.copy()
            node_sphere.location = [val/divval for val in node["location"]]
            #node_sphere.dimensions = [node_size] * 3
            node_sphere.dimensions = [node["weight"]] * 3
            #newmat = bpy.data.materials[col]
            #newmat.alpha = 0.01
            node_sphere.active_material = bpy.data.materials[col + 'sphere']
            bpy.context.scene.objects.link(node_sphere)
            shapes.append(node_sphere)
            shapes_to_smooth.append(node_sphere)
        #node_text = text.copy()
        #node_text.data = text.data.copy()
        #node_text.location = node["location"]
        bpy.ops.object.text_add(view_align=False, location = [val/divval for val in node["location"]])
        #bpy.ops.object.text_add(view_align=False, location = [val for val in node["location"]])
        bpy.ops.object.editmode_toggle()
        bpy.ops.font.delete()
        bpy.ops.font.text_insert(text=key)
        bpy.ops.object.editmode_toggle()
        bpy.data.curves[bpy.context.active_object.name].size = node["weight"]/2
        bpy.data.curves[bpy.context.active_object.name].bevel_depth = 0.044
        bpy.data.curves[bpy.context.active_object.name].offset = 0
        bpy.data.curves[bpy.context.active_object.name].extrude = 0.2
        bpy.data.curves[bpy.context.active_object.name].align = "CENTER"
        bpy.context.active_object.rotation_euler = [1.5708,0,1.5708]
        bpy.context.active_object.active_material = bpy.data.materials[col]
        #bpy.ops.object.mode_set(mode='OBJECT')
        #Extrude the text
        #bpy.context.object.data.extrude = 0.03
        #Convert text to mesh
        #bpy.context.active_object.convert(target='MESH', keep_original=False)
        const = bpy.context.active_object.constraints.new(type='TRACK_TO')
        const.target = bpy.data.objects['Camera']
        const.track_axis = "TRACK_Z"
        const.up_axis = "UP_Y"
        #bpy.context.scene.objects.link(bpy.context.active_object)
        #shapes.append(bpy.context.active_object)
        #sha* 2 + [mag - node_size]
        shapes_to_smooth.append(bpy.context.active_object)        
    # Draw edges
    for edge in network["edges"]:
        # Get source and target locations by drilling down into data structure
        source_loc = network["nodes"][edge["source"]]["location"]
        source_loc = [val/divval for val in source_loc]
        target_loc = network["nodes"][edge["target"]]["location"]
        target_loc = [val / divval for val in target_loc]
        diff = [c2 - c1 for c2, c1 in zip(source_loc, target_loc)]
        cent = [(c2 + c1) / 2 for c2, c1 in zip(source_loc, target_loc)]
        mag = sum([(c2 - c1) ** 2
                  for c1, c2 in zip(source_loc, target_loc)]) ** 0.5
        # Euler rotation calculation
        v_axis = Vector(diff).normalized()
        v_obj = Vector((0, 0, 1))
        v_rot = v_obj.cross(v_axis)
        angle = acos(v_obj.dot(v_axis))
        # Copy mesh primitive to create edge
        edge_cylinder = cylinder.copy()
        edge_cylinder.data = cylinder.data.copy()
        edge_cylinder.dimensions = [float(edge['weight'])/10] * 2 + [mag - node_size]
        #edge_cylinder.dimensions = [edge_thickness] * 2 + [mag - node_size]
        edge_cylinder.location = cent
        edge_cylinder.rotation_mode = "AXIS_ANGLE"
        edge_cylinder.rotation_axis_angle = [angle] + list(v_rot)
        bpy.context.scene.objects.link(edge_cylinder)
        shapes.append(edge_cylinder)
        shapes_to_smooth.append(edge_cylinder)
        # Copy another mesh primitive to make an arrow head
        if directed:
            arrow_cone = cone.copy()
            arrow_cone.data = cone.data.copy()
            arrow_cone.dimensions = [edge_thickness * 4.0] * 3
            arrow_cone.location = cent
            arrow_cone.rotation_mode = "AXIS_ANGLE"
            arrow_cone.rotation_axis_angle = [angle + pi] + list(v_rot)
            bpy.context.scene.objects.link(arrow_cone)
            shapes.append(arrow_cone)
    # Remove primitive meshes
    bpy.ops.object.select_all(action='DESELECT')
    sphere.select = True
    cylinder.select = True
    cone.select = True
    #text.select = True
    # If the starting cube is there, remove it
    if "Cube" in list(bpy.data.objects.keys()):
        bpy.data.objects.get("Cube").select = True
    bpy.ops.object.delete()
    # Smooth specified shapes
    for shape in shapes_to_smooth:
        shape.select = True
    #bpy.context.scene.objects.active = shapes_to_smooth[0]
    #bpy.ops.object.shade_smooth()
    # Join shapes
    for shape in shapes:
        shape.select = True
    #bpy.context.scene.objects.active = shapes[0]
    #bpy.ops.object.join()
    # Center object origin to geometry
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="MEDIAN")
    # Refresh scene
    bpy.context.scene.update()

# If main, load json and run
if __name__ == "__main__":
    with open(sys.argv[3]) as network_file:
        network = json.load(network_file)
    draw_network(network)
