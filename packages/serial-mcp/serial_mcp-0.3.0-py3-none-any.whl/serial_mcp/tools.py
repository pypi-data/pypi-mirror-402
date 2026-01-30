from typing import Annotated

from mcp.server.fastmcp import Context, FastMCP
from pydantic import Field


def register_tools(mcp: FastMCP):
    @mcp.tool()
    async def list_ports() -> dict:
        """List all available serial ports on the system.

        Returns information about each port including device path,
        description, manufacturer, and hardware IDs.
        """
        from .port_manager import PortManager

        ports = PortManager.list_available_ports()
        return {"ports": ports, "count": len(ports)}

    @mcp.tool()
    async def open_port(
        port: Annotated[str, Field(description="Serial port path (e.g., /dev/ttyUSB0, COM3)")],
        baud_rate: Annotated[int, Field(description="Communication speed", ge=50, le=4000000)] = 9600,
        data_bits: Annotated[int, Field(description="Data bits per byte (5, 6, 7, or 8)")] = 8,
        parity: Annotated[str, Field(description="Parity checking: none, even, odd, mark, or space")] = "none",
        stop_bits: Annotated[float, Field(description="Stop bits: 1, 1.5, or 2")] = 1,
        timeout: Annotated[float, Field(description="Read timeout in seconds", ge=0)] = 1.0,
        rtscts: Annotated[bool, Field(description="Enable hardware RTS/CTS flow control")] = False,
        xonxoff: Annotated[bool, Field(description="Enable software XON/XOFF flow control")] = False,
        ctx: Context = None,
    ) -> dict:
        """Open a serial port with the specified configuration.

        Returns a port_id that must be used for all subsequent operations
        on this port.
        """
        try:
            port_manager = ctx.request_context.lifespan_context.port_manager
            port_id = await port_manager.open_port(
                device_path=port,
                baud_rate=baud_rate,
                data_bits=data_bits,
                parity=parity,
                stop_bits=stop_bits,
                timeout=timeout,
                rtscts=rtscts,
                xonxoff=xonxoff,
            )
            return {
                "success": True,
                "port_id": port_id,
                "device": port,
                "message": f"Port {port} opened successfully as {port_id}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def close_port(
        port_id: Annotated[str, Field(description="The port identifier returned from open_port")],
        ctx: Context = None,
    ) -> dict:
        """Close an open serial port.

        The port_id is the identifier returned when the port was opened.
        """
        try:
            port_manager = ctx.request_context.lifespan_context.port_manager
            await port_manager.close_port(port_id)
            return {"success": True, "message": f"Port {port_id} closed successfully"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def write_data(
        port_id: Annotated[str, Field(description="The port identifier")],
        data: Annotated[str, Field(description="Data to write (string or hex if hex_mode is True)")],
        encoding: Annotated[str, Field(description="Text encoding for string data")] = "utf-8",
        hex_mode: Annotated[bool, Field(description="Interpret data as hex string (e.g., '48454C4C4F')")] = False,
        ctx: Context = None,
    ) -> dict:
        """Write data to an open serial port.

        Data can be a regular string (encoded with the specified encoding)
        or a hex string if hex_mode is True.
        """
        try:
            port_manager = ctx.request_context.lifespan_context.port_manager

            if hex_mode:
                bytes_data = bytes.fromhex(data.replace(" ", ""))
            else:
                bytes_data = data.encode(encoding)

            bytes_written = await port_manager.write_data(port_id, bytes_data)
            return {
                "success": True,
                "bytes_written": bytes_written,
                "message": f"Wrote {bytes_written} bytes to port {port_id}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def read_bytes(
        port_id: Annotated[str, Field(description="The port identifier")],
        num_bytes: Annotated[int, Field(description="Number of bytes to read", ge=1)],
        timeout: Annotated[float, Field(description="Maximum time to wait in seconds", ge=0)] = 5.0,
        encoding: Annotated[str, Field(description="Decode bytes using this encoding (or 'raw' for hex)")] = "utf-8",
        ctx: Context = None,
    ) -> dict:
        """Read a specific number of bytes from the serial port.

        Reads up to num_bytes, returning early if timeout is reached.
        """
        try:
            port_manager = ctx.request_context.lifespan_context.port_manager
            data, timed_out = await port_manager.read_bytes(port_id, num_bytes, timeout)

            result = {
                "success": True,
                "bytes_read": len(data),
                "timed_out": timed_out,
                "hex_data": data.hex(),
            }

            if encoding.lower() != "raw":
                try:
                    result["data"] = data.decode(encoding)
                except UnicodeDecodeError:
                    result["data"] = None
                    result["decode_error"] = f"Could not decode as {encoding}"
            else:
                result["data"] = None

            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def read_until(
        port_id: Annotated[str, Field(description="The port identifier")],
        terminator: Annotated[str, Field(description="Stop reading when this string is received")] = "\n",
        timeout: Annotated[float, Field(description="Maximum time to wait in seconds", ge=0)] = 5.0,
        max_bytes: Annotated[int, Field(description="Maximum bytes to read", ge=1)] = 1024,
        encoding: Annotated[str, Field(description="Encoding for terminator and output")] = "utf-8",
        ctx: Context = None,
    ) -> dict:
        """Read from serial port until a terminator string is received.

        Useful for reading line-based protocols (terminator='\\n').
        """
        try:
            port_manager = ctx.request_context.lifespan_context.port_manager
            terminator_bytes = terminator.encode(encoding)
            data, timed_out = await port_manager.read_until(
                port_id, terminator_bytes, timeout, max_bytes
            )

            result = {
                "success": True,
                "bytes_read": len(data),
                "timed_out": timed_out,
                "hex_data": data.hex(),
            }

            try:
                result["data"] = data.decode(encoding)
            except UnicodeDecodeError:
                result["data"] = None
                result["decode_error"] = f"Could not decode as {encoding}"

            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def read_for_duration(
        port_id: Annotated[str, Field(description="The port identifier")],
        duration: Annotated[float, Field(description="Time to read in seconds", gt=0)],
        max_bytes: Annotated[int, Field(description="Maximum bytes to collect", ge=1)] = 4096,
        encoding: Annotated[str, Field(description="Encoding for output (or 'raw' for hex only)")] = "utf-8",
        ctx: Context = None,
    ) -> dict:
        """Read all data from serial port for a specified duration.

        Continuously reads data for the specified time period, collecting
        all received bytes.
        """
        try:
            port_manager = ctx.request_context.lifespan_context.port_manager
            data = await port_manager.read_for_duration(port_id, duration, max_bytes)

            result = {
                "success": True,
                "bytes_read": len(data),
                "duration": duration,
                "hex_data": data.hex(),
            }

            if encoding.lower() != "raw":
                try:
                    result["data"] = data.decode(encoding)
                except UnicodeDecodeError:
                    result["data"] = None
                    result["decode_error"] = f"Could not decode as {encoding}"
            else:
                result["data"] = None

            return result
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def send_break(
        port_id: Annotated[str, Field(description="The port identifier")],
        duration: Annotated[float, Field(description="Duration of break signal in seconds", gt=0)] = 0.25,
        ctx: Context = None,
    ) -> dict:
        """Send a BREAK signal on the serial port.

        A BREAK is a special signal where the TX line is held low for
        a specified duration, used for various protocols.
        """
        try:
            port_manager = ctx.request_context.lifespan_context.port_manager
            await port_manager.send_break(port_id, duration)
            return {
                "success": True,
                "message": f"Sent break signal for {duration}s on port {port_id}",
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def get_port_status(
        port_id: Annotated[str, Field(description="The port identifier")],
        ctx: Context = None,
    ) -> dict:
        """Get the current status of a managed serial port.

        Returns configuration, buffer status, and control line states.
        """
        try:
            port_manager = ctx.request_context.lifespan_context.port_manager
            status = port_manager.get_port_status(port_id)
            if status is None:
                return {"success": False, "error": f"Port {port_id} not found"}
            return {"success": True, **status}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def list_open_ports(ctx: Context = None) -> dict:
        """List all currently open/managed serial ports.

        Returns information about each port that has been opened
        through this MCP server.
        """
        try:
            port_manager = ctx.request_context.lifespan_context.port_manager
            ports = port_manager.list_managed_ports()
            return {"success": True, "ports": ports, "count": len(ports)}
        except Exception as e:
            return {"success": False, "error": str(e)}
