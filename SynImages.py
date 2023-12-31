import typing
import bpy
from bpy.types import Context
import numpy as np
import mathutils
import os


#-------------------------------------------------------------------------#

# Painel principal
class VIEW3D_PT_synthetic_image_generator(bpy.types.Panel):
    bl_label = 'Synthetic Image Generator'
    bl_idname = 'VIEW3D_PT_synthetic_image_generator'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Image Generator'
 
    def draw(self, context):
        layout = self.layout
        object = context.object
        scene = context.scene
       
        box1 = layout.box()

        icon = 'TRIA_DOWN' if scene.auto_exec else 'TRIA_RIGHT'
        row1 = box1.row()
        row1.prop(scene, "auto_exec", text="Generate from Directory", icon=icon, emboss=False)

        if scene.auto_exec:

            row = box1.row()
            row.label(text="Files Path", icon='FOLDER_REDIRECT')
            row = box1.row()
            row.prop(context.scene, "import_dir")

            row = box1.row()
        
        box2 = layout.box()

        icon = 'TRIA_DOWN' if scene.manual_exec else 'TRIA_RIGHT'
        row2 = box2.row()
        row2.prop(scene, "manual_exec", text="Generate from File", icon=icon, emboss=False)

        if scene.manual_exec:

            row = box2.row()
            row.label(text="File Path", icon='FOLDER_REDIRECT')
            row = box2.row()
            row.prop(context.scene, "file_dir")
            
            row = box2.row()
            row.operator("opr.import_object")

            row = box2.row()
            col1 = row.column(align=True)
            col1.scale_x = 0.9
            op_xp = col1.operator("opr.custom_rotate", text="X+", icon='FILE_REFRESH')
            op_xp.axis = 'X'
            op_xp.angle = np.deg2rad(5)
            op_yp = col1.operator("opr.custom_rotate", text="Y+", icon='FILE_REFRESH')
            op_yp.axis = 'Y'
            op_yp.angle = np.deg2rad(5)
            op_zp = col1.operator("opr.custom_rotate", text="Z+", icon='FILE_REFRESH')
            op_zp.axis = 'Z'
            op_zp.angle = np.deg2rad(5)
            
            col2 = row.column(align=True)
            col2.scale_x = 0.9
            op_xn = col2.operator("opr.custom_rotate", text="X-", icon='FILE_REFRESH')
            op_xn.axis = 'X'
            op_xn.angle = np.deg2rad(-5)
            op_yn = col2.operator("opr.custom_rotate", text="Y-", icon='FILE_REFRESH')
            op_yn.axis = 'Y'
            op_yn.angle = np.deg2rad(-5)
            op_zn = col2.operator("opr.custom_rotate", text="Z-", icon='FILE_REFRESH')
            op_zn.axis = 'Z'
            op_zn.angle = np.deg2rad(-5)

            col3 = row.column(align=True)
            row1 = col3.row()
            row1.prop(object, "rotation_euler", text="", index=0,)
            row2 = col3.row()
            row2.prop(object, "rotation_euler", text="", index=1)
            row3 = col3.row()
            row3.prop(object, "rotation_euler", text="", index=2)

            row = box2.row()
            row.operator("opr.default_rotation", icon='DRIVER_ROTATIONAL_DIFFERENCE')
            row = box2.row()
        
        box_out = layout.box()

        row = box_out.row()
        row.label(text="Save images to", icon='FOLDER_REDIRECT')
        row = box_out.row()
        row.prop(context.scene, "image_dir")

        row = box_out.row()
        col1 = row.column()
        col2 = row.column()
        col1.label(text="Steps", icon='SPHERE')
        col2.prop(context.scene, "rotation_steps", text="")

        row = box_out.row()
        if scene.auto_exec:
            row = box_out.row()
            row.operator("opr.auto_execute", icon='RESTRICT_RENDER_OFF')
            row = box_out.row()

        if scene.manual_exec:
            row = box_out.row()
            row.operator("opr.start_render", icon='RESTRICT_RENDER_OFF')
            row = box_out.row()


#-------------------------------------------------------------------------#

# 
class Select:
    def select_object(self, context):
        fixed_object_names = ['Camera', 'Light']

        for object in bpy.data.objects:
            object.select_set(False)

        for object in bpy.data.objects:
            if object.name not in fixed_object_names:
                object.select_set(True)
                context.view_layer.objects.active = object


class Follow:
    def camera_follow_object(self, context):
        object = context.object
        camera = context.scene.camera
        constraint = camera.constraints.new(type='TRACK_TO')
        constraint.target = object

    def light_follow_object(self, context):
        object = context.object
        light = bpy.data.objects.get('Light')
        constraint = light.constraints.new(type='TRACK_TO')
        constraint.target = object
    

class SetObject:
    def auto_set_object(self, context):
            self.set_origin(context)
            self.set_light()
            self.fit_distance_camera(context)
            self.auto_rotate(context)

    def set_origin(self, context):
        object = context.object
        bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
        object.location = mathutils.Vector((0, 0, 0))
        object.rotation_euler = mathutils.Vector((0, 0, 0))
    
    def set_light(self):
        light = bpy.data.objects.get('Light')
        light.data.type = 'SUN'
        light.data.energy = 2
        light.data.use_shadow = False

    def fit_distance_camera(self, context):
        object = context.object
        camera = context.scene.camera
        light = bpy.data.objects.get('Light')

        camera.location = mathutils.Vector((1,1,1))
        light.location = camera.location + mathutils.Vector((1,1,1))
        
        bounding_box = object.bound_box
        min_coords = mathutils.Vector(bounding_box[0])
        max_coords = mathutils.Vector(bounding_box[6])
        
        scaled_min_coords = min_coords * object.scale
        scaled_max_coords = max_coords * object.scale

        diagonal = (scaled_max_coords - scaled_min_coords).length
        
        aspect_ratio = context.scene.render.resolution_x / context.scene.render.resolution_y
        camera_angle = camera.data.angle
        
        if aspect_ratio > 1:
            camera_angle /= aspect_ratio
        
        distance_camera = (diagonal / 2) / np.tan(camera_angle / 2)
        
        camera_direction = (camera.location - object.location).normalized()
        camera.location = object.location + camera_direction * distance_camera
        light.location = camera.location

        clip_start = 0.1
        clip_end = camera.location[0] * 4
        camera.data.clip_start = clip_start
        camera.data.clip_end = clip_end
    
    def auto_rotate(self, context):
        self.select_object(context)
        object = context.object
        rotation_angle = np.deg2rad(90)
        default_angle = mathutils.Vector((0, 0, 0))
        
        object.rotation_euler = default_angle

        dimensions = {
            "x": object.dimensions.x,
            "y": object.dimensions.y,
            "z": object.dimensions.z
        }
        
        sorted_dims = sorted(dimensions.items(), key=lambda x: x[1], reverse=True)
        max_dim = sorted_dims[0][0]
        second_max_dim = sorted_dims[1][0]

        if max_dim == "x":
            if second_max_dim == "y":
                pass
            elif second_max_dim == "z":
                object.rotation_euler.x = rotation_angle

        elif max_dim == "y":
            if second_max_dim == "x":
                object.rotation_euler.z = rotation_angle
            elif second_max_dim == "z":
                object.rotation_euler.y = -rotation_angle
                object.rotation_euler.z = rotation_angle

        elif max_dim == "z":
            if second_max_dim == "x":
                object.rotation_euler.x = rotation_angle
                object.rotation_euler.z = rotation_angle
            elif second_max_dim == "y":
                object.rotation_euler.x= rotation_angle
                object.rotation_euler.z = rotation_angle
        return {"FINISHED"}


#-------------------------------------------------------------------------#

# Operador para importar arquivos de uma pasta e aplicar as configuracoes iniciais no objeto
class Opr_auto_execute(bpy.types.Operator, Select, Follow, SetObject):
    bl_idname = "opr.auto_execute"
    bl_label = "Generate Images"

    def execute(self, context):
        object = bpy.context.active_object
        if object:
            bpy.data.objects.remove(object, do_unlink=True)
        self.auto_import(context)
        return {"FINISHED"}
    
    def auto_import(self, context):
        object_path = context.scene.import_dir
        
        for file in os.listdir(object_path):
            if file.endswith(".stl") or file.endswith(".STL"):
                filepath = os.path.join(object_path, file)
                bpy.ops.import_mesh.stl(filepath=filepath)

                self.select_object(context)
                self.select_object(context)
                self.auto_set_object(context)
                self.camera_follow_object(context)
                self.light_follow_object(context)
                bpy.ops.opr.start_render()
                object = bpy.context.active_object
                bpy.data.objects.remove(object, do_unlink=True)


 #-------------------------------------------------------------------------#   

# Operador para aplicar as configuracoes iniciais no objeto
class Opr_import_object(bpy.types.Operator, Select, Follow, SetObject):
    bl_idname = "opr.import_object"
    bl_label = "Import Object"

    def execute(self, context):
        object = bpy.context.active_object
        if object:
            bpy.data.objects.remove(object, do_unlink=True)
        self.manual_import(context)
        self.select_object(context)
        self.auto_set_object(context)
        self.camera_follow_object(context)
        self.light_follow_object(context)

        return {"FINISHED"}
    
    def manual_import(self, context):
        file = context.scene.file_dir
        
        if file.endswith(".stl") or file.endswith(".STL"):
            bpy.ops.import_mesh.stl(filepath=file)


#-------------------------------------------------------------------------#

# Operador para aplicar as configuracoes iniciais no objeto
class Opr_default_rotation(bpy.types.Operator, Select, SetObject):
    bl_idname = "opr.default_rotation"
    bl_label = "Default Rotation"

    def execute(self, context):
        self.select_object(context)
        self.auto_rotate(context)

        return {"FINISHED"}


#-------------------------------------------------------------------------#

# Operador para o usuario definir uma rotacao customizada
class Opr_custom_rotate(bpy.types.Operator, Select):
    bl_idname = "opr.custom_rotate"
    bl_label = "Custom rotate object"

    axis_items = [('X', "X", ""), ('Y', "Y", ""), ('Z', "Z", "")]
    
    axis: bpy.props.EnumProperty(
        name="Axis",
        description="Axis to Rotate",
        items=axis_items,
        default='X'
    )

    angle: bpy.props.FloatProperty(name="Angle", default=0)

    def execute(self, context):
        self.select_object(context)
        self.custom_rotate(context, self.axis, self.angle)

        return {"FINISHED"}

    def custom_rotate(self, context, axis, angle):
        object = context.object
        if axis == 'X':
            object.rotation_euler.x += angle
        elif axis == 'Y':
            object.rotation_euler.y += angle
        elif axis == 'Z':
            object.rotation_euler.z += angle


#-------------------------------------------------------------------------#

# Operador para iniciar a renderização
class Opr_start_render(bpy.types.Operator, Follow, Select):
    bl_idname = "opr.start_render"
    bl_label = "Generate Images"
        
    def execute(self, context):
        self.select_object(context)
        self.set_render(context)
        self.start_render(context)
        return {"FINISHED"}

    def set_render(self, context):
        context.scene.render.image_settings.file_format = 'PNG'

    def rotateTo(self, planet, moon, angle):
        angle = np.deg2rad(angle)
        posX = moon[0] - planet[0]
        posY = moon[1] - planet[1]
        newX = posX * np.cos(angle) - posY * np.sin(angle)
        newY = posX * np.sin(angle) + posY * np.cos(angle)
        newPos = (newX + planet[0], newY + planet[1], moon[2])
        return newPos

    def start_render(self, context):
        object = context.object
        camera = context.scene.camera
        obj_location = object.location
        cam_location = camera.location
        light = bpy.data.objects.get('Light')
        rotation_steps = context.scene.rotation_steps
        pic_qnt = round(360 / rotation_steps)

        image_path = context.scene.image_dir

        for pic in range(pic_qnt):
            context.scene.render.filepath = f'{image_path}/{object.name}/{pic + 1}'
            bpy.ops.render.render(write_still=1)
            camera.location = self.rotateTo(obj_location, cam_location, rotation_steps)
            light.location = camera.location


#-------------------------------------------------------------------------#

# Registradores
def register():
    bpy.utils.register_class(VIEW3D_PT_synthetic_image_generator)
    bpy.utils.register_class(Opr_import_object)
    bpy.utils.register_class(Opr_default_rotation)
    bpy.utils.register_class(Opr_custom_rotate)
    bpy.utils.register_class(Opr_start_render)
    bpy.utils.register_class(Opr_auto_execute)
    
    bpy.types.Scene.auto_exec = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.manual_exec = bpy.props.BoolProperty(default=False)

    bpy.types.Scene.import_dir = bpy.props.StringProperty(
        name="",
        description="Directory to import objects",
        default="",
        maxlen=1024,
        subtype='DIR_PATH'
    )

    bpy.types.Scene.file_dir = bpy.props.StringProperty(
        name="",
        description="Directory to import single object",
        default="",
        maxlen=1024,
        subtype='FILE_PATH'
    )
    
    bpy.types.Scene.image_dir = bpy.props.StringProperty(
        name="",
        description="Directory to save images",
        default="SynImages",
        maxlen=1024,
        subtype='DIR_PATH'
    )

    bpy.types.Scene.rotation_steps = bpy.props.IntProperty(
        name="Rotation Steps",
        min=1,
        max=360,
        default=36,
    )


#-------------------------------------------------------------------------#

# Desregistradores
def unregister():
    bpy.utils.unregister_class(VIEW3D_PT_synthetic_image_generator)
    bpy.utils.unregister_class(Opr_import_object)
    bpy.utils.unregister_class(Opr_default_rotation)
    bpy.utils.unregister_class(Opr_custom_rotate)
    bpy.utils.unregister_class(Opr_start_render)
    bpy.utils.unregister_class(Opr_auto_execute)


#-------------------------------------------------------------------------#

# main
if __name__ == "__main__":
    register()