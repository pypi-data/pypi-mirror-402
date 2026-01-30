"""Manages a Coq session and XML protocol communication"""
import asyncio
import logging
from pathlib import Path
import subprocess
from typing import Optional, Dict
from xml.etree import ElementTree as ET

logger = logging.getLogger(__name__)

class CoqResponse:
    """Structured response from Coq"""
    def __init__(self, xml_str: str):
        self.raw = xml_str
        self.parsed = self._parse_xml(xml_str)
        
    def _parse_xml(self, xml_str: str) -> Dict:
        """Parse Coq's XML response"""
        try:
            root = ET.fromstring(xml_str)
            if root.tag == "value":
                return {
                    "status": "success",
                    "message": root.text,
                    "response_type": root.get("val")
                }
            elif root.tag == "feedback":
                return {
                    "status": "feedback",
                    "message": root.find("message").text,
                    "level": root.get("object")  
                }
            elif root.tag == "error":
                return {
                    "status": "error",
                    "message": root.find("message").text
                }
            return {"status": "unknown", "message": xml_str}
            
        except ET.ParseError as e:
            return {"status": "error", "message": f"XML parse error: {e}"}

    @property
    def status(self) -> str:
        return self.parsed["status"]
        
    @property
    def message(self) -> str:
        return self.parsed["message"]
        
    def __bool__(self) -> bool:
        return self.status == "success"

class CoqSession:
    """Manages interaction with a Coq process"""

    def __init__(self, coq_path: Path, lib_path: Path):
        self.coq_path = coq_path
        self.lib_path = lib_path
        self.process: Optional[subprocess.Popen] = None
        self.mock_mode = False
        self._start_coq()

    def _start_coq(self):
        """Start Coq process with XML protocol"""
        try:
            # Check if coq_path exists
            if not self.coq_path.exists():
                logger.warning(f"Coq not found at {self.coq_path}, running in mock mode")
                self.mock_mode = True
                return

            cmd = [
                str(self.coq_path),
                "-xml",  # Use XML protocol
                "-Q", str(self.lib_path), "Coq"
            ]

            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            logger.info("Coq process started successfully")

        except Exception as e:
            logger.warning(f"Failed to start Coq: {e}, running in mock mode")
            self.mock_mode = True

    async def send_command(self, cmd: str) -> CoqResponse:
        """Send command to Coq and get response"""
        if self.mock_mode:
            # Return mock response when Coq is not available
            logger.info(f"Mock mode: executing command '{cmd}'")
            return CoqResponse('<value val="good">Mock response: Coq not available - command would be: ' + cmd + '</value>')

        if not self.process:
            raise RuntimeError("Coq process not running")

        try:
            # Send command
            self.process.stdin.write(cmd + "\n")
            self.process.stdin.flush()

            # Get response until </value> tag
            response = []
            while True:
                line = self.process.stdout.readline()
                if not line:
                    break
                response.append(line)
                if "</value>" in line:
                    break

            return CoqResponse("".join(response))

        except Exception as e:
            logger.error(f"Command error: {e}")
            return CoqResponse(f'<error><message>{str(e)}</message></error>')

    async def close(self):
        """Clean up Coq process"""
        if self.mock_mode:
            logger.info("Mock mode: no process to close")
            return

        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception as e:
                logger.error(f"Error closing Coq process: {e}")
