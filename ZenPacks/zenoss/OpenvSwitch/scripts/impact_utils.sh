#!/bin/bash
##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

ZENOSS_URL=${ZENOSS_URL-"http://localhost:8080"}
ZENOSS_USERNAME=${ZENOSS_USERNAME-"admin"}
ZENOSS_PASSWORD=${ZENOSS_PASSWORD-"zenoss"}
ZENOSS_LOG=${ZENOSS_LOG-/tmp/tutorial.log}
ZENOSS_RESULTS=${ZENOSS_RESULTS-/tmp/last.log}

echo `date` > $ZENOSS_LOG

# Generic call to make Zenoss JSON API calls easier on the shell
zenoss_api () {
    local router_endpoint=$1
    local router_action=$2
    local router_method=$3
    local data=$4

    if [ -z "${data}" ]; then
        echo "Usage: zenoss_api <endpoint> <action> <method> <data>"
        return 1
    fi
    rm -f $ZENOSS_RESULTS
    curl -s \
        -u "$ZENOSS_USERNAME:$ZENOSS_PASSWORD" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "{\"action\":\"$router_action\",\"method\":\"$router_method\",\"data\":[$data], \"tid\":1}" \
        "$ZENOSS_URL/zport/dmd/$router_endpoint" \
        2>&1 | tee -a $ZENOSS_LOG > $ZENOSS_RESULTS
    echo >> /tmp/tutorial.log
}


# Helper to extract a string value from the most recent JSON response
#  returns the value associated with the input key
zenoss_extract_key () {
    local key="$1"
    local val=$(sed -n -e "s/.*\"$key\": \"\([^\"]*\)\".*/\1/p" $ZENOSS_RESULTS)
    echo $val
}


# Helper to check the status value of the most recent JSON response and exit
#  in case of non-success
zenoss_check_status() {
    status=$(sed -n -e "s/.*\"success\": \(false\|true\).*/\1/p" $ZENOSS_RESULTS)
    if [ "$status" != "true" ] ; then
        message="REST call returned non-true status:"\ $1
        shift
        for a in "$@" ; do message=$message\ \<$a\> ; done
        echo >&2 $message
        cat >&2 $ZENOSS_RESULTS
        echo >&2
        kill $$
    fi
}


# Helper to check that the number of arguments is expected and exit if not
zenoss_check_arg_count() {
    local expected=$1
    local usage=$2
    shift 2
    if [ $# -ne $expected ]; then
        echo >&2 Error: incorrect arguments: $usage
        message="Found"
        for a in "$@" ; do message=$message\ \<$a\> ; done
        echo >&2 $message
        kill $$
    fi
}


# Helper which if the argument is true, returns the argument quoted; else returns null
zenoss_string_or_null()
{
    if [ -z "$1" ]; then
        echo null
    else
        echo \"$1\"
    fi
}


# Helper which builds a state map string for use in zenoss_set_state_provider
# or zenoss_get_event_config
#   the arguments should either be empty strings or an appropriate
#   state_type for the policy type; e.g.,
#   for AVAILABILITY, one of (UP, DOWN, DEGRADED, ATRISK);
#   for PERFORMANCE one of (UNACCEPTABLE, DEGRADED, ACCEPTABLE)
zenoss_get_state_map() {
    echo "{\
        \"SEVERITY_CRITICAL\":$(zenoss_string_or_null $1),\
		\"SEVERITY_ERROR\":$(zenoss_string_or_null $2),\
		\"SEVERITY_WARNING\":$(zenoss_string_or_null $3),\
		\"SEVERITY_INFO\":$(zenoss_string_or_null $4),\
		\"SEVERITY_DEBUG\":$(zenoss_string_or_null $5),\
		\"SEVERITY_CLEAR\":$(zenoss_string_or_null $6) \
		}"
}


# Helper to create an event config string for use in zenoss_logical_node_set_info
zenoss_get_event_config() {
    zenoss_check_arg_count 2 "zenoss_get_event_config <event_class> <state_map>" "$@"
    local event_class="$1"
    local state_map="$2"
    echo "{ \
        \"eventClass\":\"$event_class\", \
        \"stateMap\":$state_map \
        }"
}


# Create a service organizer
#  returns: uid of the created organizer
zenoss_add_service_organizer () {
    zenoss_check_arg_count 2 "zenoss_add_service_organizer <base> <name>" "$@"
    local organizer_base="$1"
    local organizer_name="$2"

    zenoss_api enterpriseservices_router ImpactRouter addOrganizer \
        "{\"id\":\"$organizer_name\",
          \"contextUid\":\"/zport/dmd/DynamicServices$organizer_base\"}"

    zenoss_check_status zenoss_add_service_organizer "$@"
    zenoss_extract_key "uid"
}


# Create a service
#  returns: uid of the created service
zenoss_add_service () {
    zenoss_check_arg_count 2 "zenoss_add_service <organizer_uid> <name>" "$@"
    local service_base="$1"
    local service_name="$2"

    zenoss_api enterpriseservices_router ImpactRouter addNode \
        "{\"id\":\"$service_name\",
          \"contextUid\":\"/zport/dmd/DynamicServices$service_base\"}"

    zenoss_check_status zenoss_add_service "$@"
    zenoss_extract_key "uid"
}


# Add an impactor to a service
zenoss_add_to_dynamic_service () {
    zenoss_check_arg_count 2 "zenoss_add_to_dynamic_service <service_uid> <impactor_uid>" "$@"
    local service_uid="$1"
    local impactor_uid="$2"

    zenoss_api enterpriseservices_router ImpactRouter addToDynamicService \
        "{\"targetUid\":\"$service_uid\",
          \"uids\":[\"$impactor_uid\"]}"

    zenoss_check_status zenoss_add_to_dynamic_service "$@"
}


# Add a policy (context or global) to a service node
zenoss_add_policy () {
    zenoss_check_arg_count 8 "zenoss_add_policy <service_uid> <node_uid> <policy_type> <threshold> <trigger_type> <state> <dependant_state> <meta_types>" "$@"
    local service_uid="$1"        # Service for which to add policy; "global" implies global policy
    local node_uid="$2"           # Node to which policy is added
    local policy_type="$3"        # One of "AVAILABILITY", "PERFORMANCE"
    local threshold="$4"          # String representing integer value

    # One of "policyThresholdTrigger", "policyPercentageTrigger",
    #   "policyNegativeThresholdTrigger", "policyNegativePercentageTrigger"
    local trigger_type="$5"

    # Depending on the policy type, one of the following:
    #   Availability => DOWN, DEGRADED, ATRISK, UP
    #   Performance => UNACCEPTABLE, DEGRADED, ACCEPTABLE
    local state="$6"              # State which triggers policy
    local dependant_state="$7"    # State set as a result

    # Comma separated list of meta-types; common meta-types include
    # "Device", "DynamicService", "LogicalNode", "IpInterface", etc.
    local meta_types="$8"

    zenoss_api enterpriseservices_router ImpactRouter addStateTrigger \
        "{\"permissionUid\":\"$node_uid\",\
          \"contextUid\":\"$service_uid\",\
          \"uid\":\"$node_uid\",\
          \"policyType\":\"$policy_type\",\
          \"data\":{\
              \"dependentState\":\"$dependant_state\",\
              \"state\":\"$state\",\
              \"threshold\":\"$threshold\",\
              \"triggerType\":\"$trigger_type\",\
              \"metaTypes\":[$meta_types]\
            }\
        }"

    zenoss_check_status zenoss_add_policy "$@"
}


# Set a custom state provider for a node
zenoss_set_state_provider() {
    zenoss_check_arg_count 5 "zenoss_set_state_provider <node_uid> <state_type> <apply_to> <event_class> <state_map>" "$@"
    local node_uid="$1"
    local state_type="$2"     # One of "AVAILABILITY", "PERFORMANCE"
    local apply_to="$3"       # One of NODE, DEVICE, DEVICECLASS, ALL
    local event_class="$4"
    local state_map="$5"      # State map as generated by zenoss_state_map

    zenoss_api enterpriseservices_router ImpactRouter setStateProvider \
        "{\"uid\":\"$node_uid\",\
        \"stateType\":\"$state_type\",\
        \"applyTo\":\"$apply_to\",\
        \"eventClass\":\"$event_class\",\
        \"stateMap\":$STATE_MAP\
        }"

    zenoss_check_status zenoss_set_state_provider "$@"
}


# Delete service organizer or node
zenoss_delete_node() {
    zenoss_check_arg_count 1 "zenoss_delete_node <node_uid>" "$@"
    local node_uid="$1"
    zenoss_api enterpriseservices_router ImpactRouter deleteNode \
        "{\"uid\":\"$node_uid\"}"
    zenoss_check_status zenoss_delete_node "$@"
}


# Add a logical node organizer
#  returns: uid of created organizer
zenoss_add_logical_node_organizer () {
    zenoss_check_arg_count 2 "zenoss_add_logical_node_organizer <base> <name>" "$@"
    organizer_base="$1"
    organizer_name="$2"

    zenoss_api logicalnode_router LogicalNodeRouter addOrganizer \
        "{\"id\":\"$organizer_name\",\
          \"contextUid\":\"/zport/dmd/LogicalNodes$organizer_base\"}"

    zenoss_check_status zenoss_add_logical_node_organizer "$@"
    zenoss_extract_key "uid"
}


# Add a logical node
#  returns: uid of created node
zenoss_add_logical_node () {
    zenoss_check_arg_count 2 "zenoss_add_logical_node <organizer_uid> <node_name>" "$@"
    local organizer_uid="$1"
    local logical_node_name="$2"

    zenoss_api logicalnode_router LogicalNodeRouter addNode\
        "{\"id\":\"$logical_node_name\",\
          \"contextUid\":\"$organizer_uid\"}"

    zenoss_check_status zenoss_add_logical_node "$@"
    zenoss_extract_key "uid"
}


# Set the attributes of logical node
zenoss_logical_node_set_info() {
    zenoss_check_arg_count 5 "zenoss_logical_node_set_info <logical_node_uid> <criteria> <description> <availability_config> <performance_config>" "$@"
    local node_uid="$1"
    local criteria="$2"               # match-criteria string.
    local description="$3"            # empty string is valid, but arg is required
    local availability_config="$4"    # event config from zenoss_get_event_config
    local performance_config="$5"     # event config from zenoss_get_event_config

    zenoss_api logicalnode_router LogicalNodeRouter setInfo \
        "{\"uid\":\"$node_uid\", \
          \"description\":\"$description\", \
          \"criteria\":\"$criteria\", \
          \"availability_states\":$availability_config, \
          \"performance_states\":$performance_config \
          }"
    zenoss_check_status zenoss_add_logical_node "$@"
}


# Delete logical organizer or node
zenoss_delete_logical_node() {
    zenoss_check_arg_count 1 "zenoss_delete_node <logical_node_uid>" "$@"
    local node_uid="$1"

    zenoss_api logicalnode_router LogicalNodeRouter deleteNode \
        "{\"uid\":\"$node_uid\"}"

    zenoss_check_status zenoss_delete_node "$@"
}
