# Copyright 2014-2015 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from rosidl_cmake import convert_camel_case_to_lower_case_underscore
from rosidl_cmake import expand_template
from rosidl_cmake import extract_message_types
from rosidl_cmake import get_newest_modification_time
from rosidl_cmake import read_generator_arguments
from rosidl_parser import parse_message_file
from rosidl_parser import parse_service_file
from rosidl_parser import validate_field_types


# HACK temporary map until the generator uses the IDL-base pipeline
MSG_TYPE_TO_CPP = {
    'bool': 'bool',
    'byte': 'uint8_t',
    'char': 'char',
    'float32': 'float',
    'float64': 'double',
    'uint8': 'uint8_t',
    'int8': 'int8_t',
    'uint16': 'uint16_t',
    'int16': 'int16_t',
    'uint32': 'uint32_t',
    'int32': 'int32_t',
    'uint64': 'uint64_t',
    'int64': 'int64_t',
    'string': 'std::basic_string<char, std::char_traits<char>, ' +
              'typename ContainerAllocator::template rebind<char>::other>',
}


def generate_cpp(generator_arguments_file):
    args = read_generator_arguments(generator_arguments_file)

    template_dir = args['template_dir']
    mapping_msgs = {
        os.path.join(template_dir, 'msg__rosidl_typesupport_introspection_cpp.hpp.em'):
        '%s__rosidl_typesupport_introspection_cpp.hpp',
        os.path.join(template_dir, 'msg__type_support.cpp.em'):
        '%s__type_support.cpp',
    }
    mapping_srvs = {
        os.path.join(template_dir, 'srv__rosidl_typesupport_introspection_cpp.hpp.em'):
        '%s__rosidl_typesupport_introspection_cpp.hpp',
        os.path.join(template_dir, 'srv__type_support.cpp.em'):
        '%s__type_support.cpp',
    }

    for template_file in mapping_msgs.keys():
        assert os.path.exists(template_file), 'Could not find template: ' + template_file

    for template_file in mapping_srvs.keys():
        assert os.path.exists(template_file), 'Could not find template: ' + template_file

    pkg_name = args['package_name']
    known_msg_types = extract_message_types(
        pkg_name, args['ros_interface_files'], args.get('ros_interface_dependencies', []))

    functions = {
        'get_header_filename_from_msg_name': convert_camel_case_to_lower_case_underscore,
    }
    latest_target_timestamp = get_newest_modification_time(args['target_dependencies'])

    for ros_interface_file in args['ros_interface_files']:
        extension = os.path.splitext(ros_interface_file)[1]
        subfolder = os.path.basename(os.path.dirname(ros_interface_file))
        if extension == '.msg':
            spec = parse_message_file(pkg_name, ros_interface_file)
            validate_field_types(spec, known_msg_types)
            for template_file, generated_filename in mapping_msgs.items():
                generated_file = os.path.join(
                    args['output_dir'], subfolder, generated_filename %
                    convert_camel_case_to_lower_case_underscore(spec.base_type.type))

                data = {'spec': spec, 'subfolder': subfolder, 'cpp_primitives': MSG_TYPE_TO_CPP}
                data.update(functions)
                expand_template(
                    template_file, data, generated_file,
                    minimum_timestamp=latest_target_timestamp)

        elif extension == '.srv':
            spec = parse_service_file(pkg_name, ros_interface_file)
            validate_field_types(spec, known_msg_types)
            for template_file, generated_filename in mapping_srvs.items():
                generated_file = os.path.join(
                    args['output_dir'], subfolder, generated_filename %
                    convert_camel_case_to_lower_case_underscore(spec.srv_name))

                data = {'spec': spec, 'subfolder': subfolder}
                data.update(functions)
                expand_template(
                    template_file, data, generated_file,
                    minimum_timestamp=latest_target_timestamp)

    return 0
