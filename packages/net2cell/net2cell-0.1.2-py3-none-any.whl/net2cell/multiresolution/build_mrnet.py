from ..networkclass.macronet import Network
from ..networkclass.mesonet import MesoNetwork, MesoNode, MesoLink
from ..networkclass.micronet import MicroNetwork, MicroNode, MicroLink
from .netgen import NetGenerator
from ..movement.generate_movements import generateMovements, validateUserInputMovements
from ..utils.util_geo import getLineAngle, offsetLine
from .. import settings as og_settings
from shapely import geometry
from shapely.ops import substring
import math

_length_of_short_cut = 0.1
_length_of_cut = {0: 2.0, 1: 8.0, 2: 12.0, 3: 14.0, 4: 16.0, 5: 18.0, 6: 20, 7:22, 8:24}
for i_ in range(9,100): _length_of_cut[i_] = 25
_minimum_cutted_length = 2.0

def _checkMovementLinkNecessity(node_dict):
    for node_id, node in node_dict.items():
        if node.ctrl_type == 'signal': continue
        if len(node.incoming_link_list) == 1 and len(node.outgoing_link_list) >= 1:
            ib_link = node.incoming_link_list[0]
            angle_flag = True
            for ob_link in node.outgoing_link_list:
                angle = getLineAngle(ib_link.geometry_xy, ob_link.geometry_xy)
                if angle > 0.75 * math.pi or angle < -0.75 * math.pi:
                    angle_flag = False
                    break
            if not angle_flag: continue
            ob_link_set = set()
            multiple_connection = False
            for movement in node.movement_list:
                if movement.ob_link in ob_link_set:
                    multiple_connection = True
                    break
                else:
                    ob_link_set.add(movement.ob_link)
            if multiple_connection: continue
            node.movement_link_needed = False
            ib_link.downstream_short_cut = True
            ib_link.downstream_is_target = True
            for ob_link in node.outgoing_link_list:
                ob_link.upstream_short_cut = True
        elif len(node.outgoing_link_list) == 1 and len(node.incoming_link_list) >= 1:
            ob_link = node.outgoing_link_list[0]
            angle_flag = True
            for ib_link in node.incoming_link_list:
                angle = getLineAngle(ib_link.geometry_xy, ob_link.geometry_xy)
                if angle > 0.75 * math.pi or angle < -0.75 * math.pi:
                    angle_flag = False
                    break
            if not angle_flag: continue
            ib_link_set = set()
            multiple_connection = False
            for movement in node.movement_list:
                if movement.ib_link in ib_link_set:
                    multiple_connection = True
                    break
                else:
                    ib_link_set.add(movement.ib_link)
            if multiple_connection: continue
            node.movement_link_needed = False
            ob_link.upstream_short_cut = True
            ob_link.upstream_is_target = True
            for ib_link in node.incoming_link_list:
                ib_link.downstream_short_cut = True

def _offsetLinkGeometry(link_dict, width_of_lane, GT):
    link_offset_dict = {}
    link_ids = tuple(link_dict.keys())
    for link_no_a, link_id_a in enumerate(link_ids):
        link_a = link_dict[link_id_a]
        if link_a in link_offset_dict.keys():
            continue
        geometry_xy_a_r = geometry.LineString(list(link_a.geometry_xy.coords)[::-1])
        reversed_link_found = False
        for link_id_b in link_ids[link_no_a+1:]:
            link_b = link_dict[link_id_b]
            if geometry_xy_a_r.equals_exact(link_b.geometry_xy, tolerance=0.1):
                reversed_link_found = True
                link_offset_dict[link_a] = True
                link_offset_dict[link_b] = True
                break
        if not reversed_link_found:
            link_offset_dict[link_a] = False

    for link, need_offset in link_offset_dict.items():
        if need_offset:
            offset_distance = (link.max_lanes / 2 + 0.5) * width_of_lane
            geometry_xy_offset = link.geometry_xy.offset_curve(distance=-1*offset_distance, join_style=2)
            if isinstance(geometry_xy_offset, geometry.MultiLineString):
                link.geometry_xy_offset = offsetLine(link.geometry_xy, offset_distance)
            else:
                link.geometry_xy_offset = geometry_xy_offset
            link.geometry_offset = GT.geo_to_latlon(link.geometry_xy_offset)
        else:
            link.geometry_offset = link.geometry
            link.geometry_xy_offset = link.geometry_xy

    for link_id, link in link_dict.items():
        link.lanes_change_point_list = [item / link.length * link.length_offset for item in link.lanes_change_point_list]

def _linkLengthToCut(link):
    upstream_max_cut = max(_length_of_short_cut, link.lanes_change_point_list[1] - link.lanes_change_point_list[0] - 3)
    downstream_max_cut = max(_length_of_short_cut, link.lanes_change_point_list[-1] - link.lanes_change_point_list[-2] - 3)
    if link.upstream_short_cut and link.downstream_short_cut:
        total_length_needed = 2 * _length_of_short_cut + _minimum_cutted_length
        if link.length_offset > total_length_needed:
            link.length_of_cut_upstream = _length_of_short_cut
            link.length_of_cut_downstream = _length_of_short_cut
        else:
            link.length_of_cut_upstream = link.length_offset / total_length_needed * _length_of_short_cut
            link.length_of_cut_downstream = link.length_offset / total_length_needed * _length_of_short_cut
    elif link.upstream_short_cut:
        length_found = False
        ii = 0
        for i in range(link.lanes_list[-1], -1, -1):
            if link.length_offset > min(downstream_max_cut, _length_of_cut[i]) + _length_of_short_cut + _minimum_cutted_length:
                ii = i
                length_found = True
                break
        if length_found:
            link.length_of_cut_upstream = _length_of_short_cut
            link.length_of_cut_downstream = min(downstream_max_cut, _length_of_cut[ii])
        else:
            downstream_needed = min(downstream_max_cut, _length_of_cut[0])
            total_length_needed = downstream_needed + _length_of_short_cut + _minimum_cutted_length
            link.length_of_cut_upstream = link.length_offset / total_length_needed * _length_of_short_cut
            link.length_of_cut_downstream = link.length_offset / total_length_needed * downstream_needed
    elif link.downstream_short_cut:
        length_found = False
        ii = 0
        for i in range(link.lanes_list[-1], -1, -1):
            if link.length_offset > min(upstream_max_cut, _length_of_cut[i]) + _length_of_short_cut + _minimum_cutted_length:
                ii = i
                length_found = True
                break
        if length_found:
            link.length_of_cut_upstream = min(upstream_max_cut, _length_of_cut[ii])
            link.length_of_cut_downstream = _length_of_short_cut
        else:
            upstream_needed = min(upstream_max_cut, _length_of_cut[0])
            total_length_needed = upstream_needed + _length_of_short_cut + _minimum_cutted_length
            link.length_of_cut_upstream = link.length_offset / total_length_needed * _length_of_cut[0]
            link.length_of_cut_downstream = link.length_offset / total_length_needed * _length_of_short_cut
    else:
        length_found = False
        ii = 0
        for i in range(link.lanes_list[-1], -1, -1):
            if link.length_offset > min(upstream_max_cut, _length_of_cut[i]) + min(downstream_max_cut, _length_of_cut[i]) + _minimum_cutted_length:
                ii = i
                length_found = True
                break
        if length_found:
            link.length_of_cut_upstream = min(upstream_max_cut, _length_of_cut[ii])
            link.length_of_cut_downstream = min(downstream_max_cut, _length_of_cut[ii])
        else:
            upstream_needed = min(upstream_max_cut, _length_of_cut[0])
            downstream_needed = min(downstream_max_cut, _length_of_cut[0])
            total_length_needed = downstream_needed + upstream_needed + _minimum_cutted_length
            link.length_of_cut_upstream = link.length_offset / total_length_needed * upstream_needed
            link.length_of_cut_downstream = link.length_offset / total_length_needed * downstream_needed

def _performLinkCut(link, GT):
    link.cutted_lanes_change_point_list = link.lanes_change_point_list.copy()
    link.cutted_lanes_list = link.lanes_list.copy()
    link.cutted_lanes_change_list = link.lanes_change_list.copy()
    link.cutted_lanes_change_point_list[0], link.cutted_lanes_change_point_list[-1] = link.length_of_cut_upstream, link.length_offset - link.length_of_cut_downstream
    for i in range(len(link.cutted_lanes_list)):
        start_position = link.cutted_lanes_change_point_list[i]
        end_position = link.cutted_lanes_change_point_list[i+1]
        segment_geometry_xy = substring(link.geometry_xy_offset, start_dist=start_position, end_dist=end_position)
        link.cutted_geometry_xy_list.append(segment_geometry_xy)
        link.cutted_geometry_list.append(GT.geo_to_latlon(segment_geometry_xy))

def _cutMacroLinks(link_dict, GT):
    for link_id, link in link_dict.items():
        _linkLengthToCut(link)
        _performLinkCut(link, GT)

## NetGenerator is imported from .netgen; no local stub here

def buildMultiResolutionNets(macronet,
                             generate_micro_net=True,
                             auto_movement_generation=True,
                             exclusive_bike_walk_lanes=True,
                             connector_type=None,
                             width_of_lane=3.5,
                             length_of_cell=7.0,
                             num_nodes_for_ramp_alignment=8):
    if og_settings.verbose:
        print('Building Multiresolution Networks (mrnet)')

    if not macronet.complete_link_lane_info:
        print('WARNING: Multiresolution network generation skipped: some links are missing lanes info.')
        return

    if auto_movement_generation:
        generateMovements(macronet)
    else:
        for _, link in macronet.link_dict.items():
            link.linkLaneListFromSegment()
        validateUserInputMovements(macronet)

    _offsetLinkGeometry(macronet.link_dict, width_of_lane, macronet.GT)
    _checkMovementLinkNecessity(macronet.node_dict)
    _cutMacroLinks(macronet.link_dict, macronet.GT)

    net_generator = NetGenerator(macronet, generate_micro_net, exclusive_bike_walk_lanes, length_of_cell, width_of_lane, num_nodes_for_ramp_alignment)
    net_generator.generateNet()
    macronet.mesonet, macronet.micronet = net_generator.mesonet, net_generator.micronet



