import collections

FieldRaw = collections.namedtuple("FieldRaw", "name value")
MediaField = collections.namedtuple("MediaField", "media port number_of_ports proto fmt")
OriginField = collections.namedtuple(
    "OriginField", "username session_id session_type nettype addrtype unicast_address"
)
TimingField = collections.namedtuple("TimingField", "start_time stop_time")
RepeatTimesField = collections.namedtuple(
    "RepeatTimesField", "repeat_interval active_duration offsets"
)
TimeDescription = collections.namedtuple("TimeDescription", "timing repeat_times")
MediaDescription = collections.namedtuple(
    "MediaDescription",
    "media media_title connection_information bandwidth_information encryption_key media_attributes",
)
ConnectionDataField = collections.namedtuple(
    "ConnectionDataField", "net_type addr_type connection_address"
)
