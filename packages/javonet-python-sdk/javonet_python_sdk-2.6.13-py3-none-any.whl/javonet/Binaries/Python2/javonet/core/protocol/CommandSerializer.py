# -*- coding: utf-8 -*-
"""
The CommandSerializer module implements command serialization.
"""

import io

from javonet.core.protocol.TypeSerializer import TypeSerializer
from javonet.core.referenceCache.ReferencesCache import ReferencesCache
from javonet.utils.Command import Command
from javonet.utils.CommandType import CommandType
from javonet.utils.RuntimeName import RuntimeName
from javonet.utils.TypesHandler import TypesHandler
from javonet.utils.connectionData.IConnectionData import IConnectionData


class CommandSerializer(object):
    """
    Class responsible for command serialization.
    """

    @staticmethod
    def serialize(root_command, connection_data, runtime_version=0):
        """
        Serializes a command.

        :param root_command: Command to serialize
        :param connection_data: Connection data
        :param runtime_version: Runtime version
        :return: Serialized command as bytearray
        """
        ms = io.BytesIO()

        ms.write(bytearray([root_command.runtime_name.value, runtime_version]))

        if connection_data is not None:
            ms.write(bytearray(connection_data.serialize_connection_data()))
        else:
            ms.write(bytearray([0, 0, 0, 0, 0, 0, 0]))

        ms.write(bytearray([RuntimeName.python27.value, root_command.command_type.value]))

        CommandSerializer.serialize_recursively(root_command, ms)

        return list(bytearray(ms.getvalue()))

    @staticmethod
    def serialize_recursively(command, ms):
        """
        Serializes a command recursively.

        :param command: Command to serialize
        :param ms: BytesIO buffer to write to
        """
        for item in command.get_payload():
            if isinstance(item, Command):
                ms.write(bytearray(TypeSerializer.serialize_command(item)))
                CommandSerializer.serialize_recursively(item, ms)
            elif TypesHandler.is_primitive_or_none(item):
                ms.write(bytearray(TypeSerializer.serialize_primitive(item)))
            else:
                cached_reference = ReferencesCache().cache_reference(item)
                ref_command = Command(RuntimeName.python27, CommandType.Reference, cached_reference)
                ms.write(bytearray(TypeSerializer.serialize_command(ref_command)))
                CommandSerializer.serialize_recursively(ref_command, ms)
