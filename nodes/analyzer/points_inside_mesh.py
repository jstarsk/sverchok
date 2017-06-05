# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
import bmesh
from mathutils.kdtree import KDTree
from mathutils import Vector

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata


def are_inside(points, bm):
    rpoints = []
    addp = rpoints.append

    if len(bm.verts) <= 8:
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], smooth=False)

    size = len(bm.verts)
    kd = KDTree(size)
    for i, xyz in enumerate(bm.verts):
        kd.insert(xyz.co[:], i)
    kd.balance()
    
    # bm.verts.ensure_lookup_table()
    
    verts = bm.verts
    for p in points:
        co, index, _ = kd.find(p)
        normal = verts[index].normal
        p2 = co - Vector(p)
        v = p2.dot(normal)
        addp(not v < 0.0)  # addp(v >= 0.0) ?

    return rpoints



class SvPointInside(bpy.types.Node, SverchCustomTreeNode):
    ''' pin get points inside mesh '''
    bl_idname = 'SvPointInside'
    bl_label = 'Points Inside Mesh'

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'verts')
        self.inputs.new('VerticesSocket', 'faces')
        self.inputs.new('VerticesSocket', 'verts')
        self.outputs.new('StringsSocket', 'mask')
        self.outputs.new('VerticesSocket', 'verts')

    def process(self):

        # no vectorization yet

        verts_in, faces_in, points = [s.sv_get() for s in self.inputs]
        
        mask = []
        for idx, (verts, faces, pts_in) in enumerate(zip(verts_in, faces_in, points)):
            bm = bmesh_from_pydata(verts, [], faces, normal_update=True)
            mask.append(are_inside(pts_in, bm))

        self.outputs['mask'].sv_set(mask)
        if self.outputs['verts'].is_linked:
            out_verts = []
            for masked, pts_in in zip(mask, points):
                out_verts.append([p for m, p in zip(masked, pts_in) if m])


def register():
    bpy.utils.register_class(SvPointInside)


def unregister():
    bpy.utils.unregister_class(SvPointInside)
