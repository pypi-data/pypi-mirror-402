import copy

from ..networkclass.mesonet import MesoNode, MesoLink, MesoNetwork
from ..networkclass.micronet import MicroNode, MicroLink, MicroNetwork
from ..utils.util_geo import offsetLine
from .. import settings as og_settings
from shapely import geometry
import sys


class NetGenerator:
    def __init__(self, macronet, generate_micro_net, exclusive_bike_walk_lanes, length_of_cell, width_of_lane, num_nodes_for_ramp_alignment=8):
        self.macronet = macronet
        self.generate_micro_net = generate_micro_net
        self.exclusive_bike_walk_lanes = False
        self.length_of_cell = length_of_cell
        self.width_of_lane = width_of_lane
        self.num_nodes_for_ramp_alignment = num_nodes_for_ramp_alignment

        self.bike_lane_width = 0.5
        self.walk_lane_width = 0.5

        self.mesonet = MesoNetwork()
        self.micronet = MicroNetwork() if generate_micro_net else None

        self.number_of_expanded_mesonode = {}

    def getMultimoalUse(self, allowed_uses):
        if self.exclusive_bike_walk_lanes:
            if len(allowed_uses) <= 1:
                return {'mainlane_allowed_uses': allowed_uses, 'extra_bike': False, 'extra_walk': False}
            else:
                allowed_uses_set = set(allowed_uses).union({'auto','bike','walk'})
                if allowed_uses_set == {'auto','bike'}:
                    return {'mainlane_allowed_uses':['auto'], 'extra_bike':True, 'extra_walk':False}
                elif allowed_uses_set == {'auto','walk'}:
                    return {'mainlane_allowed_uses':['auto'], 'extra_bike':False, 'extra_walk':True}
                elif allowed_uses_set == {'bike','walk'}:
                    return {'mainlane_allowed_uses':['bike'], 'extra_bike':False, 'extra_walk':True}
                elif allowed_uses_set == {'auto','bike','walk'}:
                    return {'mainlane_allowed_uses':['auto'], 'extra_bike':True, 'extra_walk':True}
        else:
            return {'mainlane_allowed_uses':allowed_uses, 'extra_bike':False, 'extra_walk':False}

    def getLaneGeometry(self, original_geometry, lane_offset):
        if lane_offset < -1e-3 or lane_offset > 1e-3:

            lane_geometry_xy = original_geometry.offset_curve(distance=-1*lane_offset, join_style=2)
            if isinstance(lane_geometry_xy, geometry.MultiLineString):
                lane_geometry_xy = offsetLine(original_geometry, lane_offset)

            if lane_geometry_xy.is_empty:
                return self.getLaneGeometry(original_geometry, lane_offset*0.6)

            return lane_geometry_xy

        else:
            return copy.copy(original_geometry)

    # The remaining methods mirror the original implementation closely

    def createMicroNetForConnector(self, mesolink, ib_mesolink, ib_lane_index_start, ob_mesolink, ob_lane_index_start):
        max_micronode_id = self.micronet.max_node_id
        max_microlink_id = self.micronet.max_link_id

        for i in range(mesolink.lanes):
            start_micronode = ib_mesolink.micronode_list[ib_lane_index_start+i][-1]
            end_micronode = ob_mesolink.micronode_list[ob_lane_index_start+i][0]
            lane_geometry_xy = geometry.LineString([start_micronode.geometry_xy, end_micronode.geometry_xy])

            number_of_cells = max(1, round(lane_geometry_xy.length / self.length_of_cell))
            micronode_geometry_xy_list = [lane_geometry_xy.interpolate(i/number_of_cells, normalized=True) for i in range(1,number_of_cells)]

            mesolink.micronode_list.append([])
            mesolink.microlink_list.append([])
            last_micronode = start_micronode

            first_movement_cell = True

            for micronode_geometry_xy in micronode_geometry_xy_list:
                micronode = MicroNode(max_micronode_id)
                micronode.geometry_xy = micronode_geometry_xy
                micronode.geometry = self.macronet.GT.geo_to_latlon(micronode_geometry_xy)
                micronode.mesolink = mesolink
                micronode.lane_no = i + 1
                mesolink.micronode_list[-1].append(micronode)
                self.micronet.node_dict[micronode.node_id] = micronode
                max_micronode_id += 1

                microlink = MicroLink(max_microlink_id)
                microlink.from_node = last_micronode
                microlink.to_node = micronode
                microlink.geometry = geometry.LineString([microlink.from_node.geometry, microlink.to_node.geometry])
                microlink.geometry_xy = geometry.LineString([microlink.from_node.geometry_xy, microlink.to_node.geometry_xy])
                microlink.mesolink = mesolink
                microlink.cell_type = 1

                if first_movement_cell:
                    microlink.is_first_movement_cell = True
                    first_movement_cell = False

                mesolink.microlink_list[-1].append(microlink)
                self.micronet.link_dict[microlink.link_id] = microlink
                max_microlink_id += 1
                microlink.from_node.outgoing_link_list.append(microlink)
                microlink.to_node.incoming_link_list.append(microlink)

                last_micronode = micronode

            microlink = MicroLink(max_microlink_id)
            microlink.from_node = last_micronode
            microlink.to_node = end_micronode
            microlink.geometry = geometry.LineString([microlink.from_node.geometry, microlink.to_node.geometry])
            microlink.geometry_xy = geometry.LineString([microlink.from_node.geometry_xy, microlink.to_node.geometry_xy])
            microlink.mesolink = mesolink
            microlink.cell_type = 1

            if first_movement_cell:
                microlink.is_first_movement_cell = True

            mesolink.microlink_list[-1].append(microlink)
            self.micronet.link_dict[microlink.link_id] = microlink
            max_microlink_id += 1
            microlink.from_node.outgoing_link_list.append(microlink)
            microlink.to_node.incoming_link_list.append(microlink)

        self.micronet.max_node_id = max_micronode_id
        self.micronet.max_link_id = max_microlink_id
    def createMicroNetForNormalLink(self, link):
        max_micronode_id = self.micronet.max_node_id
        max_microlink_id = self.micronet.max_link_id

        MultimoalUse = self.getMultimoalUse(link.allowed_uses)
        mainlane_allowed_uses, extra_bike, extra_walk = MultimoalUse['mainlane_allowed_uses'], MultimoalUse['extra_bike'], MultimoalUse['extra_walk']

        for mesolink in link.mesolink_list:
            original_number_of_lanes = mesolink.macrolink.lanes
            lane_changes_left = mesolink.lanes_change[0]
            num_of_lane_offset_between_left_most_and_central = -1 * (original_number_of_lanes / 2 - 0.5 + lane_changes_left)

            lane_geometry_xy_list = []
            extra_bike_geometry_xy, extra_walk_geometry_xy = None, None
            lane_offset = 0
            for i in range(mesolink.lanes):
                lane_offset = (num_of_lane_offset_between_left_most_and_central + i) * self.width_of_lane
                lane_geometry_xy_list.append(self.getLaneGeometry(mesolink.geometry_xy, lane_offset))
            if extra_bike and not extra_walk:
                bike_lane_offset = lane_offset + self.bike_lane_width
                extra_bike_geometry_xy = self.getLaneGeometry(mesolink.geometry_xy, bike_lane_offset)
            if not extra_bike and extra_walk:
                walk_lane_offset = lane_offset + self.walk_lane_width
                extra_walk_geometry_xy = self.getLaneGeometry(mesolink.geometry_xy, walk_lane_offset)
            if extra_bike and extra_walk:
                bike_lane_offset = lane_offset + self.bike_lane_width
                walk_lane_offset = bike_lane_offset + self.walk_lane_width
                extra_bike_geometry_xy = self.getLaneGeometry(mesolink.geometry_xy, bike_lane_offset)
                extra_walk_geometry_xy = self.getLaneGeometry(mesolink.geometry_xy, walk_lane_offset)

            # anchor: parallel-translate current mesolink lane centerlines to upstream mapped lanes (LEFT-aligned)
            try:
                meso_index = link.mesolink_list.index(mesolink)
                if meso_index > 0:
                    upstream_mesolink = link.mesolink_list[meso_index - 1]
                    if hasattr(upstream_mesolink, 'lane_geometry_xy_list') and upstream_mesolink.lane_geometry_xy_list:
                        up_left_index = upstream_mesolink.lanes_change[0]
                        down_left_index = mesolink.lanes_change[0]
                        min_left_index = min(up_left_index, down_left_index)
                        up_lane_index_start = up_left_index - min_left_index
                        down_lane_index_start = down_left_index - min_left_index

                        number_of_connecting_lanes = min(
                            upstream_mesolink.lanes - up_lane_index_start,
                            mesolink.lanes - down_lane_index_start
                        )

                        for j in range(number_of_connecting_lanes):
                            up_lane_index = up_lane_index_start + j
                            down_lane_index = down_lane_index_start + j
                            up_end_x, up_end_y = upstream_mesolink.lane_geometry_xy_list[up_lane_index].coords[-1]
                            down_start_x, down_start_y = lane_geometry_xy_list[down_lane_index].coords[0]
                            dx, dy = up_end_x - down_start_x, up_end_y - down_start_y
                            if abs(dx) > 1e-9 or abs(dy) > 1e-9:
                                shifted = [(x + dx, y + dy) for (x, y) in lane_geometry_xy_list[down_lane_index].coords]
                                lane_geometry_xy_list[down_lane_index] = geometry.LineString(shifted)
            except Exception:
                pass

            number_of_cells = max(1, round(mesolink.length / self.length_of_cell))
            micronode_geometry_xy_list = [[lane_geometry_xy.interpolate(i/number_of_cells, normalized=True) for i in range(number_of_cells+1)] for lane_geometry_xy in lane_geometry_xy_list]
            micronode_geometry_xy_bike = [extra_bike_geometry_xy.interpolate(i / number_of_cells, normalized=True) for i in range(number_of_cells + 1)] if extra_bike_geometry_xy is not None else None
            micronode_geometry_xy_walk = [extra_walk_geometry_xy.interpolate(i / number_of_cells, normalized=True) for i in range(number_of_cells + 1)] if extra_walk_geometry_xy is not None else None

            for i in range(mesolink.lanes):
                micronode_list_lane = []
                for micronode_geometry_xy in micronode_geometry_xy_list[i]:
                    micronode = MicroNode(max_micronode_id)
                    micronode.geometry_xy = micronode_geometry_xy
                    micronode.geometry = self.macronet.GT.geo_to_latlon(micronode_geometry_xy)
                    micronode.mesolink = mesolink
                    micronode.lane_no = i + 1
                    micronode_list_lane.append(micronode)
                    self.micronet.node_dict[micronode.node_id] = micronode
                    max_micronode_id += 1
                mesolink.micronode_list.append(micronode_list_lane)

            # persist current lane centerlines for downstream anchoring
            mesolink.lane_geometry_xy_list = lane_geometry_xy_list

            if extra_bike:
                for micronode_geometry_xy in micronode_geometry_xy_bike:
                    micronode = MicroNode(max_micronode_id)
                    micronode.geometry_xy = micronode_geometry_xy
                    micronode.geometry = self.macronet.GT.geo_to_latlon(micronode_geometry_xy)
                    micronode.mesolink = mesolink
                    mesolink.micronode_bike.append(micronode)
                    self.micronet.node_dict[micronode.node_id] = micronode
                    max_micronode_id += 1

            if extra_walk:
                for micronode_geometry_xy in micronode_geometry_xy_walk:
                    micronode = MicroNode(max_micronode_id)
                    micronode.geometry_xy = micronode_geometry_xy
                    micronode.geometry = self.macronet.GT.geo_to_latlon(micronode_geometry_xy)
                    micronode.mesolink = mesolink
                    mesolink.micronode_walk.append(micronode)
                    self.micronet.node_dict[micronode.node_id] = micronode
                    max_micronode_id += 1

        first_mesolink = link.mesolink_list[0]
        for micronode_list_lane in first_mesolink.micronode_list:
            micronode_list_lane[0].is_link_upstream_end_node = True
        if extra_bike: first_mesolink.micronode_bike[0].is_link_upstream_end_node = True
        if extra_walk: first_mesolink.micronode_walk[0].is_link_upstream_end_node = True
        last_mesolink = link.mesolink_list[-1]
        for micronode_list_lane in last_mesolink.micronode_list:
            micronode_list_lane[-1].is_link_downstream_end_node = True
        if extra_bike: last_mesolink.micronode_bike[-1].is_link_downstream_end_node = True
        if extra_walk: last_mesolink.micronode_walk[-1].is_link_downstream_end_node = True

        for i in range(len(link.mesolink_list)-1):
            upstream_mesolink = link.mesolink_list[i]
            downstream_mesolink = link.mesolink_list[i+1]

            up_index_of_left_most_lane_of_original_link = upstream_mesolink.lanes_change[0]
            down_index_of_left_most_lane_of_original_link = downstream_mesolink.lanes_change[0]
            min_left_most_lane_index = min(up_index_of_left_most_lane_of_original_link, down_index_of_left_most_lane_of_original_link)
            up_lane_index_start = up_index_of_left_most_lane_of_original_link - min_left_most_lane_index
            down_lane_index_start = down_index_of_left_most_lane_of_original_link - min_left_most_lane_index

            number_of_connecting_lanes = min(upstream_mesolink.lanes-up_lane_index_start,
                                             downstream_mesolink.lanes-down_lane_index_start)

            for j in range(number_of_connecting_lanes):
                up_lane_index = up_lane_index_start + j
                down_lane_index = down_lane_index_start + j
                up_micronode = upstream_mesolink.micronode_list[up_lane_index][-1]
                down_micronode = downstream_mesolink.micronode_list[down_lane_index][0]
                upstream_mesolink.micronode_list[up_lane_index][-1] = down_micronode
                del self.micronet.node_dict[up_micronode.node_id]

            if extra_bike:
                up_micronode = upstream_mesolink.micronode_bike[-1]
                down_micronode = downstream_mesolink.micronode_bike[0]
                upstream_mesolink.micronode_bike[-1] = down_micronode
                del self.micronet.node_dict[up_micronode.node_id]
            if extra_walk:
                up_micronode = upstream_mesolink.micronode_walk[-1]
                down_micronode = downstream_mesolink.micronode_walk[0]
                upstream_mesolink.micronode_walk = down_micronode
                del self.micronet.node_dict[up_micronode.node_id]

        for mesolink in link.mesolink_list:
            for i in range(mesolink.lanes):
                for j in range(len(mesolink.micronode_list[i])-1):
                    microlink = MicroLink(self.micronet.max_link_id)
                    self.micronet.max_link_id += 1
                    microlink.from_node = mesolink.micronode_list[i][j]
                    microlink.to_node = mesolink.micronode_list[i][j+1]
                    microlink.geometry = geometry.LineString([microlink.from_node.geometry, microlink.to_node.geometry])
                    microlink.geometry_xy = geometry.LineString([microlink.from_node.geometry_xy, microlink.to_node.geometry_xy])
                    microlink.mesolink = mesolink
                    microlink.cell_type = 1
                    microlink.allowed_uses = mainlane_allowed_uses
                    self.micronet.link_dict[microlink.link_id] = microlink
                    microlink.from_node.outgoing_link_list.append(microlink)
                    microlink.to_node.incoming_link_list.append(microlink)

                if i <= mesolink.lanes - 2:
                    for j in range(len(mesolink.micronode_list[i])-1):
                        microlink = MicroLink(self.micronet.max_link_id)
                        self.micronet.max_link_id += 1
                        microlink.from_node = mesolink.micronode_list[i][j]
                        microlink.to_node = mesolink.micronode_list[i+1][j+1]
                        microlink.geometry = geometry.LineString([microlink.from_node.geometry, microlink.to_node.geometry])
                        microlink.geometry_xy = geometry.LineString([microlink.from_node.geometry_xy, microlink.to_node.geometry_xy])
                        microlink.mesolink = mesolink
                        microlink.cell_type = 2
                        microlink.allowed_uses = mainlane_allowed_uses
                        self.micronet.link_dict[microlink.link_id] = microlink
                        microlink.from_node.outgoing_link_list.append(microlink)
                        microlink.to_node.incoming_link_list.append(microlink)

                if i >= 1:
                    for j in range(len(mesolink.micronode_list[i])-1):
                        microlink = MicroLink(self.micronet.max_link_id)
                        self.micronet.max_link_id += 1
                        microlink.from_node = mesolink.micronode_list[i][j]
                        microlink.to_node = mesolink.micronode_list[i-1][j+1]
                        microlink.geometry = geometry.LineString([microlink.from_node.geometry, microlink.to_node.geometry])
                        microlink.geometry_xy = geometry.LineString([microlink.from_node.geometry_xy, microlink.to_node.geometry_xy])
                        microlink.mesolink = mesolink
                        microlink.cell_type = 2
                        microlink.allowed_uses = mainlane_allowed_uses
                        self.micronet.link_dict[microlink.link_id] = microlink
                        microlink.from_node.outgoing_link_list.append(microlink)
                        microlink.to_node.incoming_link_list.append(microlink)

            if extra_bike:
                for j in range(len(mesolink.micronode_bike) - 1):
                    microlink = MicroLink(self.micronet.max_link_id)
                    self.micronet.max_link_id += 1
                    microlink.from_node = mesolink.micronode_bike[j]
                    microlink.to_node = mesolink.micronode_bike[j + 1]
                    microlink.geometry = geometry.LineString([microlink.from_node.geometry, microlink.to_node.geometry])
                    microlink.geometry_xy = geometry.LineString([microlink.from_node.geometry_xy, microlink.to_node.geometry_xy])
                    microlink.mesolink = mesolink
                    microlink.cell_type = 1
                    microlink.allowed_uses = ['bike']
                    self.micronet.link_dict[microlink.link_id] = microlink
                    microlink.from_node.outgoing_link_list.append(microlink)
                    microlink.to_node.incoming_link_list.append(microlink)

            if extra_walk:
                for j in range(len(mesolink.micronode_walk) - 1):
                    microlink = MicroLink(self.micronet.max_link_id)
                    self.micronet.max_link_id += 1
                    microlink.from_node = mesolink.micronode_walk[j]
                    microlink.to_node = mesolink.micronode_walk[j + 1]
                    microlink.geometry = geometry.LineString([microlink.from_node.geometry, microlink.to_node.geometry])
                    microlink.geometry_xy = geometry.LineString([microlink.from_node.geometry_xy, microlink.to_node.geometry_xy])
                    microlink.mesolink = mesolink
                    microlink.cell_type = 1
                    microlink.allowed_uses = ['walk']
                    self.micronet.link_dict[microlink.link_id] = microlink
                    microlink.from_node.outgoing_link_list.append(microlink)
                    microlink.to_node.incoming_link_list.append(microlink)

        self.micronet.max_node_id = max(self.micronet.node_dict.keys()) + 1 if self.micronet.node_dict else 0
        self.micronet.max_link_id = max(self.micronet.link_dict.keys()) + 1 if self.micronet.link_dict else 0

    def createMesoNodeForCentriod(self):
        for node_id, node in self.macronet.node_dict.items():
            if node.is_centroid:
                if node not in self.number_of_expanded_mesonode.keys():
                    self.number_of_expanded_mesonode[node] = 0
                number_of_expanded_mesonode = self.number_of_expanded_mesonode[node]
                self.number_of_expanded_mesonode[node] += 1
                mesonode = MesoNode(node.node_id * 100 + number_of_expanded_mesonode)
                mesonode.geometry = node.geometry
                mesonode.geometry_xy = node.geometry_xy
                mesonode.macronode = node
                node.centroid_mesonode = mesonode
                self.mesonet.node_dict[mesonode.node_id] = mesonode

    def createNormalLinks(self):
        if og_settings.verbose:
            print('  generating normal meso links... (mrnet)')

        max_mesolink_id = self.mesonet.max_link_id

        for _, link in self.macronet.link_dict.items():
            macro_from_node = link.from_node
            if macro_from_node.is_centroid:
                upstream_node = macro_from_node.centroid_meso_node
            else:
                if macro_from_node not in self.number_of_expanded_mesonode.keys():
                    self.number_of_expanded_mesonode[macro_from_node] = 0
                number_of_expanded_mesonode = self.number_of_expanded_mesonode[macro_from_node]
                self.number_of_expanded_mesonode[macro_from_node] += 1

                upstream_node = MesoNode(macro_from_node.node_id * 100 + number_of_expanded_mesonode)
                upstream_node.geometry = geometry.Point(link.cutted_geometry_list[0].coords[0])
                upstream_node.geometry_xy = geometry.Point(link.cutted_geometry_xy_list[0].coords[0])
                upstream_node.macronode = macro_from_node

                self.mesonet.node_dict[upstream_node.node_id] = upstream_node

            cutted_number_of_segments = len(link.cutted_lanes_list)
            macro_to_node = link.to_node
            for section_no in range(cutted_number_of_segments):
                if macro_to_node.is_centroid and section_no == cutted_number_of_segments - 1:
                    downstream_node = macro_to_node.centroid_meso_node
                else:
                    if macro_to_node not in self.number_of_expanded_mesonode.keys():
                        self.number_of_expanded_mesonode[macro_to_node] = 0
                    number_of_expanded_mesonode = self.number_of_expanded_mesonode[macro_to_node]
                    self.number_of_expanded_mesonode[macro_to_node] += 1

                    downstream_node = MesoNode(macro_to_node.node_id * 100 + number_of_expanded_mesonode)
                    downstream_node.geometry = geometry.Point(link.cutted_geometry_list[section_no].coords[-1])
                    downstream_node.geometry_xy = geometry.Point(link.cutted_geometry_xy_list[section_no].coords[-1])
                    if section_no == cutted_number_of_segments - 1:
                        downstream_node.macronode = macro_to_node
                    else:
                        downstream_node.macrolink = link

                    self.mesonet.node_dict[downstream_node.node_id] = downstream_node

                mesolink = MesoLink(max_mesolink_id)
                mesolink.from_node = upstream_node
                mesolink.to_node = downstream_node
                mesolink.lanes = link.cutted_lanes_list[section_no]
                mesolink.lanes_change = link.cutted_lanes_change_list[section_no]
                mesolink.geometry = link.cutted_geometry_list[section_no]
                mesolink.geometry_xy = link.cutted_geometry_xy_list[section_no]
                mesolink.macrolink = link

                link.mesolink_list.append(mesolink)
                upstream_node.outgoing_link_list.append(mesolink)
                downstream_node.incoming_link_list.append(mesolink)

                self.mesonet.link_dict[mesolink.link_id] = mesolink
                max_mesolink_id += 1
                upstream_node = downstream_node

            if self.generate_micro_net:
                self.createMicroNetForNormalLink(link)

        self.mesonet.max_link_id = max_mesolink_id

    def connectMesoLinksMVMT(self):
        if og_settings.verbose:
            print('  generating movement meso links... (mrnet)')

        max_mesolink_id = self.mesonet.max_link_id

        for _, macronode in self.macronet.node_dict.items():
            for mvmt in macronode.movement_list:
                ib_link, ob_link = mvmt.ib_link, mvmt.ob_link
                ib_mesolink = ib_link.mesolink_list[-1]
                ob_mesolink = ob_link.mesolink_list[0]

                if macronode.movement_link_needed:
                    mesolink = MesoLink(max_mesolink_id)
                    mesolink.from_node = ib_mesolink.to_node
                    mesolink.to_node = ob_mesolink.from_node
                    mesolink.lanes = mvmt.lanes
                    mesolink.isconnector = True
                    mesolink.movement = mvmt
                    mesolink.macronode = macronode

                    mesolink.geometry = geometry.LineString([ib_mesolink.geometry.coords[-1], ob_mesolink.geometry.coords[0]])
                    mesolink.geometry_xy = geometry.LineString([ib_mesolink.geometry_xy.coords[-1], ob_mesolink.geometry_xy.coords[0]])

                    self.mesonet.link_dict[mesolink.link_id] = mesolink
                    max_mesolink_id += 1

                    mesolink.from_node.outgoing_link_list.append(mesolink)
                    mesolink.to_node.incoming_link_list.append(mesolink)
                    if self.generate_micro_net:
                        self.createMicroNetForConnector(mesolink, ib_mesolink, mvmt.start_ib_lane_seq_no, ob_mesolink, mvmt.start_ob_lane_seq_no)
                        # Group-wise alignment: off ramp vs on ramp with gradual transition
                        try:
                            affected = set()
                            # Off ramp (4->3+1): translate downstream first 6 nodes
                            if ib_mesolink.lanes >= ob_mesolink.lanes:
                                num_nodes_to_shift = min(self.num_nodes_for_ramp_alignment, len(ob_mesolink.micronode_list[0]) if ob_mesolink.micronode_list else 0)
                                for i_lane in range(mvmt.lanes):
                                    ib_idx = mvmt.start_ib_lane_seq_no + i_lane
                                    ob_idx = mvmt.start_ob_lane_seq_no + i_lane
                                    if ob_idx < 0 or ob_idx >= len(ob_mesolink.micronode_list):
                                        continue
                                    if ib_idx < 0 or ib_idx >= len(ib_mesolink.micronode_list):
                                        continue
                                    ib_end_node = ib_mesolink.micronode_list[ib_idx][-1]
                                    ob_lane_nodes = ob_mesolink.micronode_list[ob_idx]
                                    if not ob_lane_nodes:
                                        continue
                                    dx = ib_end_node.geometry_xy.x - ob_lane_nodes[0].geometry_xy.x
                                    dy = ib_end_node.geometry_xy.y - ob_lane_nodes[0].geometry_xy.y
                                    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
                                        continue
                                    # Gradual transition: first 6 nodes with decreasing ratio
                                    for idx in range(num_nodes_to_shift):
                                        if idx < len(ob_lane_nodes):
                                            n = ob_lane_nodes[idx]
                                            ratio = 1.0 - (idx / num_nodes_to_shift)
                                            n.geometry_xy = geometry.Point((n.geometry_xy.x + dx * ratio, n.geometry_xy.y + dy * ratio))
                                            n.geometry = self.macronet.GT.geo_to_latlon(n.geometry_xy)
                                            for lk in n.outgoing_link_list:
                                                affected.add(lk.link_id)
                                            for lk in n.incoming_link_list:
                                                affected.add(lk.link_id)
                            # On ramp (3+1->4): translate upstream last 6 nodes per-lane
                            else:
                                num_nodes_to_shift = min(self.num_nodes_for_ramp_alignment, len(ib_mesolink.micronode_list[0]) if ib_mesolink.micronode_list else 0)
                                for i_lane in range(mvmt.lanes):
                                    ib_lane_idx = mvmt.start_ib_lane_seq_no + i_lane
                                    ob_lane_idx = mvmt.start_ob_lane_seq_no + i_lane
                                    if ib_lane_idx < 0 or ib_lane_idx >= len(ib_mesolink.micronode_list):
                                        continue
                                    if ob_lane_idx < 0 or ob_lane_idx >= len(ob_mesolink.micronode_list):
                                        continue
                                    ib_lane_end = ib_mesolink.micronode_list[ib_lane_idx][-1]
                                    ob_lane_start = ob_mesolink.micronode_list[ob_lane_idx][0]
                                    lane_dx = ib_lane_end.geometry_xy.x - ob_lane_start.geometry_xy.x
                                    lane_dy = ib_lane_end.geometry_xy.y - ob_lane_start.geometry_xy.y
                                    if abs(lane_dx) < 1e-9 and abs(lane_dy) < 1e-9:
                                        continue
                                    lane_nodes = ib_mesolink.micronode_list[ib_lane_idx]
                                    lane_len = len(lane_nodes)
                                    for idx in range(num_nodes_to_shift):
                                        node_idx = lane_len - num_nodes_to_shift + idx
                                        if 0 <= node_idx < lane_len:
                                            n = lane_nodes[node_idx]
                                            ratio = (idx + 1) / num_nodes_to_shift
                                            n.geometry_xy = geometry.Point((n.geometry_xy.x - lane_dx * ratio, n.geometry_xy.y - lane_dy * ratio))
                                            n.geometry = self.macronet.GT.geo_to_latlon(n.geometry_xy)
                                            for lk in n.outgoing_link_list:
                                                affected.add(lk.link_id)
                                            for lk in n.incoming_link_list:
                                                affected.add(lk.link_id)
                            # Rebuild connector's intermediate nodes after alignment
                            # Both off ramp and on ramp need this, as endpoints have moved
                            if mesolink and mesolink.isconnector and hasattr(mesolink, 'micronode_list'):
                                for connector_lane_idx in range(len(mesolink.micronode_list)):
                                    if connector_lane_idx < mvmt.lanes:
                                        ob_lane_idx = mvmt.start_ob_lane_seq_no + connector_lane_idx
                                        ib_lane_idx = mvmt.start_ib_lane_seq_no + connector_lane_idx
                                        if (0 <= ob_lane_idx < len(ob_mesolink.micronode_list) and 
                                            0 <= ib_lane_idx < len(ib_mesolink.micronode_list)):
                                            connector_nodes = mesolink.micronode_list[connector_lane_idx]
                                            if len(connector_nodes) > 0:
                                                # Get new endpoint positions after alignment
                                                ib_end = ib_mesolink.micronode_list[ib_lane_idx][-1]
                                                ob_start = ob_mesolink.micronode_list[ob_lane_idx][0]
                                                # Rebuild connector geometry with new endpoints
                                                total_nodes = len(connector_nodes) + 2  # including start and end
                                                for idx, n in enumerate(connector_nodes):
                                                    # Interpolate between new start and end positions
                                                    t = (idx + 1) / total_nodes
                                                    new_x = ib_end.geometry_xy.x * (1 - t) + ob_start.geometry_xy.x * t
                                                    new_y = ib_end.geometry_xy.y * (1 - t) + ob_start.geometry_xy.y * t
                                                    n.geometry_xy = geometry.Point((new_x, new_y))
                                                    n.geometry = self.macronet.GT.geo_to_latlon(n.geometry_xy)
                                                    for lk in n.outgoing_link_list:
                                                        affected.add(lk.link_id)
                                                    for lk in n.incoming_link_list:
                                                        affected.add(lk.link_id)
                            for lid in affected:
                                ml = self.micronet.link_dict.get(lid)
                                if ml is not None:
                                    ml.geometry_xy = geometry.LineString([ml.from_node.geometry_xy, ml.to_node.geometry_xy])
                                    ml.geometry = geometry.LineString([ml.from_node.geometry, ml.to_node.geometry])
                        except Exception:
                            pass
                else:
                    if ib_link.downstream_is_target and not ob_link.upstream_is_target:
                        ib_mesolink_to_node = ib_mesolink.to_node
                        ob_mesolink_from_node = ob_mesolink.from_node
                        ob_mesolink.from_node = ib_mesolink_to_node
                        ob_mesolink.geometry = geometry.LineString([ib_mesolink.geometry.coords[-1]] + ob_mesolink.geometry.coords[1:])
                        ob_mesolink.geometry_xy = geometry.LineString([ib_mesolink.geometry_xy.coords[-1]] + ob_mesolink.geometry_xy.coords[1:])
                        del self.mesonet.node_dict[ob_mesolink_from_node.node_id]
                        if self.generate_micro_net:
                            for i in range(mvmt.lanes):
                                ib_lane_index = mvmt.start_ib_lane_seq_no + i
                                ob_lane_index = mvmt.start_ob_lane_seq_no + i
                                ib_mesolink_outgoing_micro_node = ib_mesolink.micronode_list[ib_lane_index][-1]
                                ob_mesolink_incoming_micro_node = ob_mesolink.micronode_list[ob_lane_index][0]
                                for microlink in ob_mesolink_incoming_micro_node.outgoing_link_list:
                                    microlink.from_node = ib_mesolink_outgoing_micro_node
                                del self.micronet.node_dict[ob_mesolink_incoming_micro_node.node_id]
                            # Group-wise alignment: off ramp vs on ramp
                            try:
                                affected = set()
                                if ib_mesolink.lanes >= ob_mesolink.lanes:
                                    num_nodes_to_shift = min(self.num_nodes_for_ramp_alignment, len(ob_mesolink.micronode_list[0]) if ob_mesolink.micronode_list else 0)
                                    for i_lane in range(mvmt.lanes):
                                        ib_idx = mvmt.start_ib_lane_seq_no + i_lane
                                        ob_idx = mvmt.start_ob_lane_seq_no + i_lane
                                        if ob_idx < 0 or ob_idx >= len(ob_mesolink.micronode_list):
                                            continue
                                        if ib_idx < 0 or ib_idx >= len(ib_mesolink.micronode_list):
                                            continue
                                        ib_end_node = ib_mesolink.micronode_list[ib_idx][-1]
                                        ob_lane_nodes = ob_mesolink.micronode_list[ob_idx]
                                        if not ob_lane_nodes:
                                            continue
                                        dx = ib_end_node.geometry_xy.x - ob_lane_nodes[0].geometry_xy.x
                                        dy = ib_end_node.geometry_xy.y - ob_lane_nodes[0].geometry_xy.y
                                        if abs(dx) < 1e-9 and abs(dy) < 1e-9:
                                            continue
                                        for idx in range(num_nodes_to_shift):
                                            if idx < len(ob_lane_nodes):
                                                n = ob_lane_nodes[idx]
                                                ratio = 1.0 - (idx / num_nodes_to_shift)
                                                n.geometry_xy = geometry.Point((n.geometry_xy.x + dx * ratio, n.geometry_xy.y + dy * ratio))
                                                n.geometry = self.macronet.GT.geo_to_latlon(n.geometry_xy)
                                                for lk in n.outgoing_link_list:
                                                    affected.add(lk.link_id)
                                                for lk in n.incoming_link_list:
                                                    affected.add(lk.link_id)
                                else:
                                    num_nodes_to_shift = min(self.num_nodes_for_ramp_alignment, len(ib_mesolink.micronode_list[0]) if ib_mesolink.micronode_list else 0)
                                    for i_lane in range(mvmt.lanes):
                                        ib_lane_idx = mvmt.start_ib_lane_seq_no + i_lane
                                        ob_lane_idx = mvmt.start_ob_lane_seq_no + i_lane
                                        if ib_lane_idx < 0 or ib_lane_idx >= len(ib_mesolink.micronode_list):
                                            continue
                                        if ob_lane_idx < 0 or ob_lane_idx >= len(ob_mesolink.micronode_list):
                                            continue
                                        ib_lane_end = ib_mesolink.micronode_list[ib_lane_idx][-1]
                                        ob_lane_start = ob_mesolink.micronode_list[ob_lane_idx][0]
                                        lane_dx = ib_lane_end.geometry_xy.x - ob_lane_start.geometry_xy.x
                                        lane_dy = ib_lane_end.geometry_xy.y - ob_lane_start.geometry_xy.y
                                        if abs(lane_dx) < 1e-9 and abs(lane_dy) < 1e-9:
                                            continue
                                        lane_nodes = ib_mesolink.micronode_list[ib_lane_idx]
                                        lane_len = len(lane_nodes)
                                        for idx in range(num_nodes_to_shift):
                                            node_idx = lane_len - num_nodes_to_shift + idx
                                            if 0 <= node_idx < lane_len:
                                                n = lane_nodes[node_idx]
                                                ratio = (idx + 1) / num_nodes_to_shift
                                                n.geometry_xy = geometry.Point((n.geometry_xy.x - lane_dx * ratio, n.geometry_xy.y - lane_dy * ratio))
                                                n.geometry = self.macronet.GT.geo_to_latlon(n.geometry_xy)
                                                for lk in n.outgoing_link_list:
                                                    affected.add(lk.link_id)
                                                for lk in n.incoming_link_list:
                                                    affected.add(lk.link_id)
                                for lid in affected:
                                    ml = self.micronet.link_dict.get(lid)
                                    if ml is not None:
                                        ml.geometry_xy = geometry.LineString([ml.from_node.geometry_xy, ml.to_node.geometry_xy])
                                        ml.geometry = geometry.LineString([ml.from_node.geometry, ml.to_node.geometry])
                            except Exception:
                                pass
                    elif not ib_link.downstream_is_target and ob_link.upstream_is_target:
                        ib_mesolink_to_node = ib_mesolink.to_node
                        ob_mesolink_from_node = ob_mesolink.from_node
                        ib_mesolink.to_node = ob_mesolink_from_node
                        ib_mesolink.geometry = geometry.LineString(ib_mesolink.geometry.coords[:-1] + [ob_mesolink.geometry.coords[0]])
                        ib_mesolink.geometry_xy = geometry.LineString(ib_mesolink.geometry_xy.coords[:-1] + [ob_mesolink.geometry_xy.coords[0]])
                        del self.mesonet.node_dict[ib_mesolink_to_node.node_id]
                        if self.generate_micro_net:
                            for i in range(mvmt.lanes):
                                ib_lane_index = mvmt.start_ib_lane_seq_no + i
                                ob_lane_index = mvmt.start_ob_lane_seq_no + i
                                ib_mesolink_outgoing_micro_node = ib_mesolink.micronode_list[ib_lane_index][-1]
                                ob_mesolink_incoming_micro_node = ob_mesolink.micronode_list[ob_lane_index][0]
                                for microlink in ib_mesolink_outgoing_micro_node.incoming_link_list:
                                    microlink.to_node = ob_mesolink_incoming_micro_node
                                del self.micronet.node_dict[ib_mesolink_outgoing_micro_node.node_id]
                            # Group-wise alignment: off ramp vs on ramp
                            try:
                                affected = set()
                                if ib_mesolink.lanes >= ob_mesolink.lanes:
                                    num_nodes_to_shift = min(self.num_nodes_for_ramp_alignment, len(ob_mesolink.micronode_list[0]) if ob_mesolink.micronode_list else 0)
                                    for i_lane in range(mvmt.lanes):
                                        ib_idx = mvmt.start_ib_lane_seq_no + i_lane
                                        ob_idx = mvmt.start_ob_lane_seq_no + i_lane
                                        if ob_idx < 0 or ob_idx >= len(ob_mesolink.micronode_list):
                                            continue
                                        if ib_idx < 0 or ib_idx >= len(ib_mesolink.micronode_list):
                                            continue
                                        ib_end_node = ib_mesolink.micronode_list[ib_idx][-1]
                                        ob_lane_nodes = ob_mesolink.micronode_list[ob_idx]
                                        if not ob_lane_nodes:
                                            continue
                                        dx = ib_end_node.geometry_xy.x - ob_lane_nodes[0].geometry_xy.x
                                        dy = ib_end_node.geometry_xy.y - ob_lane_nodes[0].geometry_xy.y
                                        if abs(dx) < 1e-9 and abs(dy) < 1e-9:
                                            continue
                                        for idx in range(num_nodes_to_shift):
                                            if idx < len(ob_lane_nodes):
                                                n = ob_lane_nodes[idx]
                                                ratio = 1.0 - (idx / num_nodes_to_shift)
                                                n.geometry_xy = geometry.Point((n.geometry_xy.x + dx * ratio, n.geometry_xy.y + dy * ratio))
                                                n.geometry = self.macronet.GT.geo_to_latlon(n.geometry_xy)
                                                for lk in n.outgoing_link_list:
                                                    affected.add(lk.link_id)
                                                for lk in n.incoming_link_list:
                                                    affected.add(lk.link_id)
                                else:
                                    num_nodes_to_shift = min(self.num_nodes_for_ramp_alignment, len(ib_mesolink.micronode_list[0]) if ib_mesolink.micronode_list else 0)
                                    for i_lane in range(mvmt.lanes):
                                        ib_lane_idx = mvmt.start_ib_lane_seq_no + i_lane
                                        ob_lane_idx = mvmt.start_ob_lane_seq_no + i_lane
                                        if ib_lane_idx < 0 or ib_lane_idx >= len(ib_mesolink.micronode_list):
                                            continue
                                        if ob_lane_idx < 0 or ob_lane_idx >= len(ob_mesolink.micronode_list):
                                            continue
                                        ib_lane_end = ib_mesolink.micronode_list[ib_lane_idx][-1]
                                        ob_lane_start = ob_mesolink.micronode_list[ob_lane_idx][0]
                                        lane_dx = ib_lane_end.geometry_xy.x - ob_lane_start.geometry_xy.x
                                        lane_dy = ib_lane_end.geometry_xy.y - ob_lane_start.geometry_xy.y
                                        if abs(lane_dx) < 1e-9 and abs(lane_dy) < 1e-9:
                                            continue
                                        lane_nodes = ib_mesolink.micronode_list[ib_lane_idx]
                                        lane_len = len(lane_nodes)
                                        for idx in range(num_nodes_to_shift):
                                            node_idx = lane_len - num_nodes_to_shift + idx
                                            if 0 <= node_idx < lane_len:
                                                n = lane_nodes[node_idx]
                                                ratio = (idx + 1) / num_nodes_to_shift
                                                n.geometry_xy = geometry.Point((n.geometry_xy.x - lane_dx * ratio, n.geometry_xy.y - lane_dy * ratio))
                                                n.geometry = self.macronet.GT.geo_to_latlon(n.geometry_xy)
                                                for lk in n.outgoing_link_list:
                                                    affected.add(lk.link_id)
                                                for lk in n.incoming_link_list:
                                                    affected.add(lk.link_id)
                                for lid in affected:
                                    ml = self.micronet.link_dict.get(lid)
                                    if ml is not None:
                                        ml.geometry_xy = geometry.LineString([ml.from_node.geometry_xy, ml.to_node.geometry_xy])
                                        ml.geometry = geometry.LineString([ml.from_node.geometry, ml.to_node.geometry])
                            except Exception:
                                pass
                    else:
                        sys.exit('Target link defintion error')

        self.mesonet.max_link_id = max_mesolink_id

    def generateNet(self):
        self.createMesoNodeForCentriod()
        self.createNormalLinks()
        self.connectMesoLinksMVMT()






