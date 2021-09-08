import os
import ifcopenshell
import create_temp as ct
from create_temp import split_by_connection
import extract_ifc as ext

class IfcToSdf(object):
    def __init__(self, input_bim_path, folder_name, output_sdf_path, ifc_converter_path):
        # create folders as gazebo requirements
        self.input_bim_path = input_bim_path
        self.folder_name = folder_name
        self.output_sdf_path = output_sdf_path + '\\{}'.format(self.folder_name)
        self.launch_path = self.output_sdf_path + '\\launch'
        self.models_path = self.output_sdf_path + '\\models'
        self.worlds_path = self.output_sdf_path + '\\worlds'
        self.ifc_converter_path = ifc_converter_path
        if not os.path.exists(self.output_sdf_path):
            os.mkdir(self.output_sdf_path)
        if not os.path.exists(self.launch_path):
            os.mkdir(self.launch_path)
        if not os.path.exists(self.models_path):
            os.mkdir(self.models_path)
        if not os.path.exists(self.worlds_path):
            os.mkdir(self.worlds_path)

        # read ifc by ifcopenshell
        self.ifc_file = ifcopenshell.open(self.input_bim_path)

        # def requirement attr
        self.project = self.ifc_file.by_type('IFCPROJECT')[0]
        self.site = self.ifc_file.by_type('IFCSITE')[0]
        self.ifc_connection = self.ifc_file.by_type('IFCRELCONNECTSWITHREALIZINGELEMENTS')

        # namespace
        self.site_namespace = str(self.site.is_a() + '_' + self.site.GlobalId)

        # element_list
        self.elements_list = []

    def create_ros_launch(self):
        launch_path = self.launch_path + '\\{}.launch'.format(str(self.project.is_a() + '_launch'))
        launch_file = """<launch>
  <include file="$(find gazebo_ros)/launch/empty_world.launch">
    <arg name="world_name" value="$(find {})/worlds/{}.world"/> 
    <arg name="paused" value="false"/>
    <arg name="use_sim_time" value="true"/>
    <arg name="gui" value="true"/>
    <arg name="recording" value="false"/>
    <arg name="debug" value="false"/>
  </include>
</launch>
""".format(self.folder_name, self.site_namespace)

        with open(launch_path, 'w', encoding='utf-8') as f:
            f.write(str(launch_file))

    def create_models(self):
        sorted_types = split_by_connection(self.ifc_connection)
        all_elements = list(sorted_types) + [[self.site]]

        for elements in all_elements:
            for _ in elements:
                element_name = _.is_a() + '_' + _.GlobalId
                if _.is_a() != 'IfcFastener':
                    self.elements_list.append(element_name)
                element_folder_path = self.models_path + '\\{}'.format(element_name)
                # create single element sdf format folder
                if not os.path.exists(element_folder_path):
                    os.mkdir(element_folder_path)
                # create meshes folder, save .dae here
                element_meshes = element_folder_path + '\\meshes'
                if not os.path.exists(element_meshes):
                    os.mkdir(element_meshes)
                    # create .ifc for single element
                element_path = element_meshes + '\\{}.ifc'.format(element_name)
                with open(element_path, 'w', encoding='utf-8') as f:
                    for head in ct.get_head(path_bim):
                        f.write(str(head))
                    f.write('\n')
                    f.write('DATA;')
                    f.write('\n')
                    ifc_agg = self.ifc_file.by_type('IFCRELAGGREGATES')
                    for agg in ifc_agg:
                        f.write(str(agg).upper() + ';' + '\n')
                    for tem in ct.get_project(ifc_agg):
                        tem = ct.drop_rep(tem)
                        f.write(str(tem).upper() + ';' + '\n')
                    ifc_contain = self.ifc_file.by_type('IFCRELCONTAINEDINSPATIALSTRUCTURE')
                    for contain in ifc_contain:
                        f.write(str(contain).upper() + ';' + '\n')
                    print('element is: ', _)
                    element_value = []
                    temp = list(ext.LinkEntity().find_all_entity(_))
                    for i in temp:
                        element_value.append(i)
                    for element in element_value:
                        if _.is_a() == 'IfcSite':
                            f.write(str(element).upper() + ';' + '\n')
                        else:
                            element = ct.drop_rep(element)
                            f.write(str(element).upper() + ';' + '\n')
                    f.write('\n')
                    f.write('ENDSEC;')
                    f.write('\n')
                    f.write('END-ISO-10303-21;')
                # use ifcconvert to convert ifc to collada
                collada_path = element_meshes + '\\{}.dae'.format(element_name)
                convert_path = '{} {} {}'.format(self.ifc_converter_path, element_path, collada_path)
                os.popen(convert_path)
                # create model.config
                model_config_path = element_folder_path + '\\model.config'
                model_config = """<?xml version = "1.0"?>
<model>
    <name>{0}</name>
    <version>1.0</version>
    <sdf version='1.5'>model.sdf</sdf>

    <author>
        <name>Pandzay</name>
        <email>a.zhu@tue.nl</email>
    </author>

    <description>
        {0}
    </description>
</model>
""".format(element_name)

                with open(model_config_path, 'w', encoding='utf-8') as f:
                    f.write(str(model_config))
                # create model.sdf
                model_sdf_path = element_folder_path + '\\model.sdf'
                model_meshes = 'model://' + element_name + '//meshes//{}'.format(element_name + '.dae')
                exact_weight = 0
                for definition in _.IsDefinedBy:
                    if definition.is_a('IfcRelDefinesByProperties'):
                        property_set = definition.RelatingPropertyDefinition
                        if property_set.Name == 'Structural':
                            structural_property = property_set[4]

                            for property in structural_property:
                                if property.is_a('IfcPropertySingleValue'):
                                    if property.Name == 'Exact Weight':
                                        exact_weight = property.NominalValue.wrappedValue
                model_sdf = """<?xml version="1.0" ?>
<sdf version = '1.5'>
    <model name = "{0}">
        <static>False</static>
        <self_collide>True</self_collide>
        <enable_wind>True</enable_wind>
        <pose>0 0 0 0 0 0</pose>

        <link name = '{1}'>
            <inertial>
                <mass>{2}</mass>
            </inertial>

            <collision name='collision'>
                <geometry>
                    <mesh>
                        <uri>{3}</uri>
                    </mesh>
                </geometry>
            </collision>

            <visual name='visual'>
                <geometry>
                    <mesh>
                        <uri>{3}</uri>
                    </mesh>
                </geometry>
            </visual>
        </link>
    </model>
</sdf>
""".format(element_name, _.is_a(), exact_weight, model_meshes)

                with open(model_sdf_path, 'w', encoding='utf-8') as f:
                    f.write(str(model_sdf))

    def create_worlds(self):
        world_path = self.worlds_path + '\\{}.world'.format(self.site_namespace)
        world_meshes_path = 'model://{0}/meshes/{0}.dae'.format(self.site_namespace)
        world_file = """<?xml version="1.0" ?>
<sdf version="1.5">
  <world name="{0}">
    <physics type="ode">
      ...
    </physics>
    <model name = "{0}">
        <static>True</static>
        <self_collide>True</self_collide>
        <enable_wind>True</enable_wind>
        <pose>0 0 0 0 0 0</pose>
        <link name = 'site'>
            <inertial>
                <mass>999999999</mass>
            </inertial>

            <collision name='collision'>
                <geometry>
                    <mesh>
                        <uri>{1}</uri>
                    </mesh>
                </geometry>
            </collision>

            <visual name='visual'>
                <geometry>
                    <mesh>
                        <uri>{1}</uri>
                    </mesh>
                </geometry>
            </visual>

        </link>
    </model>
""".format(self.site_namespace, world_meshes_path)
        with open(world_path, 'w', encoding='utf-8') as f:
            f.write(str(world_file))
        with open(world_path, 'a', encoding='utf-8') as f:
            for in_element in self.elements_list:
                include_element = """
    <include>
        <uri>model://{}</uri>
    </include>
    """.format(in_element)
                f.write(str(include_element))
        with open(world_path, 'a', encoding='utf-8') as f:
            f.write('\n')
            f.write(' </world>')
            f.write('\n')
            f.write('</sdf>')


if __name__ == "__main__":
    # BIM model's path
    path_bim = 'your path'
    # the path where you want to set the sdf folder
    path_sdf = 'your path'
    # the path for ifcConverter
    path_converter = 'your path'
    # name your model
    its = IfcToSdf(path_bim, 'bim_model', path_sdf, path_converter)
    its.create_ros_launch()
    its.create_models()
    its.create_worlds()