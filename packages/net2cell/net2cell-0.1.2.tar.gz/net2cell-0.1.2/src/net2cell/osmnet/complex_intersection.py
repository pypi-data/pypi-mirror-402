from ..networkclass.macronet import Node, Network
from .. import settings as og_settings
from shapely import geometry
import csv
import os
import sys


def _designateComplexIntersectionsFromIntFile(network, int_file, int_buffer):
    if not os.path.exists(int_file):
        sys.exit(f'ERROR: int_file {int_file} does not exist')

    fin = open(int_file, 'r')
    reader = csv.DictReader(fin)

    for field in ['x_coord', 'y_coord']:
        if field not in reader.fieldnames:
            sys.exit(f'ERROR: required field ({field}) does not exist in the int_file')

    max_intersection_id = network.max_intersection_id
    for int_info in reader:
        int_center = geometry.Point(float(int_info['x_coord']), float(int_info['y_coord']))
        int_center_xy = network.GT.geo_from_latlon(int_center)
        if 'int_buffer' in reader.fieldnames:
            buffer_ = int_info['int_buffer']
            buffer_ = float(buffer_) if buffer_ else int_buffer
        else:
            buffer_ = int_buffer

        intersection_nodes = [node for _, node in network.node_dict.items() if node.intersection_id is None and int_center_xy.distance(node.geometry_xy) <= buffer_]

        if len(intersection_nodes) < 2:
            continue

        for node in intersection_nodes:
            node.intersection_id = max_intersection_id
        max_intersection_id += 1

    network.max_intersection_id = max_intersection_id


def _autoidentifyComplexIntersections(network, int_buffer):
    group_list = []
    group_status = []
    for _,link in network.link_dict.items():
        if link.length > int_buffer: continue
        if not (link.from_node.intersection_id is None and link.to_node.intersection_id is None): continue
        if not (link.from_node.ctrl_type == 'signal' and link.to_node.ctrl_type == 'signal'): continue
        group_list.append({link.from_node, link.to_node})
        group_status.append(1)

    number_of_valid_groups = sum(group_status)
    while True:
        for group_no1,group1 in enumerate(group_list):
            if group_status[group_no1] == 0: continue
            for group_no2,group2 in enumerate(group_list):
                if group_status[group_no2] == 0: continue
                if group_no1 == group_no2: continue
                if len(group1.intersection(group2)) > 0:
                    group1.update(group2)
                    group_status[group_no2] = 0

        new_number_of_valid_groups = sum(group_status)
        if number_of_valid_groups == new_number_of_valid_groups:
            break
        else:
            number_of_valid_groups = new_number_of_valid_groups

    max_intersection_id = network.max_intersection_id
    for group_no, group in enumerate(group_list):
        if group_status[group_no] == 0: continue
        for node in group: node.intersection_id = max_intersection_id
        max_intersection_id += 1
    network.max_intersection_id = max_intersection_id


def consolidateComplexIntersections(network, auto_identify=False, intersection_file=None, int_buffer=og_settings.default_int_buffer):
    if intersection_file is not None:
        _designateComplexIntersectionsFromIntFile(network, intersection_file, int_buffer)

    if auto_identify:
        _autoidentifyComplexIntersections(network, int_buffer)

    if og_settings.verbose:
        print('Consolidating Complex Intersections (mrnet)')

    node_group_dict = {}
    node_group_ctrl_type_dict = {}
    for _, node in network.node_dict.items():
        if node.intersection_id is not None:
            if node.intersection_id in node_group_dict.keys():
                node_group_dict[node.intersection_id].append(node)
            else:
                node_group_dict[node.intersection_id] = [node]
                node_group_ctrl_type_dict[node.intersection_id] = False
            if node.ctrl_type == 'signal':
                node_group_ctrl_type_dict[node.intersection_id] = True

    removal_node_set = set()
    removal_link_set = set()
    number_of_intersections_consolidated = 0

    for intersection_id, node_group in node_group_dict.items():
        if len(node_group) < 2:
            continue

        new_node = Node(network.max_node_id)
        new_node.intersection_id = intersection_id
        if node_group_ctrl_type_dict[intersection_id]:
            new_node.ctrl_type = 'signal'
        osm_node_id_list = []
        x_coord_sum, y_coord_sum = 0.0, 0.0
        x_coord_xy_sum, y_coord_xy_sum = 0.0, 0.0

        for node in node_group:
            removal_node_set.add(node)
            osm_node_id_list.append(node.osm_node_id if node.osm_node_id is not None else 'None')
            x_coord_sum += node.geometry.x
            y_coord_sum += node.geometry.y
            x_coord_xy_sum += node.geometry_xy.x
            y_coord_xy_sum += node.geometry_xy.y

            for link in node.incoming_link_list:
                if link.from_node in node_group:
                    removal_link_set.add(link)
                else:
                    link.to_node = new_node
                    new_node.incoming_link_list.append(link)
            for link in node.outgoing_link_list:
                if link.to_node in node_group:
                    removal_link_set.add(link)
                else:
                    link.from_node = new_node
                    new_node.outgoing_link_list.append(link)

            new_node.osm_highway = node.osm_highway

        new_node.osm_node_id = '_'.join(osm_node_id_list)
        x_coord_ave = round(x_coord_sum / len(node_group), og_settings.lonlat_coord_precision)
        y_coord_ave = round(y_coord_sum / len(node_group), og_settings.lonlat_coord_precision)
        new_node.geometry = geometry.Point(x_coord_ave, y_coord_ave)
        x_coord_xy_ave = round(x_coord_xy_sum / len(node_group), og_settings.local_coord_precision)
        y_coord_xy_ave = round(y_coord_xy_sum / len(node_group), og_settings.local_coord_precision)
        new_node.geometry_xy = geometry.Point(x_coord_xy_ave, y_coord_xy_ave)

        for link in new_node.incoming_link_list:
            new_coordinates = list(link.geometry.coords) + list(link.to_node.geometry.coords)
            link.geometry = geometry.LineString(new_coordinates)
        for link in new_node.outgoing_link_list:
            new_coordinates = list(link.from_node.geometry.coords) + list(link.geometry.coords)
            link.geometry = geometry.LineString(new_coordinates)

        network.node_dict[new_node.node_id] = new_node
        network.max_node_id += 1
        number_of_intersections_consolidated += 1

    for node in removal_node_set: del network.node_dict[node.node_id]
    for link in removal_link_set: del network.link_dict[link.link_id]

    if og_settings.verbose:
        print(f'    {number_of_intersections_consolidated} intersections have been consolidated')



