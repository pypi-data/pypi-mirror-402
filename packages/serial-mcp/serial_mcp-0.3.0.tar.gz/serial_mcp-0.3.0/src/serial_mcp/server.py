import logging
import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

from .port_manager import PortManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)


@dataclass
class AppContext:
    port_manager: PortManager


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    logger.info("Initializing serial port manager")
    port_manager = PortManager()
    try:
        yield AppContext(port_manager=port_manager)
    finally:
        logger.info("Shutting down, closing all ports")
        await port_manager.close_all()


mcp = FastMCP("serial-mcp", lifespan=app_lifespan)

from .tools import register_tools  # noqa: E402

register_tools(mcp)
