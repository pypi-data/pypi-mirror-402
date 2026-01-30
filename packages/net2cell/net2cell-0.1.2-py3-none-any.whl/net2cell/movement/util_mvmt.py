import math
from shapely import geometry

_indent = 8.0


def getMovementDescription(ib_link, ob_link):
    ib_coords = list(ib_link.geometry_xy.coords)
    ob_coords = list(ob_link.geometry_xy.coords)
    
    # Direction should be based on link END (approaching junction), not start
    # Use local direction at link end (last few points) to handle curved links
    ib_end = ib_coords[-1]
    if len(ib_coords) >= 3:
        # Use direction from third-to-last point to last point
        ib_direction_start = ib_coords[-3]
    else:
        ib_direction_start = ib_coords[0]

    angle_ib = math.atan2(ib_end[1] - ib_direction_start[1], ib_end[0] - ib_direction_start[0])
    if -0.75 * math.pi <= angle_ib < -0.25 * math.pi:
        direction = 'SB'
    elif -0.25 * math.pi <= angle_ib < 0.25 * math.pi:
        direction = 'EB'
    elif 0.25 * math.pi <= angle_ib < 0.75 * math.pi:
        direction = 'NB'
    else:
        direction = 'WB'

    # For turn angle, use local directions at the junction
    # ib_link: direction at end (last few points)
    ib_end = ib_coords[-1]
    if len(ib_coords) >= 3:
        ib_end_direction_point = ib_coords[-3]
    else:
        ib_end_direction_point = ib_coords[0]
    
    # ob_link: direction at start (first few points)
    ob_start = ob_coords[0]
    if len(ob_coords) >= 3:
        ob_start_direction_point = ob_coords[2]
    else:
        ob_start_direction_point = ob_coords[-1]
    
    angle_ib_end = math.atan2(ib_end[1] - ib_end_direction_point[1], ib_end[0] - ib_end_direction_point[0])
    angle_ob_start = math.atan2(ob_start_direction_point[1] - ob_start[1], ob_start_direction_point[0] - ob_start[0])
    angle = angle_ob_start - angle_ib_end
    if angle < -1 * math.pi:
        angle += 2 * math.pi
    if angle > math.pi:
        angle -= 2 * math.pi

    if -0.25 * math.pi <= angle <= 0.25 * math.pi:
        mvmt = 'T'
        mvmt_type = 'thru'
    elif angle < -0.25 * math.pi:
        mvmt = 'R'
        mvmt_type = 'right'
    elif angle <= 0.75 * math.pi:
        mvmt = 'L'
        mvmt_type = 'left'
    else:
        mvmt = 'U'
        mvmt_type = 'uturn'

    mvmt_txt_id = direction + mvmt
    return mvmt_txt_id, mvmt_type


def getMovementGeometry(ib_link, ob_link):
    ib_geometry_xy = ib_link.geometry_xy
    ib_indent = _indent if ib_geometry_xy.length > _indent else ib_geometry_xy.length / 2
    ib_point = ib_geometry_xy.interpolate(-1 * ib_indent)

    ob_geometry_xy = ob_link.geometry_xy
    ob_indent = _indent if ob_geometry_xy.length > _indent else ob_geometry_xy.length / 2
    ob_point = ob_geometry_xy.interpolate(ob_indent)

    geometry_xy = geometry.LineString([ib_point, ob_point])
    return geometry_xy



