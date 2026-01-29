from abc import ABC
from typing import Literal, Optional
from pydantic import BaseModel
from ._internal.factory import ConversationalGraphEngine
from ._internal.tools import PreDefinedToolEngine, HttpReqTool
from ._internal.conversion import ConversationalGraphConversion


class ConversationalDataModel(BaseModel):
    """
    Public interface for Data Models for the Conversational Graph.
    """   
    pass


class ConversationalGraph(ABC):
    """
    Public interface for the Conversational Graph.
    """
    
    def __new__(cls, name: str, DataModel: ConversationalDataModel = None, off_topic_threshold: int = 5, graph_type: Literal["STRICT"] = "STRICT", conversation_data_file: Optional[str] = "conversation_data.json"):
        return ConversationalGraphEngine(name, DataModel, off_topic_threshold, graph_type, conversation_data_file)


class PreDefinedTool(ABC):
    """
    Public interface for PreDefined Tools in the Conversational Graph.
    """
    
    def __new__(cls):
        return PreDefinedToolEngine()


class HttpToolRequest(ABC):
    """
    Public interface for HTTP Tools Request in the Conversational Graph.
    """
    
    def __new__(cls, name:str, description:str, url:str, method:Literal["GET","POST"] = "GET", headers:Optional[dict] = None, params:Optional[dict] = None,payload:Optional[dict] = None):
        return HttpReqTool(name=name, description=description, url=url, method=method, headers=headers, params=params, payload=payload)


class Conversion(ABC):
    """
    Public interface for Conversion in the Conversational Graph.
    """
    
    def __new__(cls):
        return ConversationalGraphConversion()