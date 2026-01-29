"""ITL JSON mapping with EPS format."""

from ...misc import fmt_datetime

EPS_MAPPING_OBS = {
    'OBS_KEY': ('name', str),
    't_start': ('start_time', fmt_datetime),
    't_end': ('end_time', fmt_datetime),
    'TYPE': ('type', str),
    'OBSERVATION_TYPE': ('observation_type', str),
    'INSTRUMENT': ('instrument', str),
    'OBS_NAME': ('unique_id', str),
    'TARGET': ('target', str),
    'COMMENTS': ('comment', str),
}

# Temporary patch with explicit list from SOC v2 schema (see !10, !12 and !13)
EPS_MAPPING_OBS_EXTRA = {
    'STACK': ('stack', str),
    'MODE': ('mode', str),
    'POINTING': ('pointing', str),
    'POINTING_DESCRIPTION': ('pointing_description', str),
    'POINTING_DESIGNER': ('pointing_designer', bool),
    'DESCRIPTION': ('description', str),
    'SCHEDULING_RULES': ('scheduling_rules', str),
    'POWER_PROFILE': ('power_profile', dict),
    'DATA_RATE_PROFILE': ('data_rate_profile', dict),
    'DATA_VOLUME_PROFILE': ('data_volume_profile', dict),
    'INSTRUMENT_AREA': ('instrument_area', dict),
}

EPS_MAPPING_PARAMS = {
    'SCENARIO': ('scenario_id', str),
    'CU_TREP': (
        'cu_trep_ms',
        lambda v: int(str(v).replace('ms', '')),
    ),
    'CU_FRAME': ('nb_cu_frames_tot', int),
    'BINNING': ('spatial_binning', int),
    'PPE': ('ppe', int),
    'START_ROW_VIS': ('start_row_vi', int),
    'START_ANGLE': ('start_angle', float),
    'STOP_ANGLE': ('stop_angle', float),
    'SYNCHRONOUS': ('scanner_step_per_frame', int),
    'START_SCAN_SPEED': ('start_scan_speed', float),
    'STOP_SCAN_SPEED': ('stop_scan_speed', float),
}

JSON_MAPPING = {
    json: eps for eps, (json, _) in (EPS_MAPPING_OBS | EPS_MAPPING_PARAMS).items()
}
