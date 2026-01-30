"""
Asterisk Manager Interface (AMI) Client

A modern AMI client for Python 3.10+ with both async and sync interfaces.
The async client uses modern asyncio patterns without deprecated parameters.
The sync wrapper allows use in threaded/gevent environments.
"""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Awaitable, Callable

if TYPE_CHECKING:
    pass

EOL = "\r\n"
EOM = EOL + EOL  # End of message


@dataclass
class AMIResponse:
    """
    Represents a response from the AMI server.

    Attributes:
        raw: The raw response string from the server
        action_id: The ActionID that was sent with the request
        response: The Response header value (Success, Error, etc.)
        message: The Message header value if present
        data: Dictionary of all key-value pairs from the response
        output: List of Output lines (for Command actions)
    """

    raw: str
    action_id: str = ""
    response: str = ""
    message: str = ""
    data: dict[str, str] = field(default_factory=dict)
    output: list[str] = field(default_factory=list)

    @classmethod
    def from_raw(cls, raw: str) -> AMIResponse:
        """Parse raw AMI response into structured data."""
        lines = raw.strip().split(EOL)
        data: dict[str, str] = {}
        output: list[str] = []

        for line in lines:
            if ": " in line:
                key, value = line.split(": ", 1)
                if key == "Output":
                    output.append(value)
                else:
                    data[key] = value
            elif line.startswith("--"):
                continue

        return cls(
            raw=raw,
            action_id=data.get("ActionID", ""),
            response=data.get("Response", ""),
            message=data.get("Message", ""),
            data=data,
            output=output,
        )

    @property
    def success(self) -> bool:
        """Check if the response indicates success."""
        return self.response.lower() == "success"


class AMIError(Exception):
    """
    Exception raised for AMI errors.

    Attributes:
        response: The AMIResponse that caused the error, if available
    """

    def __init__(self, message: str, response: AMIResponse | None = None) -> None:
        super().__init__(message)
        self.response = response


class AsyncAMIClient:
    """
    Asynchronous Asterisk Manager Interface client.

    Modern asyncio implementation for Python 3.10+ without deprecated patterns.

    Example:
        async with AsyncAMIClient("localhost", 5038, "admin", "secret") as ami:
            response = await ami.command("core show version")
            print(response.output)

            # Execute multiple commands
            await ami.command("dialplan reload")
            await ami.command("sip reload")

    Args:
        host: Asterisk server hostname or IP address
        port: AMI port (default: 5038)
        username: AMI username
        secret: AMI password/secret
        timeout: Connection and read timeout in seconds (default: 10.0)
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5038,
        username: str = "",
        secret: str = "",
        timeout: float = 10.0,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.secret = secret
        self.timeout = timeout
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._connected = False
        self._authenticated = False

    async def __aenter__(self) -> AsyncAMIClient:
        await self.connect()
        await self.login()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if self._authenticated:
            try:
                await self.logoff()
            except Exception:
                pass
        await self.disconnect()

    @property
    def connected(self) -> bool:
        """Return True if connected to the AMI server."""
        return self._connected

    @property
    def authenticated(self) -> bool:
        """Return True if authenticated with the AMI server."""
        return self._authenticated

    async def connect(self) -> None:
        """
        Establish TCP connection to AMI server.

        Raises:
            AMIError: If connection fails or times out
        """
        if self._connected:
            return

        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout,
            )
            # Read the initial banner (e.g., "Asterisk Call Manager/6.0.0")
            await self._read_until(EOL)
            self._connected = True
        except asyncio.TimeoutError:
            raise AMIError(f"Connection timeout to {self.host}:{self.port}")
        except OSError as e:
            raise AMIError(f"Failed to connect to {self.host}:{self.port}: {e}")

    async def disconnect(self) -> None:
        """Close the connection to the AMI server."""
        if self._writer:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
            self._writer = None
            self._reader = None
        self._connected = False
        self._authenticated = False

    async def login(self) -> AMIResponse:
        """
        Authenticate with the AMI server.

        Returns:
            AMIResponse from the login action

        Raises:
            AMIError: If not connected or authentication fails
        """
        if not self._connected:
            raise AMIError("Not connected")

        response = await self.send_action(
            {"Action": "Login", "Username": self.username, "Secret": self.secret}
        )

        if not response.success:
            raise AMIError(
                f"Authentication failed: {response.message}", response=response
            )

        self._authenticated = True
        return response

    async def logoff(self) -> AMIResponse:
        """
        Log off from the AMI server.

        Returns:
            AMIResponse from the logoff action
        """
        response = await self.send_action({"Action": "Logoff"})
        self._authenticated = False
        return response

    async def send_action(
        self,
        action: dict[str, Any],
        callback: Callable[[dict[str, str]], Awaitable[None] | None] | None = None,
    ) -> AMIResponse:
        """
        Send an action to the AMI server and wait for response.

        Args:
            action: Dictionary containing the action and its parameters.
                    Must include an "Action" key. ActionID is auto-generated
                    if not provided.
            callback: Optional callback function (sync or async) to call
                     with the response data dictionary.

        Returns:
            AMIResponse object containing the server's response

        Raises:
            AMIError: If not connected or send/receive fails

        Example:
            response = await ami.send_action({
                "Action": "Originate",
                "Channel": "SIP/1000",
                "Context": "default",
                "Exten": "1001",
                "Priority": "1",
            })
        """
        if not self._connected:
            raise AMIError("Not connected")

        if "ActionID" not in action:
            action["ActionID"] = str(uuid.uuid4())

        message = self._build_message(action)
        await self._send(message)

        response = await self._read_response(action["ActionID"])

        if callback:
            result = callback(response.data)
            if asyncio.iscoroutine(result):
                await result

        return response

    async def command(self, command: str) -> AMIResponse:
        """
        Execute an Asterisk CLI command.

        Args:
            command: The CLI command to execute (e.g., "core show version")

        Returns:
            AMIResponse with command output in the 'output' field

        Example:
            response = await ami.command("sip show peers")
            for line in response.output:
                print(line)
        """
        return await self.send_action({"Action": "Command", "Command": command})

    async def database_put(self, family: str, key: str, value: str) -> AMIResponse:
        """
        Store a value in the Asterisk database (AstDB).

        Args:
            family: Database family
            key: Database key
            value: Value to store

        Returns:
            AMIResponse from the command
        """
        return await self.command(f'database put {family} {key} "{value}"')

    async def database_get(self, family: str, key: str) -> AMIResponse:
        """
        Retrieve a value from the Asterisk database (AstDB).

        Args:
            family: Database family
            key: Database key

        Returns:
            AMIResponse from the command
        """
        return await self.send_action(
            {"Action": "DBGet", "Family": family, "Key": key}
        )

    async def database_del(self, family: str, key: str) -> AMIResponse:
        """
        Delete a key from the Asterisk database (AstDB).

        Args:
            family: Database family
            key: Database key

        Returns:
            AMIResponse from the command
        """
        return await self.command(f"database del {family} {key}")

    async def database_deltree(self, family: str, key: str = "") -> AMIResponse:
        """
        Delete a family or key tree from the Asterisk database (AstDB).

        Args:
            family: Database family
            key: Optional key prefix to delete

        Returns:
            AMIResponse from the command
        """
        if key:
            return await self.command(f"database deltree {family} {key}")
        return await self.command(f"database deltree {family}")

    async def originate(
        self,
        channel: str,
        context: str | None = None,
        exten: str | None = None,
        priority: int = 1,
        application: str | None = None,
        data: str | None = None,
        timeout: int = 30000,
        caller_id: str | None = None,
        variables: dict[str, str] | None = None,
        account: str | None = None,
        async_: bool = False,
    ) -> AMIResponse:
        """
        Originate a call.

        Can originate to either a dialplan (context/exten/priority) or
        directly to an application.

        Args:
            channel: Channel to call (e.g., "SIP/1000", "PJSIP/1000")
            context: Dialplan context to connect to
            exten: Dialplan extension to connect to
            priority: Dialplan priority (default: 1)
            application: Application to execute instead of dialplan
            data: Data to pass to the application
            timeout: Timeout in milliseconds (default: 30000)
            caller_id: Caller ID to set
            variables: Channel variables to set
            account: Account code
            async_: If True, return immediately without waiting for answer

        Returns:
            AMIResponse from the originate action

        Example:
            # Originate to dialplan
            await ami.originate(
                channel="PJSIP/1000",
                context="default",
                exten="1001",
                caller_id="Test <1234>",
            )

            # Originate to application
            await ami.originate(
                channel="PJSIP/1000",
                application="Playback",
                data="hello-world",
            )
        """
        action: dict[str, Any] = {
            "Action": "Originate",
            "Channel": channel,
            "Timeout": str(timeout),
        }

        if context:
            action["Context"] = context
        if exten:
            action["Exten"] = exten
        if priority:
            action["Priority"] = str(priority)
        if application:
            action["Application"] = application
        if data:
            action["Data"] = data
        if caller_id:
            action["CallerID"] = caller_id
        if account:
            action["Account"] = account
        if async_:
            action["Async"] = "true"
        if variables:
            var_list = [f"{k}={v}" for k, v in variables.items()]
            action["Variable"] = ",".join(var_list)

        return await self.send_action(action)

    async def reload(self, module: str = "") -> AMIResponse:
        """
        Reload Asterisk configuration.

        Args:
            module: Specific module to reload (e.g., "sip", "pjsip", "dialplan").
                   If empty, reloads all modules.

        Returns:
            AMIResponse from the reload action
        """
        if module:
            return await self.command(f"{module} reload")
        return await self.send_action({"Action": "Reload"})

    async def ping(self) -> AMIResponse:
        """
        Send a ping to keep the connection alive.

        Returns:
            AMIResponse from the ping action
        """
        return await self.send_action({"Action": "Ping"})

    async def get_var(self, channel: str, variable: str) -> AMIResponse:
        """
        Get a channel variable.

        Args:
            channel: Channel name
            variable: Variable name to retrieve

        Returns:
            AMIResponse with the variable value
        """
        return await self.send_action(
            {"Action": "Getvar", "Channel": channel, "Variable": variable}
        )

    async def set_var(self, channel: str, variable: str, value: str) -> AMIResponse:
        """
        Set a channel variable.

        Args:
            channel: Channel name
            variable: Variable name to set
            value: Value to set

        Returns:
            AMIResponse from the setvar action
        """
        return await self.send_action(
            {"Action": "Setvar", "Channel": channel, "Variable": variable, "Value": value}
        )

    async def hangup(self, channel: str, cause: int | None = None) -> AMIResponse:
        """
        Hangup a channel.

        Args:
            channel: Channel name to hangup
            cause: Optional hangup cause code

        Returns:
            AMIResponse from the hangup action
        """
        action: dict[str, Any] = {"Action": "Hangup", "Channel": channel}
        if cause is not None:
            action["Cause"] = str(cause)
        return await self.send_action(action)

    async def redirect(
        self,
        channel: str,
        context: str,
        exten: str,
        priority: int = 1,
    ) -> AMIResponse:
        """
        Redirect a channel to a new dialplan location.

        Args:
            channel: Channel to redirect
            context: New context
            exten: New extension
            priority: New priority (default: 1)

        Returns:
            AMIResponse from the redirect action
        """
        return await self.send_action({
            "Action": "Redirect",
            "Channel": channel,
            "Context": context,
            "Exten": exten,
            "Priority": str(priority),
        })

    def _build_message(self, action: dict[str, Any]) -> str:
        """Build an AMI message from a dictionary."""
        lines: list[str] = []
        for key, value in action.items():
            if isinstance(value, list):
                for item in value:
                    lines.append(f"{key}: {item}")
            else:
                lines.append(f"{key}: {value}")
        return EOL.join(lines) + EOM

    async def _send(self, message: str) -> None:
        """Send a message to the server."""
        if not self._writer:
            raise AMIError("Not connected")
        try:
            self._writer.write(message.encode("utf-8"))
            await self._writer.drain()
        except OSError as e:
            raise AMIError(f"Failed to send message: {e}")

    async def _read_until(self, delimiter: str) -> str:
        """Read from stream until delimiter is found."""
        if not self._reader:
            raise AMIError("Not connected")

        try:
            data = await asyncio.wait_for(
                self._reader.readuntil(delimiter.encode("utf-8")),
                timeout=self.timeout,
            )
            return data.decode("utf-8")
        except asyncio.TimeoutError:
            raise AMIError("Read timeout")
        except asyncio.IncompleteReadError as e:
            if e.partial:
                return e.partial.decode("utf-8")
            raise AMIError("Connection closed by server")
        except OSError as e:
            raise AMIError(f"Socket error: {e}")

    async def _read_response(self, action_id: str) -> AMIResponse:
        """Read and parse a response for the given ActionID."""
        buffer = ""

        while True:
            raw = await self._read_until(EOM)
            buffer += raw
            response = AMIResponse.from_raw(raw)

            if response.action_id == action_id:
                # For Command actions with "Follows" response, read additional output
                if "Follows" in response.response or response.message == "Follows":
                    output = await self._read_command_output()
                    buffer += output
                    response = AMIResponse.from_raw(buffer)
                return response

    async def _read_command_output(self) -> str:
        """Read command output that follows a 'Follows' response."""
        output = ""
        while True:
            line = await self._read_until(EOL)
            output += line
            if line.strip() == "--END COMMAND--":
                break
        return output


class AMIClient:
    """
    Synchronous Asterisk Manager Interface client.

    Provides a synchronous interface for use in threaded applications,
    Celery tasks, and other non-async contexts. Uses its own event loop
    internally.

    Example:
        with AMIClient("localhost", 5038, "admin", "secret") as ami:
            response = ami.command("core show version")
            print(response.output)

            # Execute multiple commands in one connection
            ami.command("dialplan reload")
            ami.command("sip reload")

    Args:
        host: Asterisk server hostname or IP address
        port: AMI port (default: 5038)
        username: AMI username
        secret: AMI password/secret
        timeout: Connection and read timeout in seconds (default: 10.0)
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 5038,
        username: str = "",
        secret: str = "",
        timeout: float = 10.0,
    ) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.secret = secret
        self.timeout = timeout
        self._async_client: AsyncAMIClient | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def __enter__(self) -> AMIClient:
        self._loop = asyncio.new_event_loop()
        self._async_client = AsyncAMIClient(
            host=self.host,
            port=self.port,
            username=self.username,
            secret=self.secret,
            timeout=self.timeout,
        )
        self._loop.run_until_complete(self._async_client.connect())
        self._loop.run_until_complete(self._async_client.login())
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if self._async_client and self._async_client._authenticated:
            try:
                self._loop.run_until_complete(self._async_client.logoff())  # type: ignore[union-attr]
            except Exception:
                pass
        if self._async_client:
            self._loop.run_until_complete(self._async_client.disconnect())  # type: ignore[union-attr]
        if self._loop:
            self._loop.close()
            self._loop = None

    @property
    def connected(self) -> bool:
        """Return True if connected to the AMI server."""
        return self._async_client.connected if self._async_client else False

    @property
    def authenticated(self) -> bool:
        """Return True if authenticated with the AMI server."""
        return self._async_client.authenticated if self._async_client else False

    def _run(self, coro: Any) -> Any:
        """Run a coroutine in the event loop."""
        if not self._loop or not self._async_client:
            raise AMIError("Client not connected - use as context manager")
        return self._loop.run_until_complete(coro)

    def send_action(
        self,
        action: dict[str, Any],
        callback: Callable[[dict[str, str]], None] | None = None,
    ) -> AMIResponse:
        """
        Send an action to the AMI server.

        See AsyncAMIClient.send_action for full documentation.
        """
        return self._run(self._async_client.send_action(action, callback))  # type: ignore[union-attr]

    def command(self, command: str) -> AMIResponse:
        """
        Execute an Asterisk CLI command.

        See AsyncAMIClient.command for full documentation.
        """
        return self._run(self._async_client.command(command))  # type: ignore[union-attr]

    def database_put(self, family: str, key: str, value: str) -> AMIResponse:
        """
        Store a value in the Asterisk database.

        See AsyncAMIClient.database_put for full documentation.
        """
        return self._run(self._async_client.database_put(family, key, value))  # type: ignore[union-attr]

    def database_get(self, family: str, key: str) -> AMIResponse:
        """
        Retrieve a value from the Asterisk database.

        See AsyncAMIClient.database_get for full documentation.
        """
        return self._run(self._async_client.database_get(family, key))  # type: ignore[union-attr]

    def database_del(self, family: str, key: str) -> AMIResponse:
        """
        Delete a key from the Asterisk database.

        See AsyncAMIClient.database_del for full documentation.
        """
        return self._run(self._async_client.database_del(family, key))  # type: ignore[union-attr]

    def database_deltree(self, family: str, key: str = "") -> AMIResponse:
        """
        Delete a family or key tree from the Asterisk database.

        See AsyncAMIClient.database_deltree for full documentation.
        """
        return self._run(self._async_client.database_deltree(family, key))  # type: ignore[union-attr]

    def originate(
        self,
        channel: str,
        context: str | None = None,
        exten: str | None = None,
        priority: int = 1,
        application: str | None = None,
        data: str | None = None,
        timeout: int = 30000,
        caller_id: str | None = None,
        variables: dict[str, str] | None = None,
        account: str | None = None,
        async_: bool = False,
    ) -> AMIResponse:
        """
        Originate a call.

        See AsyncAMIClient.originate for full documentation.
        """
        return self._run(
            self._async_client.originate(  # type: ignore[union-attr]
                channel=channel,
                context=context,
                exten=exten,
                priority=priority,
                application=application,
                data=data,
                timeout=timeout,
                caller_id=caller_id,
                variables=variables,
                account=account,
                async_=async_,
            )
        )

    def reload(self, module: str = "") -> AMIResponse:
        """
        Reload Asterisk configuration.

        See AsyncAMIClient.reload for full documentation.
        """
        return self._run(self._async_client.reload(module))  # type: ignore[union-attr]

    def ping(self) -> AMIResponse:
        """
        Send a ping to keep the connection alive.

        See AsyncAMIClient.ping for full documentation.
        """
        return self._run(self._async_client.ping())  # type: ignore[union-attr]

    def get_var(self, channel: str, variable: str) -> AMIResponse:
        """
        Get a channel variable.

        See AsyncAMIClient.get_var for full documentation.
        """
        return self._run(self._async_client.get_var(channel, variable))  # type: ignore[union-attr]

    def set_var(self, channel: str, variable: str, value: str) -> AMIResponse:
        """
        Set a channel variable.

        See AsyncAMIClient.set_var for full documentation.
        """
        return self._run(self._async_client.set_var(channel, variable, value))  # type: ignore[union-attr]

    def hangup(self, channel: str, cause: int | None = None) -> AMIResponse:
        """
        Hangup a channel.

        See AsyncAMIClient.hangup for full documentation.
        """
        return self._run(self._async_client.hangup(channel, cause))  # type: ignore[union-attr]

    def redirect(
        self,
        channel: str,
        context: str,
        exten: str,
        priority: int = 1,
    ) -> AMIResponse:
        """
        Redirect a channel to a new dialplan location.

        See AsyncAMIClient.redirect for full documentation.
        """
        return self._run(self._async_client.redirect(channel, context, exten, priority))  # type: ignore[union-attr]

    def logoff(self) -> AMIResponse:
        """
        Log off from the AMI server.

        See AsyncAMIClient.logoff for full documentation.
        """
        return self._run(self._async_client.logoff())  # type: ignore[union-attr]
