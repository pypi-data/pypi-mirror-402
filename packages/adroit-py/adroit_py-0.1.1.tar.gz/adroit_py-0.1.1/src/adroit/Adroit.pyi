from typing import Any, List, Optional
from datetime import datetime

class Adroit:
    """def AlarmTag(self, Agent: str, AlarmAgent: str, Type: str, Route: int, Ack: int, TypeEnum: int) -> Any:"""
    """Configure or remove an alarm for an agent/tag.

    Args:
        Agent: Agent name or "agent.slot".
        AlarmAgent: Alarm handler name.
        Type: Alarm type name (use TypeEnum if empty).
        Route: Alarm route number. Use -1 to delete the alarm.
        Ack: 1 if alarm must be acknowledgeable, else 0.
        TypeEnum: Numeric type enum (use -1 when Type is provided).

    Returns:
        Any: COM/driver result object (implementation-specific).

    Raises:
        RuntimeError: on failure.
    """
    def Connect(self, Computer: Optional[str], Server: Optional[str]) -> Any:
        """Connect to an Agent Server.

        Args:
            Computer: Remote computer name (None or empty for local).
            Server: Agent Server name.

        Returns:
            Any: Connection result/object.

        Raises:
            ConnectionError: if the connection fails.
        """
    """ def CreateAgent(self, Name: str, Description: Optional[str], Type: Optional[str]) -> Any:"""
    """Create a new agent on the connected server.

    Args:
        Name: Agent name.
        Description: Optional description.
        Type: Optional agent type.

    Returns:
        Any: Result object or success indicator.

    Raises:
        RuntimeError: on failure.
    """
    def Fetch(self, Agent: str, Slot: str) -> Any:
        """Read a tag/slot value.

        Args:
            Agent: Agent name or "agent.slot".
            Slot: Slot name (ignored if Agent includes a slot).

        Returns:
            Any: Python-native type depending on slot:
                - bool for BOOLEAN
                - int for INTEGER
                - float for REAL
                - str for STRING/TAGNAME/VARSTRING
                - datetime for TIME
                - list for LIST (list[str] or similar)
        """
    def FetchChanges(self, AgentSlot: str, Start: Any, End: Any) -> List[List[Any]]:
        """Retrieve logged changes for an agent.slot.

        Args:
            AgentSlot: "agent.slot" to query.
            Start: Start time (datetime or string accepted).
            End: End time (datetime or string accepted).

        Returns:
            List[List[Any]]: Rows of [timestamp(datetime), value, integrity_flag(int)].
            integrity_flag: 1=NORMAL, 4=LAST LOGGED, 5=POST STARTUP, 6=BAD
        """
    def FetchValues(self, AgentSlot: str, Start: Any, End: Any, Samples: Any) -> List[List[Any]]:
        """Retrieve interpolated logged values.

        Args:
            AgentSlot: "agent.slot" to query.
            Start: Start time.
            End: End time.
            Samples: Number of samples to return.

        Returns:
            List[List[Any]]: Rows of [timestamp(datetime), interpolated_value].
        """
    def GetSlotInfo(self, Agent: str) -> List[List[Any]]:
        """Get slot metadata for an agent.

        Args:
            Agent: Agent name.

        Returns:
            List[List[Any]]: Rows of [slot_name(str), description(str), type_no(int)].
            Type numbers:
                0=BOOLEAN, 1=INTEGER, 2=REAL, 3=STRING, 4=TIME, 5=TAGNAME, 6=AGENTID,
                7=RAWBYTES, 8=LIST, 9=AGENT, 10=VARSTRING, 11=HEADER
        """
    """def Join(self, Group: str, MemberList: Optional[str]) -> Any:"""
    """Add agents to a group.

    Args:
        Group: Group name.
        MemberList: Comma-separated agent names.

    Returns:
        Any: Result object.
    """
    """def Leave(self, Group: str, MemberList: Optional[str]) -> Any:"""
    """Remove agents from a group.

    Args:
        Group: Group name.
        MemberList: Comma-separated agent names.

    Returns:
        Any: Result object.
    """
    """def LogTag(self, Agent: str, Slot: str, Set: int, Period: int, Rate: int, Filename: Optional[str]) -> Any:"""
    """Configure historical logging for an agent or tag.

    Args:
        Agent: Agent or "agent.slot".
        Slot: Slot name (ignored if Agent contains slot).
        Set: Logging set number.
        Period: Log period (hours).
        Rate: Minimum logging interval (seconds).
        Filename: Optional path to datalog file.
    
    Note:
        To delete the historical data logging for this Adroit tag, use the RemoveAgent function and specify the following name: "LOG$Agent$Slot", where Agent, is the specified Agent name and Slot is the specified slot that was logged. For instance, to remove the logging for the example above, type the following: p = adroit.RemoveAgent("LOG$ANA-01$rawValue")

    Returns:
        Any: Result object.
    """
    """def RemoveAgent(self, Name: str) -> Any:"""
    """Remove an agent from the connected server.

    Args:
        Name: Agent name.

    Returns:
        Any: Result object.
    """
    """def ScanTag(self, Agent: str, Slot: str, Device: Optional[str], Address: Optional[str], Rate: int, Deadband: int, OutputEnable: int) -> Any:"""
    """Configure scanning for a tag/agent slot.

    Args:
        Agent: Agent or "agent.slot".
        Slot: Slot name (ignored if Agent contains slot).
        Device: Device agent name (front-end).
        Address: Scan address (protocol-specific).
        Rate: Scan period in ms (use negative rate to unscan).
        Deadband: Deadband in units.
        OutputEnable: 1 to mark point as output, else 0.

    Returns:
        Any: Result object.
    """
class AdroitOLE(Adroit):    
    def FetchTags(self, tag_names: list[str]) -> dict[str, Any]: ...    
    def SetTag(self, Agent: str, Slot: str, value: Any) -> Any: ...
    def SetTag(self, tag_values: dict[str, Any]) -> dict[str, Any]: ...

adroit: AdroitOLE