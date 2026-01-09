import asyncio
import logging
from fastapi import WebSocket, WebSocketDisconnect
from typing import Optional
import docker

logger = logging.getLogger(__name__)


class TerminalManager:
    """Manages WebSocket connections to container terminals"""
    
    def __init__(self):
        self.docker_client = docker.from_env()
    
    async def handle_terminal_session(self, websocket: WebSocket, container_id: str):
        """
        Handle a WebSocket connection for terminal access to a container
        
        Args:
            websocket: The WebSocket connection
            container_id: The Docker container ID
        """
        await websocket.accept()
        
        try:
            # Get container
            container = self.docker_client.containers.get(container_id)
            
            # Create an exec instance for an interactive shell
            exec_instance = self.docker_client.api.exec_create(
                container.id,
                "/bin/bash",
                stdin=True,
                tty=True,
                stdout=True,
                stderr=True,
                privileged=False,
                user="root"
            )
            
            exec_id = exec_instance['Id']
            
            # Start the exec instance
            exec_socket = self.docker_client.api.exec_start(
                exec_id,
                socket=True,
                tty=True
            )
            
            # Create tasks for bidirectional communication
            send_task = asyncio.create_task(
                self._send_to_container(websocket, exec_socket)
            )
            receive_task = asyncio.create_task(
                self._receive_from_container(websocket, exec_socket)
            )
            
            # Wait for either task to complete
            done, pending = await asyncio.wait(
                [send_task, receive_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
            
        except docker.errors.NotFound:
            logger.error(f"Container not found: {container_id}")
            await websocket.send_text("Error: Container not found\r\n")
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"Error in terminal session: {e}", exc_info=True)
            try:
                await websocket.send_text(f"Error: {str(e)}\r\n")
            except:
                pass
        finally:
            try:
                if exec_socket:
                    exec_socket.close()
            except:
                pass
            
            try:
                await websocket.close()
            except:
                pass
    
    async def _send_to_container(self, websocket: WebSocket, exec_socket):
        """Send data from WebSocket to container"""
        try:
            while True:
                # Receive data from WebSocket
                data = await websocket.receive_text()
                
                # Send to container
                exec_socket._sock.send(data.encode('utf-8'))
                
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected (send)")
        except Exception as e:
            logger.error(f"Error sending to container: {e}")
    
    async def _receive_from_container(self, websocket: WebSocket, exec_socket):
        """Receive data from container and send to WebSocket"""
        try:
            loop = asyncio.get_event_loop()
            
            while True:
                # Use run_in_executor to avoid blocking the event loop
                try:
                    # Read from socket in non-blocking mode with timeout
                    data = await loop.run_in_executor(
                        None, 
                        lambda: self._read_from_socket(exec_socket._sock, timeout=0.1)
                    )
                    
                    if data:
                        # Send to WebSocket
                        await websocket.send_text(data.decode('utf-8', errors='ignore'))
                    elif data == b'':
                        # Empty data means connection closed
                        break
                        
                except Exception as e:
                    logger.error(f"Error receiving from container: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in receive loop: {e}")
    
    def _read_from_socket(self, sock, timeout=0.1):
        """Read from socket with timeout (runs in thread pool)"""
        import select
        
        # Use select to wait for data with timeout
        ready, _, _ = select.select([sock], [], [], timeout)
        
        if ready:
            try:
                return sock.recv(4096)
            except Exception:
                return b''
        return None  # No data available
