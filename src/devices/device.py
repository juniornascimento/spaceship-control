
import shlex

from abc import ABC, abstractmethod

class Device(ABC):

    @abstractmethod
    def act(self) -> None:
        pass

    @abstractmethod
    def communicate(self, input_: str) -> str:
        pass

class CommandCommunicationDevice(Device):

    def communicate(self, input_: str) -> str:

        try:
            return str(self.command(shlex.split(input_)))
        except ValueError:
            return 'Invalid command'

    @abstractmethod
    def command(self, command: 'List[str]') -> 'Any':
        pass

class DefaultDevice(CommandCommunicationDevice):

    def __init__(self, device_type: str = 'none',
                 device_desc: str = 'not specified',
                 device_info: 'Dict[str, str]' = None):

        self.__device_type = device_type
        self.__device_desc = device_desc

        if device_info is None:
            self.__device_info = {}
        else:
            self.__device_info = device_info.copy()

    def setInfo(self, name: str, value: 'Optional[str]') -> None:
        if value is None:
            try:
                del self.__device_info[name]
            except KeyError:
                pass
        else:
            self.__device_info[name] = value

    def getInfo(self, name: str) -> 'Optional[str]':
        return self.__device_info.get(name)

    def deviceType(self) -> str:
        return self.__device_type

    def deviceDescription(self) -> str:
        return self.__device_desc

    def __command(self, command: 'List[str]',
                  command_actions: 'Dict[str, Callable]') -> 'Any':

        if not command:
            return None

        command_func = command_actions.get(command[0])

        if command_func is None:
            return None

        try:
            command_args = iter(command)
            next(command_args)
            return command_func(self, *command_args)
        except Exception:
            return 'An error ocurred running the command'

    def command(self, command: 'List[str]',
                *args: 'Dict[str, Callable]') -> 'Any':

        for command_actions in args:

            if command_actions is not None:

                result = self.__command(command, command_actions)
                if result is not None:
                    return result

        result = self.__command(command, DefaultDevice.__COMMANDS)

        if result is None:
            return 'Invalid command'

        return result

    __COMMANDS = {

        'device-type': deviceType,
        'device-desc': deviceDescription,
        'get-info': lambda self, name: self.getInfo(name) or '<<null>>'
    }

class DeviceGroup(DefaultDevice):

    def __init__(self, device_type: str = 'device-group', **kwargs):
        super().__init__(device_type=device_type, **kwargs)

        self.__device_list: 'List[Device]' = []
        self.__device_dict: 'Dict[str, Device]' = {}

        self.setInfo('is-device-group', 'yes')

    def addDevice(self, device: Device, name: str = None):

        self.__device_list.append(device)
        if name is not None:
            self.__device_dict[name] = device
            if isinstance(device, DefaultDevice):
                device.setInfo('device-name-in-group', name)

    def deviceCount(self):
        return len(self.__device_list)

    def act(self) -> None:
        for device in self.__device_list:
            device.act()

    def communicate(self, input_: str) -> str:

        sp_input = input_.split(':', 1)

        if len(sp_input) == 2:
            device_id = sp_input[0]
            try:
                device_number = int(device_id)
            except ValueError:
                device = self.__device_dict.get(device_id)
            else:
                if device_number < 0 or device_number >= self.deviceCount():
                    return f'Error: Invalid device \'{device_number}\''

                device = self.__device_list[device_number]

            if device is None:
                return 'Invalid device'

            return device.communicate(sp_input[1])

        return super().communicate(input_)

    def command(self, command: 'List[str]') -> 'Any':
        return super().command(command, DeviceGroup.__COMMANDS)

    __COMMANDS = {

        'device-count': deviceCount
    }

class PropertyDevice(DefaultDevice):

    def __init__(self,
                 properties: 'Dict[str, property]' = None,
                 **kwargs: 'Any') -> None:
        super().__init__(**kwargs)

        self.__properties = {} if properties is None else properties.copy()

    def getProperty(self, prop_name: str) -> 'Any':
        prop = self.__properties.get(prop_name)
        if prop is None:
            return '<<Unknown property>>'

        return prop.fget(self)

    def setProperty(self, prop_name: str, val: 'Any') -> 'Any':
        prop = self.__properties.get(prop_name)
        if prop is None:
            return '<<Unknown property>>'

        setter = prop.fset

        if setter is None:
            return '<<This property can\'t be set>>'

        setter(self, val)

        return '<<OK>>'

    def properties(self) -> 'Iterable[Tuple[str, Any]]':
        return self.__properties.items()

    def __listPropertiesStr(self) -> str:
        return ':'.join(key for key, _ in self.properties),

    def __showPropertiesStr(self) -> str:
        return ':'.join(f'{key}={val}' for key, val in self.properties)

    def command(self, command: 'List[str]',
                *args: 'Dict[str, Callable]') -> 'Any':
        return super().command(command, PropertyDevice.__COMMANDS, *args)

    __COMMANDS = {

        'set-property': setProperty,
        'get-property': getProperty,
        'list-properties': __listPropertiesStr,
        'show-properties': __showPropertiesStr
    }
