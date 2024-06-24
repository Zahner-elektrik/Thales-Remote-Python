import sys
import os

script_path = os.path.dirname(os.path.realpath(__file__))
if script_path not in sys.path:
    sys.path.append(script_path)

from thales_remote.connection import ThalesRemoteConnection
from thales_remote.script_wrapper import ThalesRemoteScriptWrapper


class ZenniumSingleton:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def init_zennium(self, target="localhost", connectionName="ScriptRemote"):
        self.zenniumConnection = ThalesRemoteConnection()
        self.zenniumConnection.connectToTerm(target, connectionName)
        self.zahnerZennium = ThalesRemoteScriptWrapper(self.zenniumConnection)
        self.zahnerZennium.forceThalesIntoRemoteScript()
        return

    def disconnect(self):
        return self.zenniumConnection.disconnectFromTerm()


zennium_instance = ZenniumSingleton()


def init(target="localhost", connectionName="ScriptRemote"):
    r"""
    This function connects to the Term Software and creates the ThalesRemoteScriptWrapper object.

    :param target: IP address of the computer on which the term is running, defaults to "localhost".
    :param connectionName: Name of the connection, defaults to "ScriptRemote".
    """
    global zennium_instance
    zennium_instance.init_zennium(target, connectionName)
    return


def disconnect():
    r"""
    Disconnect the connection.
    """
    global zennium_instance
    zennium_instance.disconnect()
    return


def _generate_function(method_name):
    r"""
    Helper function that creates functions from the object's methods.
    """

    def function(*args, **kwargs):
        zennium_method = getattr(zennium_instance.zahnerZennium, method_name)
        return zennium_method(*args, **kwargs)

    return function


def transformMethodsToFunctions():
    r"""
    After init() is called, the transformMethodsToFunctions() function must be called.

    init() creates the ThalesRemoteScriptWrapper object and transformMethodsToFunctions() converts the methods of this object into functions.
    Since the LabVIEW Python node can only execute functions from Python and not methods from objects.

    The functions are then in the global Python scope. This means that the same LabVIEW session must be used for all functions.

    Useful links from the LabVIEW documentation:

    * https://www.ni.com/docs/en-US/bundle/labview-api-ref/page/functions/python-node.html
    * https://knowledge.ni.com/KnowledgeArticleDetails?id=kA00Z0000019UFmSAM&l=en-US
    """
    for method_name in dir(zennium_instance.zahnerZennium):
        if not method_name.startswith("_") and method_name not in globals():
            globals()[method_name] = _generate_function(method_name)
    return
