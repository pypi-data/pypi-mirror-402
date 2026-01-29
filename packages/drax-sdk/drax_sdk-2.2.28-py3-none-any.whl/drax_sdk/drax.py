from collections.abc import Callable
from typing import List, Any, Dict

from drax_sdk.broker.amqp_broker import DraxAmqpBroker
from drax_sdk.clients.drax_core_client import DraxCoreClient
from drax_sdk.clients.automation_client import AutomationClient
from drax_sdk.clients.data_miner_client import DataMinerClient
from drax_sdk.clients.alarms_client import AlarmsClient
from drax_sdk.model.config import DraxConfigParams
from drax_sdk.model.event import Event
from drax_sdk.model.node import NodeType, Node, State, Configuration
from drax_sdk.model.project import Project
from drax_sdk.model.automations import Automation
from drax_sdk.model.dto import (
    PagedResult,
    HandshakeRequest,
    HandshakeResponse,
    InstalledNode,
    FindNodeByIdsRequest,
    StateRequest,
    ConfigurationRequest,
    StateResponse,
    FlatConfigurationResponse,
    InstallRequest,
    PrepareRequest,
    # Automation models
    FindAutomationsRequest,
    FindUserActionsRequest,
    FindUserConditionsRequest,
    FindLogRequest,
    UserAction,
    UserCondition,
    LogEntry,
    # Alarm models
    Alarm,
    AlarmType,
    AlarmLogEntry,
    AcknowledgeAlarmRequest,
    ResolveAlarmRequest,
    FindAlarmLogEntriesRequest,
    FindAlarmTypesRequest,
    FindAlarmsRequest,
    # Data miner models
    DataRequest,
    DataResponse,
)
from drax_sdk.utils.codec import encode_state
from drax_sdk.utils.keystore import KeyStore


class DraxCore:

    client: DraxCoreClient
    config: DraxConfigParams

    def __init__(self, client: DraxCoreClient, config: DraxConfigParams):
        self.client = client
        self.config = config

    def register_node_type(self, node_type: NodeType) -> NodeType:
        return self.client.register_node_type(node_type)

    def update_node_type(self, node_type: NodeType) -> None:
        return self.client.update_node_type(node_type)

    def get_node_type_by_id(self, node_type_id: str) -> NodeType:
        return self.client.get_node_type_by_id(node_type_id)

    def unregister_node_type(self, node_type_id: str) -> None:
        self.client.unregister_node_type(node_type_id)

    # todo: da controllare perche il client non sembra avere parametri
    def list_node_types(self, project_id: str | None = None,) -> PagedResult[NodeType]:
        return self.client.list_node_types(project_id)

    def handshake(self, request: HandshakeRequest) -> HandshakeResponse:
        return self.client.handshake(request)

    def get_my_project(self) -> Project:
        return self.client.get_my_project()

    def get_project_by_id(self, id: str) -> Project:
        return self.client.get_project_by_id(id)

    def register_project(self, project: Project) -> Project:
        return self.client.register_project(project)

    def update_project(self, project: Project) -> None:
        self.client.update_project(project)

    def unregister_project(self, id: str) -> None:
        self.client.unregister_project(id)

    def prepare_node(self, request: PrepareRequest) -> InstalledNode:
        return self.client.prepare_node(request)

    def install_node(self, request: InstallRequest) -> InstalledNode:
        return self.client.install_node(request)

    # def generate_key_pair(self, request: ECDHKeysPairRequest) -> ECDHKeysPairResponse:
    #     return self.client.generate_keys_pair(request)
    #
    # def revoke_key_pair(self, request: ECDHRevokeRequest) -> ECDHRevokeResponse:
    #     return self.client.revoke_key(request)

    def update_node(self, node: Node) -> None:
        self.client.update_node(node)

    def uninstall_node(self, node_id: str) -> None:
        self.client.uninstall_node(node_id)

    def get_node_by_id(self, node_id: str) -> Node:
        return self.client.get_node_by_id(node_id)

    def get_nodes_by_ids(
        self, find_node_by_ids_request: FindNodeByIdsRequest
    ) -> List[Node]:
        return self.client.get_nodes_by_ids(find_node_by_ids_request)

    def list_projects(self, page: int = None, size: int = None) -> PagedResult[Project]:
        return self.client.list_projects()

    def list_nodes(
        self,
        project_id: str | None = None,
        keyword: str | None = None,
        page: int = 1,
        size: int = 10,
    ) -> PagedResult[Node]:
        return self.client.list_nodes(project_id, keyword, page, size)

    def list_states(
        self,
        node_id: str,
        project_id: str | None = None,
        from_time: int = None,
        to_time: int = None,
        page: int = 1,
        size: int = 10,
    ) -> PagedResult[StateResponse]:

        return self.client.list_states(
            node_id=node_id,
            project_id=project_id,
            from_time=from_time,
            to_time=to_time,
            page=page,
            size=size,
        )

    def list_configurations(
        self,
        node_id: str,
        from_time: int = None,
        to_time: int = None,
        page: int = 1,
        size: int = 10,
    ) -> PagedResult[FlatConfigurationResponse]:

        return self.client.list_configurations(
            node_id=node_id,
            from_time=from_time,
            to_time=to_time,
            page=page,
            size=size,
        )

    def list_nodes_states(
        self,
        find_node_by_ids_request: FindNodeByIdsRequest,
        start: int,
        end: int,
        page: int,
        size: int,
        project_id: str | None = None,
    ) -> PagedResult[StateResponse]:

        return self.client.list_nodes_states(
            project_id, find_node_by_ids_request, start, end, page, size
        )

    def set_state(self, node_id: str, state_request: StateRequest) -> None:
        self.client.set_state(node_id, state_request)

    def get_state(self, node_id: str) -> StateResponse:
        return self.client.get_state(node_id)

    def set_configuration(
        self, node_id: str, configuration_request: ConfigurationRequest
    ) -> None:
        # convert all values in str
        for key, value in configuration_request.configuration.items():
            configuration_request.configuration[key] = str(value)

        self.client.set_configuration(node_id, configuration_request)

    def invoke(self, event: Event) -> None:
        self.client.invoke(event)


class DraxAutomation:
    """Wrapper for AutomationClient following Java DraxAutomation pattern"""

    def __init__(self, client: AutomationClient):
        self.client = client

    def automate(
        self, activator_type: str, selector: str, data: dict = None
    ) -> None:
        self.client.automate(activator_type, selector, data)

    def delete(self, automation_id: str) -> None:
        self.client.delete(automation_id)

    def delete_user_action(self, user_action_id: str) -> None:
        self.client.delete_user_action(user_action_id)

    def delete_user_condition(self, user_condition_id: str) -> None:
        self.client.delete_user_condition(user_condition_id)

    def find(self, find_automations_request: FindAutomationsRequest) -> PagedResult[Automation]:
        return self.client.find(find_automations_request)

    def find_user_actions(
        self, find_user_actions_request: FindUserActionsRequest
    ) -> PagedResult[UserAction]:
        return self.client.find_user_actions(find_user_actions_request)

    def find_user_conditions(
        self, find_user_conditions_request: FindUserConditionsRequest
    ) -> PagedResult[UserCondition]:
        return self.client.find_user_conditions(find_user_conditions_request)

    def find_automation_log_entries(
        self, find_log_request: FindLogRequest
    ) -> PagedResult[LogEntry]:
        return self.client.find_logs(find_log_request)

    def get_actions(self, project_id: str) -> List[UserAction]:
        return self.client.get_actions(project_id)

    def get_by_id(self, automation_id: str) -> Automation:
        return self.client.get_by_id(automation_id)

    def get_conditions(self, project_id: str) -> List[UserCondition]:
        return self.client.get_conditions(project_id)

    def get_user_action_by_id(self, user_action_id: str) -> UserAction:
        return self.client.get_user_action_by_id(user_action_id)

    def get_user_condition_by_id(self, user_condition_id: str) -> UserCondition:
        return self.client.get_user_condition_by_id(user_condition_id)

    def save(self, automation: Automation) -> Automation:
        return self.client.save(automation)

    def save_user_action(self, user_action: UserAction) -> UserAction:
        return self.client.save_user_action(user_action)

    def save_user_condition(self, user_condition: UserCondition) -> UserCondition:
        return self.client.save_user_condition(user_condition)


class DraxDataMiner:
    """Wrapper for DataMinerClient following Java DraxDataMiner pattern"""

    def __init__(self, client: DataMinerClient):
        self.client = client

    def get_supported_aggregation_functions(self) -> List[str]:
        return self.client.get_supported_aggregation_functions()

    def get_supported_aggregation_periods(self) -> List[str]:
        return self.client.get_supported_aggregation_periods()

    def get_supported_time_windows(self) -> List[str]:
        return self.client.get_supported_time_windows()

    def fetch(self, request: DataRequest) -> DataResponse:
        return self.client.fetch(request)


class DraxAlarms:
    """Wrapper for AlarmsClient following Java DraxAlarms pattern"""

    def __init__(self, client: AlarmsClient):
        self.client = client

    def get_alarm_collection_strategy_types(self) -> List[str]:
        return self.client.get_alarm_collection_strategy_types()

    def get_alarm_scope_types(self) -> List[str]:
        return self.client.get_alarm_scope_types()

    def get_alarm_severity_types(self) -> List[str]:
        return self.client.get_alarm_severity_types()

    def get_alarm_status_types(self) -> List[str]:
        return self.client.get_alarm_status_types()

    def get_alarm_type_statuses(self) -> List[str]:
        return self.client.get_alarm_type_statuses()

    def acknowledge(self, acknowledge_alarm_request: AcknowledgeAlarmRequest) -> Alarm:
        return self.client.acknowledge(acknowledge_alarm_request)

    def delete(self, project_id: str, alarm_id: str) -> None:
        self.client.delete(project_id, alarm_id)

    def delete_alarm_type(self, alarm_type_id: str) -> None:
        self.client.delete_alarm_type(alarm_type_id)

    def find_alarm_log_entries(
        self, find_request: FindAlarmLogEntriesRequest
    ) -> PagedResult[AlarmLogEntry]:
        return self.client.find_alarm_log_entries(find_request)

    def find_alarm_types(self, find_alarm_types_request: FindAlarmTypesRequest) -> PagedResult[AlarmType]:
        return self.client.find_alarm_types(find_alarm_types_request)

    def find_alarms(self, find_alarms_request: FindAlarmsRequest) -> PagedResult[Alarm]:
        return self.client.find_alarms(find_alarms_request)

    def get_alarm(self, alarm_id: str) -> Alarm:
        return self.client.get_alarm(alarm_id)

    def get_alarm_type(self, alarm_type_id: str) -> AlarmType:
        return self.client.get_alarm_type(alarm_type_id)

    def resolve(self, resolve_alarm_request: ResolveAlarmRequest) -> Alarm:
        return self.client.resolve(resolve_alarm_request)

    def save_alarm_type(self, alarm_type: AlarmType) -> AlarmType:
        return self.client.save_alarm_type(alarm_type)


class Drax:
    def __init__(self, config: DraxConfigParams):
        self.config = config
        self.core = DraxCore(
            DraxCoreClient(config.drax_core_url, config.api_key, config.api_secret),
            config,
        )
        self.drax_automation = DraxAutomation(
            AutomationClient(config.automation_url, config.api_key, config.api_secret)
        )
        self.drax_data_miner = DraxDataMiner(
            DataMinerClient(config.data_miner_url, config.api_key, config.api_secret)
        )
        self.drax_alarms = DraxAlarms(
            AlarmsClient(config.alarms_url, config.api_key, config.api_secret)
        )
        self.broker = DraxAmqpBroker(config)

    def start(self):
        self.broker.start()
        pass

    def stop(self):
        self.broker.stop()
        pass

    def set_state(
        self,
        state: State | Dict[str, Any],
        node_id: str = None,
        cryptography_disabled=False,
        urn: str = None,
    ):
        if not isinstance(state, State):
            if node_id is None:
                raise ValueError("node_id must be provided")

        node_id = node_id if node_id else state.node_id
        if not node_id and not urn:
            raise ValueError("Either node_id or urn must be provided")

        node_private_key = KeyStore.get_private_key(node_id)
        
        # Get timestamp from state if it's a State object, otherwise use None
        timestamp = state.timestamp if isinstance(state, State) and hasattr(state, 'timestamp') else None

        request = StateRequest(
            node_id=node_id,
            state=encode_state(node_private_key, state),
            cryptography_disabled=cryptography_disabled,
            timestamp=timestamp,
            urn=urn,            
        )
        self.core.set_state(node_id, request)

    def set_configuration(
        self,
        configuration: Configuration | Dict[str, Any],
        node_id: str = None,
        cryptography_disabled=False,
        urn: str = None,
    ):
        if not isinstance(configuration, Configuration):
            if node_id is None:
                raise ValueError("node_id must be provided")

        node_id = node_id if node_id else configuration.node_id
        if not node_id and not urn:
            raise ValueError("Either node_id or urn must be provided")

        configuration_map = (
            configuration.to_map()
            if isinstance(configuration, Configuration)
            else configuration
        )

        self.core.set_configuration(
            node_id,
            ConfigurationRequest(
                node_id=node_id,
                configuration=configuration_map,
                cryptography_disabled=cryptography_disabled,
                urn=urn,
            ),
        )

    def add_configuration_listener(
        self, topic: str, listener: Callable[[Configuration], None]
    ):
        self.broker.add_configuration_listener(topic, listener)

    def add_state_listener(self, topic: str, listener: Callable[[State], None]):
        self.broker.add_state_listener(topic, listener)

    def add_events_listener(
        self, listener: Callable[[Event], None], project_id: str = None
    ):
        project_id = project_id or self.config.project_id
        if not project_id:
            raise ValueError("project_id is required")

        self.broker.add_event_listener(project_id=project_id, cb=listener)
