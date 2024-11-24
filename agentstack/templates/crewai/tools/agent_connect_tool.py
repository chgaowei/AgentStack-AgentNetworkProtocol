from typing import Optional, Union
from crewai_tools import tool
from dotenv import load_dotenv
import os

from agent_connect.simple_node import SimpleNode, SimpleNodeSession
import json

load_dotenv()

# An HTTP and WS service will be started in agent-connect
# It can be an IP address or a domain name
host_domain = os.getenv("HOST_DOMAIN")
# Host port, default is 80
host_port = os.getenv("HOST_PORT")
# WS path, default is /ws
host_ws_path = os.getenv("HOST_WS_PATH")
# Path to store DID document
did_document_path = os.getenv("DID_DOCUMENT_PATH")
# SSL certificate path, if using HTTPS, certificate and key need to be provided
ssl_cert_path = os.getenv("SSL_CERT_PATH")
ssl_key_path = os.getenv("SSL_KEY_PATH")


def generate_did_info(node: SimpleNode, did_document_path: str) -> None:
    """
    Generate or load DID information for a node.
    
    Args:
        node: SimpleNode instance
        did_document_path: Path to store/load DID document
    """
    if os.path.exists(did_document_path):
        print(f"Loading existing DID information from {did_document_path}")
        with open(did_document_path, "r") as f:
            did_info = json.load(f)
        node.set_did_info(
            did_info["private_key_pem"],
            did_info["did"],
            did_info["did_document_json"]
        )
    else:
        print("Generating new DID information")
        private_key_pem, did, did_document_json = node.generate_did_document()
        node.set_did_info(private_key_pem, did, did_document_json)
        
        # Save DID information
        os.makedirs(os.path.dirname(did_document_path), exist_ok=True)
        with open(did_document_path, "w") as f:
            json.dump({
                "private_key_pem": private_key_pem,
                "did": did,
                "did_document_json": did_document_json
            }, f, indent=2)
        print(f"DID information saved to {did_document_path}")


async def new_session_callback(simple_session: SimpleNodeSession):
    """
    Callback function for new session established.
    """
    print(f"New session established from {simple_session.remote_did}")

    while True:
        message = await simple_session.receive_message()
        # ToDo: add process code by user

agent_connect_simple_node = SimpleNode(host_domain=host_domain, 
                                       new_session_callback=new_session_callback,
                                       host_port=host_port, 
                                       host_ws_path=host_ws_path)
generate_did_info(agent_connect_simple_node, did_document_path)
agent_connect_simple_node.run()

@tool("Connect to Agent by DID")
async def connect_to_agent(destination_did: str) -> Optional[SimpleNodeSession]:
    """
    Connect to another agent through agent-connect node.
    
    Args:
        destination_did: DID of the agent to connect to
    Returns:
        SimpleNodeSession: Session object if connection was established successfully, None otherwise
    """
    try:
        session = await agent_connect_simple_node.connect_to_did(destination_did)
        if session:
            print(f"Successfully connected to agent: {destination_did}")
            return session
        return None
    except Exception as e:
        print(f"Failed to connect to agent: {e}")
        return None

@tool("Send Message to Agent by DID")
async def send_message(session: SimpleNodeSession, message: Union[str, bytes]) -> bool:
    """
    Send a message through agent-connect node.
    
    Args:
        message: Message content to be sent
        session: SimpleNodeSession object for the connection
    Returns:
        bool: True if message was sent successfully, False otherwise
    """
    try:
        success = await session.send_message(message)
        if success:
            print(f"Successfully sent message to {session.remote_did}")
            return True
        else:
            print(f"Failed to send message to {session.remote_did}")
            return False
    except Exception as e:
        print(f"Failed to send message: {e}")
        return False

@tool("Receive Message from Agent") 
async def receive_message(session: SimpleNodeSession) -> Optional[bytes]:
    """
    Receive message from agent-connect node.
    
    Args:
        session: SimpleNodeSession object for the connection
    Returns:
        bytes: Received message content, None if no message or error occurred
    """
    return await session.receive_message()

