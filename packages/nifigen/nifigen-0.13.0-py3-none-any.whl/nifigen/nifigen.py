"""
NiFi Automation Library
======================
This module provides a comprehensive set of functions for automating Apache NiFi
operations through the REST API. It includes functions for managing process groups,
processors, controller services, connections, and flow deployment.

Version: 1.0.0
Author: [Your Name/Organization]
"""

import requests
import time
import json
import uuid
import os
from typing import Dict, List, Optional, Any, Union, Tuple


def get_processor_stats(pg_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Retrieves processor statistics for a given process group.
    
    Args:
        pg_id: Process Group ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Dictionary containing counts of running, stopped, and total processors
        or error status if exception occurs
        
    Raises:
        requests.exceptions.RequestException: If API call fails
    """
    try:
        r = requests.get(f"{NIFI_URL}/flow/process-groups/{pg_id}")
        r.raise_for_status()

        processors = r.json()["processGroupFlow"]["flow"].get("processors", [])

        running = 0
        stopped = 0

        for p in processors:
            state = p["component"].get("state")
            if state == "RUNNING":
                running += 1
            else:
                stopped += 1

        return {
            "status": True,
            "running": running,
            "stopped": stopped,
            "total": len(processors)
        }
    except Exception as e:
        print(f"Error getting processor stats for PG {pg_id}: {str(e)}")
        return {"status": False, "error": str(e)}


def get_root_flows(NIFI_URL: str) -> Dict[str, Any]:
    """
    Retrieves all flows under the ROOT process group with processor statistics.
    
    Args:
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Dictionary containing flow details including process groups, processors,
        input ports, and output ports with their states
    """
    try:
        url = f"{NIFI_URL}/flow/process-groups/root"
        r = requests.get(url)
        r.raise_for_status()

        data = r.json()["processGroupFlow"]
        flow = data["flow"]

        results = []

        # Process Groups with processor stats
        for pg in flow.get("processGroups", []):
            comp = pg["component"]

            stats = get_processor_stats(comp["id"], NIFI_URL)
            s_status = comp.get("state")
            if stats["running"] == stats["total"]:
                s_status = "RUNNING"

            results.append({
                "id": comp["id"],
                "name": comp["name"],
                "type": "PROCESS_GROUP",
                "state": s_status or comp.get("statelessGroupScheduledState"),
                "processors": {
                    "running": stats["running"],
                    "stopped": stats["stopped"],
                    "total": stats["total"]
                }
            })

        # Processors directly under ROOT
        for p in flow.get("processors", []):
            comp = p["component"]
            results.append({
                "id": comp["id"],
                "name": comp["name"],
                "type": "PROCESSOR",
                "state": comp.get("state")
            })

        # Input Ports
        for ip in flow.get("inputPorts", []):
            comp = ip["component"]
            results.append({
                "id": comp["id"],
                "name": comp["name"],
                "type": "INPUT_PORT",
                "state": comp.get("state")
            })

        # Output Ports
        for op in flow.get("outputPorts", []):
            comp = op["component"]
            results.append({
                "id": comp["id"],
                "name": comp["name"],
                "type": "OUTPUT_PORT",
                "state": comp.get("state")
            })

        return {
            "status": True,
            "root_id": data["id"],
            "flows": results
        }
    except Exception as e:
        print(f"Error getting root flows: {str(e)}")
        return {"status": False, "error": str(e)}


def controller_service_exists(pg_id: str, name: str, NIFI_URL: str) -> Optional[Dict[str, Any]]:
    """
    Checks if a controller service exists by name in a process group.
    
    Args:
        pg_id: Process Group ID
        name: Controller service name
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Controller service entity if found, None otherwise
    """
    try:
        r = requests.get(f"{NIFI_URL}/flow/process-groups/{pg_id}/controller-services")
        r.raise_for_status()
        
        for cs in r.json()["controllerServices"]:
            if cs["component"]["name"] == name:
                return cs
        return None
    except Exception as e:
        print(f"Error checking controller service existence: {str(e)}")
        return None


def create_controller_service(pg_id: str, cs_def: Dict[str, Any], NIFI_URL: str) -> Dict[str, Any]:
    """
    Creates a new controller service in a process group.
    
    Args:
        pg_id: Process Group ID
        cs_def: Controller service definition dictionary
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Created controller service entity or existing one if already present
    """
    try:
        existing = controller_service_exists(pg_id, cs_def["name"], NIFI_URL)
        if existing:
            print(f"Controller service '{cs_def['name']}' already exists")
            return {"status": True, "data": existing, "message": "Service already exists"}

        payload = {
            "revision": {"version": 0},
            "component": {
                "type": cs_def["type"],
                "bundle": cs_def["bundle"],
                "name": cs_def["name"],
                "properties": cs_def["properties"],
                "comments": cs_def.get("comments", "")
            }
        }

        r = requests.post(
            f"{NIFI_URL}/process-groups/{pg_id}/controller-services",
            json=payload
        )

        if r.status_code == 409:
            print("NiFi error:", r.text)
            return {"status": False, "error": r.text}

        r.raise_for_status()
        return {"status": True, "data": r.json()}
    except Exception as e:
        print(f"Error creating controller service: {str(e)}")
        return {"status": False, "error": str(e)}


def create_process_orch_group(parent_pg_id: str, name: str, NIFI_URL: str, 
                             position: Tuple[int, int] = (200, 200)) -> Dict[str, Any]:
    """
    Creates a new process group with orchestration naming convention.
    
    Args:
        parent_pg_id: Parent Process Group ID
        name: Base name for the process group
        NIFI_URL: Base URL of the NiFi instance
        position: Canvas position (x, y)
        
    Returns:
        Created process group entity
    """
    try:
        url = f"{NIFI_URL}/process-groups/{parent_pg_id}/process-groups"
        payload = {
            "revision": {"version": 0},
            "component": {
                "name": f"{name}_orch",
                "position": {"x": position[0], "y": position[1]}
            }
        }
        r = requests.post(url, json=payload)
        r.raise_for_status()
        return {"status": True, "data": r.json()}
    except Exception as e:
        print(f"Error creating process group: {str(e)}")
        return {"status": False, "error": str(e)}


def enable_controller_service(cs_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Enables a controller service by ID.
    
    Args:
        cs_id: Controller Service ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Updated controller service entity
    """
    try:
        # Get fresh revision
        r = requests.get(f"{NIFI_URL}/controller-services/{cs_id}")
        r.raise_for_status()
        
        rev = r.json()["revision"]["version"]

        payload = {
            "revision": {"version": rev},
            "component": {"id": cs_id, "state": "ENABLED"}
        }
        
        r2 = requests.put(
            f"{NIFI_URL}/controller-services/{cs_id}",
            json=payload
        )
        
        print("Enable response:", r2.text)
        return {"status": True, "data": r2.json()}
    except Exception as e:
        print(f"Error enabling controller service: {str(e)}")
        return {"status": False, "error": str(e)}


def import_controller_services(pg_id: str, file_path: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Imports controller services from a JSON file.
    
    Args:
        pg_id: Process Group ID
        file_path: Path to JSON file containing service definitions
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Dictionary with status and created/enabled services
    """
    try:
        with open(file_path) as f:
            services = json.load(f)

        created = []
        for cs in services:
            cs_entity = create_controller_service(pg_id, cs, NIFI_URL)
            if cs_entity["status"]:
                created.append(cs_entity["data"])
            else:
                print(f"Failed to create service: {cs['name']}")

        for cs in created:
            enable_result = enable_controller_service(cs["id"], NIFI_URL)
            if not enable_result["status"]:
                print(f"Failed to enable service: {cs['id']}")

        return {"status": True, "created_services": created, "last_service_id": cs["id"] if created else None}
    except Exception as e:
        print(f"Error importing controller services: {str(e)}")
        return {"status": False, "error": str(e)}


def create_processor_in_pg(pg_id: str, comp: Dict[str, Any], NIFI_URL: str) -> Dict[str, Any]:
    """
    Creates a processor in a process group using component definition.
    
    Args:
        pg_id: Process Group ID
        comp: Processor component definition
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Created processor entity
    """
    try:
        time.sleep(4)
        url = f"{NIFI_URL}/process-groups/{pg_id}/processors"
        payload = {
            "revision": {"version": 0},
            "component": {
                "type": comp["type"],
                "name": comp["name"],
                "position": {"x": comp["position"]["x"], "y": comp["position"]["y"]},
                "config": comp.get("config", {})
            }
        }
        r = requests.post(url, json=payload)
        r.raise_for_status()
        print(f"Created processor: {comp['name']} - {r.json()['id']}")
        return {"status": True, "data": r.json()}
    except Exception as e:
        print(f"Error creating processor: {str(e)}")
        return {"status": False, "error": str(e)}


def get_processor_by_type(pg_id: str, processor_type: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Finds a processor by type within a process group.
    
    Args:
        pg_id: Process Group ID
        processor_type: Fully qualified processor type name
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Processor entity if found
        
    Raises:
        Exception: If processor not found
    """
    try:
        time.sleep(5)
        r = requests.get(f"{NIFI_URL}/flow/process-groups/{pg_id}")
        r.raise_for_status()
        
        for p in r.json()["processGroupFlow"]["flow"]["processors"]:
            if p["component"]["type"] == processor_type:
                return {"status": True, "data": p}
        
        raise Exception(f"Processor of type '{processor_type}' not found in PG {pg_id}")
    except Exception as e:
        print(f"Error getting processor by type: {str(e)}")
        return {"status": False, "error": str(e)}


def bind_websocket_controller_service(processor_id: str, cs_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Binds a WebSocket controller service to a processor.
    
    Args:
        processor_id: Processor ID
        cs_id: Controller Service ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Operation status
    """
    try:
        # Get fresh processor
        r = requests.get(f"{NIFI_URL}/processors/{processor_id}")
        r.raise_for_status()

        proc = r.json()
        rev = proc["revision"]["version"]
        properties = proc["component"]["config"]["properties"]
        properties["WebSocket Server Controller Service"] = cs_id

        payload = {
            "revision": {"version": rev},
            "component": {
                "id": processor_id,
                "config": {"properties": properties}
            }
        }

        r2 = requests.put(
            f"{NIFI_URL}/processors/{processor_id}",
            json=payload
        )
        r2.raise_for_status()
        
        return {"status": True, "message": "WebSocket controller service bound successfully"}
    except Exception as e:
        print(f"Error binding WebSocket controller service: {str(e)}")
        return {"status": False, "error": str(e)}


def create_connection(pg_id: str, conn: Dict[str, Any], NIFI_URL: str) -> Dict[str, Any]:
    """
    Creates a connection between components in a process group.
    
    Args:
        pg_id: Process Group ID
        conn: Connection definition
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Created connection entity
    """
    try:
        print("####### Creating connection")
        time.sleep(5)
        url = f"{NIFI_URL}/process-groups/{pg_id}/connections"

        src_old = conn["component"]["source"]["id"]
        dst_old = conn["component"]["destination"]["id"]

        print(f"Source ID: {src_old}")
        print(f"Destination ID: {dst_old}")

        payload = {
            "revision": {"version": 0},
            "component": {
                "name": conn["component"].get("selectedRelationships", ["success"])[0],
                "parentGroupId": pg_id,
                "source": {
                    "id": src_old,
                    "type": conn["component"]["source"]["type"],
                    "groupId": pg_id,
                    "name": conn["component"]["source"]["name"]
                },
                "destination": {
                    "id": dst_old,
                    "type": conn["component"]["destination"]["type"],
                    "groupId": pg_id,
                    "name": conn["component"]["source"]["name"]
                },
                "selectedRelationships": conn["component"].get("selectedRelationships", ["success"]),
                "flowFileExpiration": conn["component"].get("flowFileExpiration", "0 sec"),
                "backPressureObjectThreshold": conn["component"].get("backPressureObjectThreshold", 10000),
                "backPressureDataSizeThreshold": conn["component"].get("backPressureDataSizeThreshold", "1 GB"),
                "availableRelationships": conn["component"].get("availableRelationships", [])
            }
        }

        r = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        r.raise_for_status()

        print("Created connection successfully")
        return {"status": True, "data": r.json()}
    except Exception as e:
        print(f"Error creating connection: {str(e)}")
        return {"status": False, "error": str(e)}


def get_process_group_full(pg_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Retrieves complete process group data including all components.
    
    Args:
        pg_id: Process Group ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Complete process group data
    """
    try:
        time.sleep(5)
        url = f"{NIFI_URL}/flow/process-groups/{pg_id}"
        r = requests.get(url)
        r.raise_for_status()
        return {"status": True, "data": r.json()}
    except Exception as e:
        print(f"Error getting process group full data: {str(e)}")
        return {"status": False, "error": str(e)}


def create_controller_service_by_type(pg_id: str, cs_type: str, name: str, 
                                     NIFI_URL: str, properties: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Creates a controller service by type in a process group.
    
    Args:
        pg_id: Process Group ID
        cs_type: Controller service type
        name: Service name
        NIFI_URL: Base URL of the NiFi instance
        properties: Service properties dictionary
        
    Returns:
        Created controller service ID
    """
    try:
        print(f"==== > {NIFI_URL}")
        payload = {
            "revision": {"version": 0},
            "component": {
                "type": cs_type,
                "name": name,
                "properties": properties or {}
            }
        }
        r = requests.post(f"{NIFI_URL}/process-groups/{pg_id}/controller-services", json=payload)
        r.raise_for_status()
        cs_id = r.json()["id"]
        print(f"Created Controller Service: {name}")
        return {"status": True, "cs_id": cs_id}
    except Exception as e:
        print(f"Error creating controller service by type: {str(e)}")
        return {"status": False, "error": str(e)}


def start_processor(processor_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Starts a processor by ID.
    
    Args:
        processor_id: Processor ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Operation status
    """
    try:
        # Get current revision
        url_get = f"{NIFI_URL}/processors/{processor_id}"
        resp = requests.get(url_get)
        resp.raise_for_status()
        processor = resp.json()
        revision = processor['revision']['version']

        # Start processor
        url_put = f"{NIFI_URL}/processors/{processor_id}/run-status"
        payload = {
            "revision": {"version": revision},
            "state": "RUNNING"
        }
        r = requests.put(url_put, json=payload)
        r.raise_for_status()
        
        return {"status": True, "message": f"Processor {processor_id} started successfully"}
    except Exception as e:
        print(f"Error starting processor: {str(e)}")
        return {"status": False, "error": str(e)}


def connect_components(
    pg_id: str,
    source_id: str,
    source_type: str,
    destination_id: str,
    destination_type: str,
    NIFI_URL: str,
    relationships: Optional[List[str]] = None,
    name: Optional[str] = None,
    flowfile_expiration: str = "0 sec",
    backpressure_count: int = 10000,
    backpressure_size: str = "1 GB"
) -> Dict[str, Any]:
    """
    Creates a connection between any two NiFi components.
    
    Args:
        pg_id: Process Group ID
        source_id: Source component ID
        source_type: Source component type
        destination_id: Destination component ID
        destination_type: Destination component type
        NIFI_URL: Base URL of the NiFi instance
        relationships: Selected relationships for the connection
        name: Connection name
        flowfile_expiration: FlowFile expiration time
        backpressure_count: Backpressure object threshold
        backpressure_size: Backpressure data size threshold
        
    Returns:
        Created connection entity
    """
    try:
        print(f"\nSource connection: {source_id}\nDestination connection: {destination_id}\n")

        # Normalize processor types
        if source_type.startswith("org.apache.nifi.processors"):
            source_type = "PROCESSOR"
        if destination_type.startswith("org.apache.nifi.processors"):
            destination_type = "PROCESSOR"
        
        if relationships is None:
            relationships = ["success"]
        if source_type == "INPUT_PORT":
            relationships = None

        url = f"{NIFI_URL}/process-groups/{pg_id}/connections"

        payload = {
            "revision": {"version": 0},
            "component": {
                "parentGroupId": pg_id,
                "name": name or f"{source_id[:6]}_to_{destination_id[:6]}",
                "source": {
                    "id": source_id,
                    "type": source_type,
                    "groupId": pg_id
                },
                "destination": {
                    "id": destination_id,
                    "type": destination_type,
                    "groupId": pg_id
                },
                "selectedRelationships": relationships,
                "flowFileExpiration": flowfile_expiration,
                "backPressureObjectThreshold": backpressure_count,
                "backPressureDataSizeThreshold": backpressure_size
            }
        }

        r = requests.post(url, json=payload)
        r.raise_for_status()

        print(
            f"Connected {source_type} ({source_id}) "
            f"→ {destination_type} ({destination_id}) "
            f"relationships={relationships}"
        )

        return {"status": True, "data": r.json()}
    except Exception as e:
        print(f"Error connecting components: {str(e)}")
        return {"status": False, "error": str(e)}


def get_processor_by_id(processor_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Retrieves processor details by ID.
    
    Args:
        processor_id: Processor ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Processor entity
    """
    try:
        url = f"{NIFI_URL}/processors/{processor_id}"
        r = requests.get(url)
        r.raise_for_status()
        return {"status": True, "data": r.json()}
    except Exception as e:
        print(f"Error getting processor by ID: {str(e)}")
        return {"status": False, "error": str(e)}


def get_processors_in_pg(pg_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Retrieves all processors in a process group.
    
    Args:
        pg_id: Process Group ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        List of processors
    """
    try:
        url = f"{NIFI_URL}/flow/process-groups/{pg_id}"
        r = requests.get(url)
        r.raise_for_status()
        return {"status": True, "data": r.json()["processGroupFlow"]["flow"]["processors"]}
    except Exception as e:
        print(f"Error getting processors in PG: {str(e)}")
        return {"status": False, "error": str(e)}


def export_process_group(pg_id: str, filename: Optional[str], NIFI_URL: str) -> Dict[str, Any]:
    """
    Exports a process group as JSON file.
    
    Args:
        pg_id: Process Group ID
        filename: Output filename (optional)
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Process group JSON data
    """
    try:
        url = f"{NIFI_URL}/flow/process-groups/{pg_id}"
        r = requests.get(url)
        r.raise_for_status()
        pg_json = r.json()["processGroupFlow"]
        
        if filename:
            with open(filename, "w") as f:
                json.dump(pg_json, f, indent=2)
            print(f"Process Group exported to {filename}")
        
        return {"status": True, "data": pg_json}
    except Exception as e:
        print(f"Error exporting process group: {str(e)}")
        return {"status": False, "error": str(e)}


def get_all_child_process_group_ids(parent_pg_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Recursively retrieves all child process group IDs under a parent PG.
    
    Args:
        parent_pg_id: Parent Process Group ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        List of child process group IDs
    """
    try:
        all_pg_ids = []

        def _walk(pg_id: str):
            url = f"{NIFI_URL}/process-groups/{pg_id}/process-groups"
            r = requests.get(url)
            r.raise_for_status()

            data = r.json()
            child_pgs = data["processGroups"]

            for pg in child_pgs:
                child_id = pg["id"]
                all_pg_ids.append(child_id)
                _walk(child_id)

        _walk(parent_pg_id)
        return {"status": True, "data": all_pg_ids}
    except Exception as e:
        print(f"Error getting child PG IDs: {str(e)}")
        return {"status": False, "error": str(e)}


def stop_all_processors(pg_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Stops all processors in a process group.
    
    Args:
        pg_id: Process Group ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Operation status
    """
    try:
        r = requests.get(f"{NIFI_URL}/flow/process-groups/{pg_id}")
        r.raise_for_status()

        processors = r.json()["processGroupFlow"]["flow"].get("processors", [])

        for p in processors:
            if p["component"]["state"] != "STOPPED":
                proc_id = p["id"]

                # Fetch fresh revision
                pr = requests.get(f"{NIFI_URL}/processors/{proc_id}")
                pr.raise_for_status()

                rev = pr.json()["revision"]["version"]

                payload = {
                    "revision": {"version": rev},
                    "state": "STOPPED"
                }

                requests.put(
                    f"{NIFI_URL}/processors/{proc_id}/run-status",
                    json=payload
                ).raise_for_status()

        print(f"✔ Processors stopped in PG {pg_id}")
        return {"status": True, "message": f"All processors stopped in PG {pg_id}"}
    except Exception as e:
        print(f"Error stopping all processors: {str(e)}")
        return {"status": False, "error": str(e)}


def stop_all_ports(pg_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Stops all input and output ports in a process group.
    
    Args:
        pg_id: Process Group ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Operation status
    """
    try:
        r = requests.get(f"{NIFI_URL}/flow/process-groups/{pg_id}")
        r.raise_for_status()

        flow = r.json()["processGroupFlow"]["flow"]

        for port_type in ["inputPorts", "outputPorts"]:
            for p in flow.get(port_type, []):
                if p["component"]["state"] != "STOPPED":
                    port_id = p["id"]
                    
                    # Determine port type for API call
                    if port_type == "inputPorts":
                        port_type_api = "input-ports"
                    else:
                        port_type_api = "output-ports"

                    pr = requests.get(f"{NIFI_URL}/{port_type_api}/{port_id}")
                    pr.raise_for_status()
                    
                    rev = pr.json()["revision"]["version"]

                    payload = {
                        "revision": {"version": rev},
                        "state": "STOPPED"
                    }

                    requests.put(
                        f"{NIFI_URL}/{port_type_api}/{port_id}/run-status",
                        json=payload
                    ).raise_for_status()

        print(f"✔ Ports stopped in PG {pg_id}")
        return {"status": True, "message": f"All ports stopped in PG {pg_id}"}
    except Exception as e:
        print(f"Error stopping all ports: {str(e)}")
        return {"status": False, "error": str(e)}


def empty_all_queues(pg_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Empties all flowfile queues in a process group.
    
    Args:
        pg_id: Process Group ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Operation status
    """
    try:
        r = requests.get(f"{NIFI_URL}/flow/process-groups/{pg_id}")
        r.raise_for_status()

        connections = r.json()["processGroupFlow"]["flow"].get("connections", [])

        for c in connections:
            conn_id = c["id"]
            requests.post(
                f"{NIFI_URL}/flowfile-queues/{conn_id}/drop-requests"
            ).raise_for_status()

        print(f"✔ Queues emptied in PG {pg_id}")
        return {"status": True, "message": f"All queues emptied in PG {pg_id}"}
    except Exception as e:
        print(f"Error emptying all queues: {str(e)}")
        return {"status": False, "error": str(e)}


def disable_all_controller_services(pg_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Disables all controller services in a process group.
    
    Args:
        pg_id: Process Group ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Operation status
    """
    try:
        r = requests.get(f"{NIFI_URL}/flow/process-groups/{pg_id}/controller-services")
        r.raise_for_status()

        for cs in r.json().get("controllerServices", []):
            cs_id = cs["id"]

            cr = requests.get(f"{NIFI_URL}/controller-services/{cs_id}")
            cr.raise_for_status()

            rev = cr.json()["revision"]["version"]

            payload = {
                "revision": {"version": rev},
                "component": {
                    "id": cs_id,
                    "state": "DISABLED"
                }
            }

            requests.put(
                f"{NIFI_URL}/controller-services/{cs_id}",
                json=payload
            ).raise_for_status()

        print(f"✔ Controller services disabled in PG {pg_id}")
        return {"status": True, "message": f"All controller services disabled in PG {pg_id}"}
    except Exception as e:
        print(f"Error disabling all controller services: {str(e)}")
        return {"status": False, "error": str(e)}


def delete_process_group(pg_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Deletes a process group.
    
    Args:
        pg_id: Process Group ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Operation status
    """
    try:
        r = requests.get(f"{NIFI_URL}/process-groups/{pg_id}")
        r.raise_for_status()

        rev = r.json()["revision"]["version"]

        requests.delete(
            f"{NIFI_URL}/process-groups/{pg_id}",
            params={"version": rev}
        ).raise_for_status()

        print(f"🗑 Process Group {pg_id} deleted")
        return {"status": True, "message": f"Process Group {pg_id} deleted"}
    except Exception as e:
        print(f"Error deleting process group: {str(e)}")
        return {"status": False, "error": str(e)}


def get_controller_service_by_name(pg_id: str, service_name: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Retrieves a controller service by name within a process group.
    
    Args:
        pg_id: Process Group ID
        service_name: Controller service name
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Controller service entity if found
    """
    try:
        url = f"{NIFI_URL}/flow/process-groups/{pg_id}/controller-services"
        r = requests.get(url)
        r.raise_for_status()

        services = r.json().get("controllerServices", [])

        for cs in services:
            if cs["component"]["name"] == service_name:
                return {"status": True, "data": cs}

        return {"status": False, "error": f"Controller service '{service_name}' not found"}
    except Exception as e:
        print(f"Error getting controller service by name: {str(e)}")
        return {"status": False, "error": str(e)}


def create_process_group_inside_pg(
    parent_pg_id: str,
    name: str,
    NIFI_URL: str,
    position: Tuple[float, float] = (200.0, 200.0),
    fail_if_exists: bool = True
) -> Dict[str, Any]:
    """
    Creates a process group inside an existing process group.
    
    Args:
        parent_pg_id: Parent Process Group ID
        name: New process group name
        NIFI_URL: Base URL of the NiFi instance
        position: Canvas position (x, y)
        fail_if_exists: Raise error if PG with same name exists
        
    Returns:
        Creation status and PG details
    """
    try:
        # Check if PG already exists under parent
        r = requests.get(f"{NIFI_URL}/flow/process-groups/{parent_pg_id}")
        r.raise_for_status()

        existing_pgs = r.json()["processGroupFlow"]["flow"]["processGroups"]

        for pg in existing_pgs:
            if pg["component"]["name"] == name:
                if fail_if_exists:
                    return {
                        "status": False,
                        "id": pg["component"]["id"],
                        "name": name,
                        "message": "Process Group already exists"
                    }
                else:
                    return {
                        "status": True,
                        "id": pg["component"]["id"],
                        "name": name,
                        "message": "Process Group already exists"
                    }

        # Create Process Group
        payload = {
            "revision": {"version": 0},
            "component": {
                "name": name,
                "position": {
                    "x": float(position[0]),
                    "y": float(position[1])
                }
            }
        }

        r = requests.post(
            f"{NIFI_URL}/process-groups/{parent_pg_id}/process-groups",
            json=payload
        )
        r.raise_for_status()

        pg_id = r.json()["id"]

        print(f"Created Process Group '{name}' inside PG '{parent_pg_id}'")

        return {
            "status": True,
            "id": pg_id,
            "name": name
        }
    except Exception as e:
        print(f"Error creating process group inside PG: {str(e)}")
        return {"status": False, "error": str(e)}


def create_input_port(
    pg_id: str,
    name: str,
    NIFI_URL: str,
    position_id: int = 0,
    allow_remote_access: bool = False
) -> Dict[str, Any]:
    """
    Creates an input port inside a process group.
    
    Args:
        pg_id: Process Group ID
        name: Input port name
        NIFI_URL: Base URL of the NiFi instance
        position_id: Position multiplier for canvas layout
        allow_remote_access: Allow access from remote PGs
        
    Returns:
        Created input port details
    """
    try:
        position = (400 * position_id, 0.0)
        url = f"{NIFI_URL}/process-groups/{pg_id}/input-ports"

        payload = {
            "revision": {"version": 0},
            "component": {
                "name": name,
                "position": {
                    "x": float(position[0]),
                    "y": float(position[1])
                },
                "allowRemoteAccess": allow_remote_access
            }
        }

        r = requests.post(url, json=payload)
        r.raise_for_status()

        port_id = r.json()["id"]

        print(f"Created Input Port '{name}' in PG '{pg_id}'")

        return {
            "status": True,
            "id": port_id,
            "name": name,
            "data": r.json()
        }
    except Exception as e:
        print(f"Error creating input port: {str(e)}")
        return {"status": False, "error": str(e)}


def create_execute_stream_command(
    pg_id: str,
    NIFI_URL: str,
    name: str = "ExecuteStreamCommand",
    command: str = "",
    command_arguments: str = "",
    working_dir: str = "",
    position_id: int = 1,
    scheduling_period: str = "0 sec",
    environment: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Creates an ExecuteStreamCommand processor in a process group.
    
    Args:
        pg_id: Target Process Group ID
        NIFI_URL: Base URL of the NiFi instance
        name: Processor name
        command: Command to execute
        command_arguments: Command arguments
        working_dir: Working directory
        position_id: Position multiplier for canvas layout
        scheduling_period: Scheduling period
        environment: Environment variables dictionary
        
    Returns:
        Created processor details
    """
    try:
        position = (500 * position_id, 0.0)
        url = f"{NIFI_URL}/process-groups/{pg_id}/processors"

        properties = {
            "Command Path": command,
            "Command Arguments": command_arguments,
            "Working Directory": working_dir,
            "Ignore STDIN": "false",
            "Redirect STDERR": "true",
            "Argument Delimiter": ";",
            "Max Attribute Length": "5000",
            "Output MIME Type": "application/json"
        }

        if environment:
            properties["Environment Variables"] = "\n".join(
                f"{k}={v}" for k, v in environment.items()
            )

        payload = {
            "revision": {"version": 0},
            "component": {
                "type": "org.apache.nifi.processors.standard.ExecuteStreamCommand",
                "name": name,
                "position": {
                    "x": float(position[0]),
                    "y": float(position[1])
                },
                "config": {
                    "properties": properties,
                    "schedulingPeriod": scheduling_period,
                    "executionNode": "ALL",
                    "autoTerminatedRelationships": [
                        "original",
                        "nonzero status"
                    ]
                }
            }
        }

        r = requests.post(url, json=payload)
        r.raise_for_status()

        proc_id = r.json()["id"]

        print(f"Created ExecuteStreamCommand '{name}' in PG '{pg_id}'")

        return {
            "status": True,
            "id": proc_id,
            "name": name,
            "data": r.json()
        }
    except Exception as e:
        print(f"Error creating ExecuteStreamCommand: {str(e)}")
        return {"status": False, "error": str(e)}


def create_output_port(
    pg_id: str,
    name: str,
    NIFI_URL: str,
    position_id: int = 2,
    allow_remote_access: bool = False
) -> Dict[str, Any]:
    """
    Creates an output port inside a process group.
    
    Args:
        pg_id: Process Group ID
        name: Output port name
        NIFI_URL: Base URL of the NiFi instance
        position_id: Position multiplier for canvas layout
        allow_remote_access: Allow remote process groups to connect
        
    Returns:
        Created output port details
    """
    try:
        position = (500 * position_id, 0.0)
        url = f"{NIFI_URL}/process-groups/{pg_id}/output-ports"

        payload = {
            "revision": {"version": 0},
            "component": {
                "name": name,
                "position": {
                    "x": float(position[0]),
                    "y": float(position[1])
                },
                "allowRemoteAccess": allow_remote_access
            }
        }

        r = requests.post(url, json=payload)
        r.raise_for_status()

        port_id = r.json()["id"]

        print(f"Created Output Port '{name}' in PG '{pg_id}'")

        return {
            "status": True,
            "id": port_id,
            "name": name,
            "data": r.json()
        }
    except Exception as e:
        print(f"Error creating output port: {str(e)}")
        return {"status": False, "error": str(e)}


def create_put_websocket(
    pg_id: str,
    name: str,
    comp: Dict[str, Any],
    NIFI_URL: str,
    position_id: int = 0
) -> Dict[str, Any]:
    """
    Creates a PutWebSocket processor.
    
    Args:
        pg_id: Process Group ID
        name: Processor name
        comp: Processor component configuration
        NIFI_URL: Base URL of the NiFi instance
        position_id: Position multiplier for canvas layout
        
    Returns:
        Created processor details
    """
    try:
        url = f"{NIFI_URL}/process-groups/{pg_id}/processors"

        payload = {
            "revision": {"version": 0},
            "component": {
                "type": "org.apache.nifi.processors.websocket.PutWebSocket",
                "name": name,
                "position": {
                    "x": 400 + (position_id * 150),
                    "y": 300
                },
                "config": {
                    "properties": {
                        "WebSocket Session Id": comp["WebSocket Session Id"],
                        "WebSocket Controller Service Id": comp["WebSocket Controller Service Id"],
                        "WebSocket Endpoint Id": comp["WebSocket Endpoint Id"],
                        "WebSocket Message Type": comp["WebSocket Message Type"]
                    },
                    "autoTerminatedRelationships": ["failure", "success"],
                    "schedulingPeriod": "0 sec",
                    "executionNode": "ALL"
                }
            }
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return {"status": True, "data": response.json()}
    except Exception as e:
        print(f"Error creating PutWebSocket processor: {str(e)}")
        return {"status": False, "error": str(e)}


def add_handle_http_response(
    pg_id: str,
    http_cs_id: str,
    NIFI_URL: str,
    processor_name: str = "HandleHttpResponse"
) -> Dict[str, Any]:
    """
    Creates a HandleHttpResponse processor in a process group.
    
    Args:
        pg_id: Process Group ID
        http_cs_id: HTTP Context Map controller service ID
        NIFI_URL: Base URL of the NiFi instance
        processor_name: Processor name prefix
        
    Returns:
        Created processor details
    """
    try:
        url = f"{NIFI_URL}/process-groups/{pg_id}/processors"

        payload = {
            "revision": {"version": 0},
            "component": {
                "name": f"{processor_name}_HTTP_rep",
                "type": "org.apache.nifi.processors.standard.HandleHttpResponse",
                "config": {
                    "properties": {
                        "HTTP Status Code": "${http.status.code}",
                        "HTTP Context Map": http_cs_id,
                        "Attributes for HTTP Response": "Content-Type:application/json"
                    },
                    "autoTerminatedRelationships": ["failure", "success"]
                }
            }
        }

        headers = {"Content-Type": "application/json"}
        r = requests.post(url, headers=headers, data=json.dumps(payload))
        r.raise_for_status()

        return {"status": True, "data": r.json()}
    except Exception as e:
        print(f"Error adding HandleHttpResponse: {str(e)}")
        return {"status": False, "error": str(e)}


def add_route_on_attribute_rule(
    route_proc_id: str,
    rule_name: str,
    expression: str,
    NIFI_URL: str
) -> Dict[str, Any]:
    """
    Adds a new rule (dynamic property) to a RouteOnAttribute processor.
    
    Args:
        route_proc_id: RouteOnAttribute processor ID
        rule_name: Rule name (dynamic property name)
        expression: Expression for the rule
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Operation status
    """
    try:
        # Get processor
        proc = requests.get(f"{NIFI_URL}/processors/{route_proc_id}").json()
        rev = proc["revision"]["version"]

        properties = proc["component"]["config"]["properties"] or {}

        # Add dynamic rule
        properties[rule_name] = expression

        payload = {
            "revision": {"version": rev},
            "component": {
                "id": route_proc_id,
                "config": {
                    "properties": properties
                }
            }
        }

        r = requests.put(f"{NIFI_URL}/processors/{route_proc_id}", json=payload)
        r.raise_for_status()
        time.sleep(5)
        
        print(f"Added RouteOnAttribute rule: {rule_name}")
        return {"status": True, "message": f"Rule '{rule_name}' added successfully"}
    except Exception as e:
        print(f"Error adding RouteOnAttribute rule: {str(e)}")
        return {"status": False, "error": str(e)}


def connect_processor_to_child_pg(
    parent_pg_id: str,
    processor_id: str,
    child_pg_id: str,
    NIFI_URL: str,
    relationships: List[str]
) -> Dict[str, Any]:
    """
    Connects a processor in a parent PG to a child PG's input port.
    
    Args:
        parent_pg_id: Parent Process Group ID
        processor_id: Processor ID in the parent PG
        child_pg_id: Child Process Group ID
        NIFI_URL: Base URL of the NiFi instance
        relationships: Relationships to use for connection
        
    Returns:
        Operation status
    """
    try:
        # Get the child PG's input ports
        r = requests.get(f"{NIFI_URL}/process-groups/{child_pg_id}/input-ports")
        r.raise_for_status()
        input_ports = r.json()["inputPorts"]
        
        if not input_ports:
            raise Exception(f"Child PG {child_pg_id} has no input ports")
        
        # Use the first input port
        input_port = input_ports[0]

        # Get the processor info
        r = requests.get(f"{NIFI_URL}/processors/{processor_id}")
        r.raise_for_status()
        processor = r.json()

        # Prepare the connection payload
        connection_payload = {
            "revision": {"version": 0},
            "component": {
                "name": f"Connection_to_{input_port['component']['name']}",
                "source": {
                    "id": processor_id,
                    "type": "PROCESSOR",
                    "groupId": parent_pg_id
                },
                "destination": {
                    "id": input_port['id'],
                    "type": "INPUT_PORT",
                    "groupId": child_pg_id
                },
                "selectedRelationships": relationships,
                "flowFileExpiration": "0 sec",
                "backPressureDataSizeThreshold": "1 GB",
                "backPressureObjectThreshold": 10000
            }
        }

        # Create the connection in the parent PG
        url = f"{NIFI_URL}/process-groups/{parent_pg_id}/connections"
        r = requests.post(url, json=connection_payload)
        r.raise_for_status()
        
        print(f"Connected processor '{processor['component']['name']}' to input port '{input_port['component']['name']}' of child PG.")
        return {"status": True, "data": r.json()}
    except Exception as e:
        print(f"Error connecting processor to child PG: {str(e)}")
        return {"status": False, "error": str(e)}


def start_port_by_id(port_id: str, port_type: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Starts an InputPort or OutputPort by ID.
    
    Args:
        port_id: Port ID
        port_type: Port type ("input-ports" or "output-ports")
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Operation status
    """
    try:
        # Get current revision
        r = requests.get(f"{NIFI_URL}/{port_type}/{port_id}")
        r.raise_for_status()

        revision = r.json()["revision"]["version"]
        name = r.json()["component"]["name"]

        # Start port
        payload = {
            "revision": {"version": revision},
            "state": "RUNNING"
        }

        sr = requests.put(
            f"{NIFI_URL}/{port_type}/{port_id}/run-status",
            json=payload
        )
        sr.raise_for_status()

        print(f"✔ Started {port_type[:-1]}: {name} ({port_id})")
        return {"status": True, "message": f"Port {port_id} started successfully"}
    except Exception as e:
        print(f"Error starting port by ID: {str(e)}")
        return {"status": False, "error": str(e)}


def stop_processor(processor_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Stops a processor by ID.
    
    Args:
        processor_id: Processor ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Operation status
    """
    try:
        # Get processor details
        proc_data = get_processor(processor_id, NIFI_URL)
        if not proc_data["status"]:
            return proc_data
            
        processor = proc_data["data"]
        url = f"{NIFI_URL}/processors/{processor_id}/run-status"
        
        payload = {
            "revision": processor["revision"],
            "state": "STOPPED"
        }
        
        r = requests.put(url, json=payload)
        r.raise_for_status()
        
        print(f"Stopped processor: {processor['component']['name']}")
        return {"status": True, "message": f"Processor {processor_id} stopped"}
    except Exception as e:
        print(f"Error stopping processor: {str(e)}")
        return {"status": False, "error": str(e)}


def get_processor(processor_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Retrieves processor details by ID.
    
    Args:
        processor_id: Processor ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Processor entity
    """
    try:
        url = f"{NIFI_URL}/processors/{processor_id}"
        r = requests.get(url)
        r.raise_for_status()
        return {"status": True, "data": r.json()}
    except Exception as e:
        print(f"Error getting processor: {str(e)}")
        return {"status": False, "error": str(e)}


def stop_process_group(pg_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Stops all processors in a process group.
    
    Args:
        pg_id: Process Group ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Operation status
    """
    try:
        print(f"Stopping process group: {pg_id}")
        
        processors_data = get_processors_in_pg(pg_id, NIFI_URL)
        if not processors_data["status"]:
            return processors_data
            
        processors = processors_data["data"]
        
        if not processors:
            print("No processors in process group")
            return {"status": True, "message": "No processors to stop"}
            
        for p in processors:
            if p["component"]["state"] != "STOPPED":
                stop_result = stop_processor(p["id"], NIFI_URL)
                if not stop_result["status"]:
                    print(f"Failed to stop processor {p['id']}")
                    
        return {"status": True, "message": f"All processors in PG {pg_id} stopped"}
    except Exception as e:
        print(f"Error stopping process group: {str(e)}")
        return {"status": False, "error": str(e)}


def remove_route_on_attribute_rule(
    route_proc_id: str,
    rule_name: str,
    NIFI_URL: str
) -> Dict[str, Any]:
    """
    Removes a rule (dynamic property) from a RouteOnAttribute processor.
    
    Args:
        route_proc_id: RouteOnAttribute processor ID
        rule_name: Rule name to remove
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Operation status
    """
    try:
        # Get processor
        proc = requests.get(f"{NIFI_URL}/processors/{route_proc_id}").json()
        rev = proc["revision"]["version"]

        properties = proc["component"]["config"]["properties"] or {}

        # Remove dynamic rule by setting to None
        properties[rule_name] = None

        payload = {
            "revision": {"version": rev},
            "component": {
                "id": route_proc_id,
                "config": {
                    "properties": properties
                }
            }
        }

        r = requests.put(f"{NIFI_URL}/processors/{route_proc_id}", json=payload)
        r.raise_for_status()
        time.sleep(5)
        
        print(f"Deleted RouteOnAttribute rule: {rule_name}")
        return {"status": True, "message": f"Rule '{rule_name}' removed successfully"}
    except Exception as e:
        print(f"Error removing RouteOnAttribute rule: {str(e)}")
        return {"status": False, "error": str(e)}


def delete_all_connections_to_pg(pg_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Deletes all connections where source OR destination belongs to a process group.
    
    Args:
        pg_id: Process Group ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Operation status
    """
    try:
        # Get ALL connections from the process group
        r = requests.get(f"{NIFI_URL}/process-groups/{pg_id}/connections")
        r.raise_for_status()
        
        all_connections = []
        data = r.json()
        
        # Flatten connections (this is a simplified approach)
        if isinstance(data, dict) and "connections" in data:
            all_connections = data["connections"]
        elif isinstance(data, list):
            all_connections = data
            
        for c in all_connections:
            if isinstance(c, dict):
                src = c.get("component", {}).get("source", {})
                dest = c.get("component", {}).get("destination", {})
                
                if src.get("groupId") == pg_id or dest.get("groupId") == pg_id:
                    cid = c.get("id")
                    ver = c.get("revision", {}).get("version", 0)
                    
                    if cid:
                        requests.delete(
                            f"{NIFI_URL}/connections/{cid}",
                            params={"version": ver}
                        ).raise_for_status()
                        
                        print(f"🧹 Deleted connection {cid}")

        print(f"All connections to/from PG {pg_id} deleted")
        return {"status": True, "message": f"All connections to/from PG {pg_id} deleted"}
    except Exception as e:
        print(f"Error deleting all connections to PG: {str(e)}")
        return {"status": False, "error": str(e)}


def delete_processor_to_child_pg_connection(
    parent_pg_id: str,
    processor_id: str,
    child_pg_id: str,
    NIFI_URL: str
) -> Dict[str, Any]:
    """
    Deletes the connection from a processor in a parent PG to a child PG input port.
    
    Args:
        parent_pg_id: Parent Process Group ID
        processor_id: Processor ID in parent PG
        child_pg_id: Child Process Group ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Operation status
    """
    try:
        # Get all connections in the parent PG
        r = requests.get(f"{NIFI_URL}/flow/process-groups/{parent_pg_id}")
        r.raise_for_status()
        
        connections = r.json()["processGroupFlow"]["flow"].get("connections", [])

        # Find matching connection
        target = None
        for c in connections:
            src = c["component"]["source"]
            dst = c["component"]["destination"]

            if (
                src["type"] == "PROCESSOR"
                and src["id"] == processor_id
                and src["groupId"] == parent_pg_id
                and dst["type"] == "INPUT_PORT"
                and dst["groupId"] == child_pg_id
            ):
                target = c
                break

        if not target:
            print("⚠️ Connection not found — nothing to delete")
            return {"status": True, "message": "Connection not found"}

        conn_id = target["id"]
        version = target["revision"]["version"]

        # Delete connection
        r = requests.delete(
            f"{NIFI_URL}/connections/{conn_id}",
            params={"version": version}
        )
        r.raise_for_status()

        print(f"✅ Deleted connection {conn_id}")
        return {"status": True, "message": f"Connection {conn_id} deleted"}
    except Exception as e:
        print(f"Error deleting processor to child PG connection: {str(e)}")
        return {"status": False, "error": str(e)}


def safe_delete_process_group(pg_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Safely deletes a process group by stopping all components and emptying queues first.
    
    Args:
        pg_id: Process Group ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Operation status
    """
    try:
        print(f"⚠ Deleting Process Group {pg_id}")

        # Stop all components safely
        stop_result = stop_all_processors(pg_id, NIFI_URL)
        if not stop_result["status"]:
            print("Warning: Failed to stop some processors")
            
        stop_ports_result = stop_all_ports(pg_id, NIFI_URL)
        if not stop_ports_result["status"]:
            print("Warning: Failed to stop some ports")
            
        empty_queues_result = empty_all_queues(pg_id, NIFI_URL)
        if not empty_queues_result["status"]:
            print("Warning: Failed to empty some queues")
            
        disable_services_result = disable_all_controller_services(pg_id, NIFI_URL)
        if not disable_services_result["status"]:
            print("Warning: Failed to disable some controller services")

        time.sleep(2)  # Allow NiFi to settle

        # Delete the process group
        delete_result = delete_process_group(pg_id, NIFI_URL)
        
        if delete_result["status"]:
            return {"status": True, "message": "Process Group deleted safely"}
        else:
            return delete_result
            
    except Exception as e:
        print(f"Error in safe delete process group: {str(e)}")
        return {"status": False, "error": str(e)}


def start_process_group(pg_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Starts all processors in a process group.
    
    Args:
        pg_id: Process Group ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Operation status
    """
    try:
        processors_data = get_processors_in_pg(pg_id, NIFI_URL)
        if not processors_data["status"]:
            return processors_data
            
        processors = processors_data["data"]
        
        if not processors:
            print("No processors in process group")
            return {"status": True, "message": "No processors to start"}
            
        for p in processors:
            if p["component"]["state"] != "RUNNING":
                start_result = start_processor(p['id'], NIFI_URL)
                if not start_result["status"]:
                    print(f"Failed to start processor {p['id']}")
                    
        return {"status": True, "message": f"All processors in PG {pg_id} started"}
    except Exception as e:
        print(f"Error starting process group: {str(e)}")
        return {"status": False, "error": str(e)}


def create_execute_sql_processor(
    pg_id: str,
    name: str,
    position_x: float,
    position_y: float,
    dbcp_id: str,
    sql_query: str,
    NIFI_URL: str,
    run_every_minutes: int = 10,
    concurrent_tasks: int = 1,
    parameters: Optional[Dict[str, str]] = None,
    start: bool = True
) -> Dict[str, Any]:
    """
    Creates an ExecuteSQL processor using a DBCPConnectionPool service.
    
    Args:
        pg_id: Process Group ID
        name: Processor name
        position_x: X position on canvas
        position_y: Y position on canvas
        dbcp_id: DBCP Connection Pool controller service ID
        sql_query: SQL query to execute
        NIFI_URL: Base URL of the NiFi instance
        run_every_minutes: Scheduling interval in minutes
        concurrent_tasks: Number of concurrent tasks
        parameters: SQL parameter dictionary
        start: Whether to start the processor immediately
        
    Returns:
        Created processor ID
    """
    try:
        # Merge parameters into SQL
        if parameters:
            for k, v in parameters.items():
                sql_query = sql_query.replace(f"${{{k}}}", v)

        payload = {
            "revision": {"version": 0},
            "component": {
                "type": "org.apache.nifi.processors.standard.ExecuteSQL",
                "name": name,
                "position": {"x": position_x, "y": position_y},
                "config": {
                    "schedulingStrategy": "TIMER_DRIVEN",
                    "schedulingPeriod": f"{run_every_minutes} min",
                    "concurrentlySchedulableTaskCount": concurrent_tasks,
                    "properties": {
                        "Database Connection Pooling Service": dbcp_id,
                        "SQL Query": sql_query,
                        "Max Rows Per Flow File": "0",
                        "Output Format": "JSON"
                    },
                    "autoTerminatedRelationships": ["failure"]
                }
            }
        }

        r = requests.post(
            f"{NIFI_URL}/process-groups/{pg_id}/processors",
            json=payload
        )
        r.raise_for_status()

        processor_id = r.json()["id"]
        print(f"✔ ExecuteSQL processor created: {processor_id}")

        if start:
            start_result = start_processor(processor_id, NIFI_URL)
            if not start_result["status"]:
                print(f"Warning: Failed to start processor {processor_id}")

        return {"status": True, "processor_id": processor_id}
    except Exception as e:
        print(f"Error creating ExecuteSQL processor: {str(e)}")
        return {"status": False, "error": str(e)}


def setup_avro_to_json_services(pg_id: str, NIFI_URL: str) -> Dict[str, Any]:
    """
    Sets up AvroReader and JsonWriter controller services for data conversion.
    
    Args:
        pg_id: Process Group ID
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Tuple of (avro_reader_id, json_writer_id)
    """
    try:
        # Create AvroReader controller service
        avro_reader_result = create_controller_service_by_type(
            pg_id=pg_id,
            cs_type="org.apache.nifi.avro.AvroReader",
            name="AvroReader",
            NIFI_URL=NIFI_URL,
            properties={}
        )
        
        if not avro_reader_result["status"]:
            return avro_reader_result
            
        avro_reader_id = avro_reader_result["cs_id"]
        
        # Enable AvroReader
        enable_avro_result = enable_controller_service(avro_reader_id, NIFI_URL)
        if not enable_avro_result["status"]:
            print(f"Warning: Failed to enable AvroReader {avro_reader_id}")

        # Create JsonWriter controller service
        json_writer_result = create_controller_service_by_type(
            pg_id=pg_id,
            cs_type="org.apache.nifi.json.JsonRecordSetWriter",
            name="JsonWriter",
            NIFI_URL=NIFI_URL,
            properties={}
        )
        
        if not json_writer_result["status"]:
            return json_writer_result
            
        json_writer_id = json_writer_result["cs_id"]
        
        # Enable JsonWriter
        enable_json_result = enable_controller_service(json_writer_id, NIFI_URL)
        if not enable_json_result["status"]:
            print(f"Warning: Failed to enable JsonWriter {json_writer_id}")

        return {
            "status": True,
            "avro_reader_id": avro_reader_id,
            "json_writer_id": json_writer_id
        }
    except Exception as e:
        print(f"Error setting up Avro to JSON services: {str(e)}")
        return {"status": False, "error": str(e)}


def recreate_process_group(
    parent_pg_id: str,
    name: str,
    pg_json: Dict[str, Any],
    NIFI_URL: str,
    position: Tuple[int, int] = (0, 0),
    id_map: Optional[Dict[str, str]] = None,
    orch_dir: Optional[str] = None
) -> Dict[str, Any]:
    """
    Recreates a process group from exported JSON data.
    
    Args:
        parent_pg_id: Parent Process Group ID
        name: Process group name
        pg_json: Exported process group JSON data
        NIFI_URL: Base URL of the NiFi instance
        position: Canvas position (x, y)
        id_map: Dictionary for old_id -> new_id mapping
        orch_dir: Orchestration directory path
        
    Returns:
        Created process group details
    """
    try:
        if id_map is None:
            id_map = {}

        # Create the Process Group
        new_pg_result = create_process_orch_group(parent_pg_id, name, NIFI_URL, position)
        if not new_pg_result["status"]:
            return new_pg_result
            
        new_pg_id = new_pg_result["data"]["id"]
        
        # Define HTTP controller service
        cs_def = {
            "name": "http_cs",
            "type": "org.apache.nifi.http.StandardHttpContextMap",
            "bundle": {
                'group': 'org.apache.nifi',
                'artifact': 'nifi-http-context-map-nar',
                'version': '2.7.2'
            },
            "properties": {"Request Expiration": "5 min"}
        }
        
        id_map[pg_json["id"]] = new_pg_id
        print(f"Created new PG: {name}, id={new_pg_id}")

        # Create HTTP controller service
        http_cs_result = create_controller_service(pg_id=new_pg_id, cs_def=cs_def, NIFI_URL=NIFI_URL)
        if not http_cs_result["status"]:
            return http_cs_result
            
        http_cs = http_cs_result["data"]

        # Enable HTTP controller service
        enable_cs_result = enable_controller_service(cs_id=http_cs["id"], NIFI_URL=NIFI_URL)
        if not enable_cs_result["status"]:
            print(f"Warning: Failed to enable HTTP controller service")

        # Import controller services from file
        import_result = import_controller_services(
            pg_id=new_pg_id,
            file_path="/work/progs/nifi_aut/nifi_srv/nifi_aut/service_controller.json",
            NIFI_URL=NIFI_URL
        )
        
        if not import_result["status"]:
            print(f"Warning: Failed to import some controller services")
            
        cs_id = import_result.get("last_service_id")

        # Create orchestration directory if needed
        if orch_dir and not os.path.exists(f"{orch_dir}/{new_pg_id}"):
            os.makedirs(f"{orch_dir}/{new_pg_id}")

        # Recreate processors
        print("################### Creating processors")
        for proc in pg_json["flow"]["processors"]:
            time.sleep(2)
            print(f"-- Processing: {proc['component']['name']}")
            
            comp = proc["component"]
            
            # Apply modifications based on processor type
            if comp['type'] == 'org.apache.nifi.processors.websocket.ListenWebSocket':
                comp['config']['properties']['WebSocket Server Controller Service'] = cs_id
                
            if comp['type'] == 'org.apache.nifi.processors.standard.HandleHttpRequest':
                comp['config']['properties']['HTTP Context Map'] = http_cs["id"]
                comp['config']['properties']['Allowed Paths'] = "/" + name + "_hr"
                
            if comp['type'] == 'org.apache.nifi.processors.standard.ExecuteStreamCommand':
                comp["config"]["properties"]['Working Directory'] = f"{orch_dir}/{new_pg_id}"
                comp["config"]["properties"]['Command Arguments'] = f"main_orch.py"
                
            if comp['type'] == 'org.apache.nifi.processors.standard.EvaluateJsonPath':
                comp["config"]["properties"]['question'] = "$.question"
                comp["config"]["descriptors"]['question'] = {
                    "name": "question",
                    "displayName": "question",
                    "description": "",
                    "required": False,
                    "sensitive": False,
                    "dynamic": False,
                    "supportsEl": False,
                    "expressionLanguageScope": "Not Supported",
                    "dependencies": []
                }
                
            if comp['type'] == 'org.apache.nifi.processors.jolt.JoltTransformJSON':
                comp["config"]["properties"]['Jolt Specification'] = """[\n  {\n    \"operation\": \"shift\",\n    \"spec\": {\"question\": \"question\",\n      \"session_id\": \"session_id\",\n      \"timestamp\": \"timestamp\",\n      \"status\": \"status\",\n      \"sources\": \"sources\",\n      \"selected_agents\": \"selected_agents\"\n    }\n  },\n  {\n    \"operation\": \"modify-overwrite-beta\",\n    \"spec\": {\n      \"agent_tmp\": \"=join('--,--', @(1,selected_agents))\"\n    }\n  },\n  {\n    \"operation\": \"modify-overwrite-beta\",\n    \"spec\": {\n      \"agent\": \"=concat('--', @(1,agent_tmp), '--')\"\n    }\n  },\n  {\n    \"operation\": \"remove\",\n    \"spec\": {\n      \"agent_tmp\": \"\"\n    }\n  }\n]"""

            # Create processor
            new_proc_result = create_processor_in_pg(new_pg_id, comp, NIFI_URL)
            if new_proc_result["status"]:
                id_map[comp["id"]] = new_proc_result["data"]["id"]

        # Recreate sub-groups recursively
        for sub_pg in pg_json["flow"]["processGroups"]:
            recreate_result = recreate_process_group(
                new_pg_id,
                sub_pg["component"]["name"],
                sub_pg,
                position=(position[0] + 300, position[1] + 300),
                id_map=id_map,
                NIFI_URL=NIFI_URL
            )
            
            if not recreate_result["status"]:
                print(f"Warning: Failed to recreate sub-group {sub_pg['component']['name']}")

        # Bind WebSocket controller service
        ws_cs_result = get_processor_by_type(
            pg_id=new_pg_id,
            processor_type="org.apache.nifi.processors.websocket.ListenWebSocket",
            NIFI_URL=NIFI_URL
        )
        
        if ws_cs_result["status"]:
            ws_cs = ws_cs_result["data"]
            bind_result = bind_websocket_controller_service(ws_cs["id"], cs_id, NIFI_URL)
            if not bind_result["status"]:
                print(f"Warning: Failed to bind WebSocket controller service")

        # Recreate connections
        print("START connections ###################")
        for conn in pg_json["flow"]["connections"]:
            # Map old source/destination IDs to new IDs
            src_old = conn["component"]["source"]["id"]
            dst_old = conn["component"]["destination"]["id"]

            # Skip connection if source or destination not in id_map yet
            if src_old not in id_map or dst_old not in id_map:
                print(f"Skipping connection {conn['component'].get('name', '')} because IDs not mapped yet")
                continue

            conn_copy = conn.copy()
            conn_copy["component"]["source"]["id"] = id_map[src_old]
            conn_copy["component"]["destination"]["id"] = id_map[dst_old]
            
            create_conn_result = create_connection(new_pg_id, conn_copy, NIFI_URL)
            if not create_conn_result["status"]:
                print(f"Warning: Failed to create connection")

        print(f"Process Group {name} recreated successfully")
        return {"status": True, "pg_id": new_pg_id, "id_map": id_map}
        
    except Exception as e:
        print(f"Error recreating process group: {str(e)}")
        return {"status": False, "error": str(e)}


def create_update_attribute_processor(
    pg_id: str,
    name: str,
    NIFI_URL: str,
    position_id: int = 0,
    additional_attributes: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Creates an UpdateAttribute processor to add/modify flowfile attributes.
    
    Args:
        pg_id: Process Group ID
        name: Processor name
        NIFI_URL: Base URL of the NiFi instance
        position_id: Position multiplier for canvas layout
        additional_attributes: Dictionary of attributes to add/modify
        
    Returns:
        Created processor details
    """
    try:
        position = (400 * position_id, 100.0)  # Adjusted y position for better layout
        url = f"{NIFI_URL}/process-groups/{pg_id}/processors"
        
        # Default attributes
        properties = {
        }
        
        # Add additional attributes if provided
        if additional_attributes:
            properties.update(additional_attributes)
        
        payload = {
            "revision": {"version": 0},
            "component": {
                "type": "org.apache.nifi.processors.attributes.UpdateAttribute",
                "name": name,
                "position": {
                    "x": float(position[0]),
                    "y": float(position[1])
                },
                "config": {
                    "properties": properties,
                    "autoTerminatedRelationships": ["failure"]
                }
            }
        }
        
        r = requests.post(url, json=payload)
        r.raise_for_status()
        
        proc_id = r.json()["id"]
        
        print(f"Created UpdateAttribute processor '{name}' in PG '{pg_id}'")
        
        return {
            "status": True,
            "id": proc_id,
            "name": name,
            "data": r.json()
        }
    except Exception as e:
        print(f"Error creating UpdateAttribute processor: {str(e)}")
        return {"status": False, "error": str(e)}
#######
#   flow
########


def create_and_enable_dbcp_service(
    pg_id: str,
    name: str,
    jdbc_url: str,
    driver_class: str,
    driver_location: str,
    username: str,
    password: str,
    NIFI_URL: str,
    max_total_connections: str = "10"
) -> Dict[str, Any]:
    """
    Creates and enables a DBCPConnectionPool controller service.
    
    Args:
        pg_id: Process Group ID
        name: Service name
        jdbc_url: JDBC connection URL
        driver_class: Database driver class name
        driver_location: Database driver location path
        username: Database username
        password: Database password
        NIFI_URL: Base URL of the NiFi instance
        max_total_connections: Maximum connection pool size
        
    Returns:
        Controller service ID
    """
    try:
        # Check if service already exists
        r = requests.get(f"{NIFI_URL}/flow/process-groups/{pg_id}/controller-services")
        r.raise_for_status()

        for cs in r.json().get("controllerServices", []):
            if cs["component"]["name"] == name:
                cs_id = cs["id"]
                print(f"✔ Controller service '{name}' already exists")
                
                # Enable if not already enabled
                enable_result = enable_controller_service(cs_id, NIFI_URL)
                if not enable_result["status"]:
                    print(f"Warning: Failed to enable existing service {cs_id}")
                    
                return {"status": True, "cs_id": cs_id}

        # Create controller service
        payload = {
            "revision": {"version": 0},
            "component": {
                "type": "org.apache.nifi.dbcp.DBCPConnectionPool",
                "name": name,
                "properties": {
                    "Database Connection URL": jdbc_url,
                    "Database Driver Class Name": driver_class,
                    "Database Driver Locations": driver_location,
                    "Database User": username,
                    "Password": password,
                    "Max Total Connections": max_total_connections
                }
            }
        }

        r = requests.post(
            f"{NIFI_URL}/process-groups/{pg_id}/controller-services",
            json=payload
        )
        r.raise_for_status()

        cs_id = r.json()["id"]
        print(f"✔ Created controller service '{name}'")

        # Enable controller service
        enable_result = enable_controller_service(cs_id, NIFI_URL)
        if not enable_result["status"]:
            print(f"Warning: Failed to enable new service {cs_id}")

        return {"status": True, "cs_id": cs_id}
    except Exception as e:
        print(f"Error creating and enabling DBCP service: {str(e)}")
        return {"status": False, "error": str(e)}


def create_sql_to_json_jsonfile_flow(
    pg_id: str,
    sql_name: str,
    sql_query: str,
    dbcp_id: str,
    output_dir: str,
    output_filename: str,
    NIFI_URL: str,
    position_x: float = 0,
    position_y: float = 0,
    run_every_minutes: int = 10,
    start: bool = True
) -> Dict[str, Any]:
    """
    Creates a complete SQL to JSON file flow in NiFi.
    
    Args:
        pg_id: Process Group ID
        sql_name: SQL processor name
        sql_query: SQL query to execute
        dbcp_id: DBCP connection pool service ID
        output_dir: Output directory path
        output_filename: Output filename
        NIFI_URL: Base URL of the NiFi instance
        position_x: Starting X position
        position_y: Starting Y position
        run_every_minutes: Scheduling interval in minutes
        start: Whether to start processors immediately
        
    Returns:
        Flow creation status and component IDs
    """
    try:
        # Setup Avro to JSON controller services
        services_result = setup_avro_to_json_services(pg_id, NIFI_URL)
        if not services_result["status"]:
            return services_result
            
        avro_reader_id = services_result["avro_reader_id"]
        json_writer_id = services_result["json_writer_id"]

        # Create ExecuteSQL processor
        exec_sql_result = create_execute_sql_processor(
            pg_id=pg_id,
            name=sql_name,
            position_x=position_x,
            position_y=position_y,
            dbcp_id=dbcp_id,
            sql_query=sql_query,
            run_every_minutes=run_every_minutes,
            start=False,
            NIFI_URL=NIFI_URL
        )
        
        if not exec_sql_result["status"]:
            return exec_sql_result
            
        exec_sql_proc_id = exec_sql_result["processor_id"]

        # Create ConvertRecord processor (Avro → JSON)
        convert_payload = {
            "revision": {"version": 0},
            "component": {
                "type": "org.apache.nifi.processors.standard.ConvertRecord",
                "name": f"{sql_name}_AvroToJson",
                "position": {"x": position_x + 300, "y": position_y},
                "config": {
                    "properties": {
                        "Record Reader": avro_reader_id,
                        "Record Writer": json_writer_id
                    },
                    "autoTerminatedRelationships": ["failure"]
                }
            }
        }
        
        r = requests.post(
            f"{NIFI_URL}/process-groups/{pg_id}/processors",
            json=convert_payload
        )
        r.raise_for_status()
        convert_proc_id = r.json()["id"]

        # Create UpdateAttribute processor (set filename)
        update_attr_payload = {
            "revision": {"version": 0},
            "component": {
                "type": "org.apache.nifi.processors.attributes.UpdateAttribute",
                "name": f"{sql_name}_SetFilename",
                "position": {"x": position_x + 450, "y": position_y},
                "config": {
                    "properties": {
                        "filename": output_filename
                    },
                    "autoTerminatedRelationships": ["failure"]
                }
            }
        }
        
        r = requests.post(
            f"{NIFI_URL}/process-groups/{pg_id}/processors",
            json=update_attr_payload
        )
        r.raise_for_status()
        update_attr_id = r.json()["id"]

        # Create PutFile processor
        putfile_payload = {
            "revision": {"version": 0},
            "component": {
                "type": "org.apache.nifi.processors.standard.PutFile",
                "name": f"{sql_name}_PutFile",
                "position": {"x": position_x + 650, "y": position_y},
                "config": {
                    "properties": {
                        "Directory": output_dir + "/" + pg_id,
                        "Conflict Resolution Strategy": "replace",
                        "Create Missing Directories": "true"
                    },
                    "autoTerminatedRelationships": ["failure", "success"]
                }
            }
        }
        
        r = requests.post(
            f"{NIFI_URL}/process-groups/{pg_id}/processors",
            json=putfile_payload
        )
        r.raise_for_status()
        putfile_id = r.json()["id"]

        # Create connections between processors
        connections = [
            # ExecuteSQL → ConvertRecord
            connect_components(
                pg_id=pg_id,
                source_id=exec_sql_proc_id,
                source_type="PROCESSOR",
                destination_id=convert_proc_id,
                destination_type="PROCESSOR",
                relationships=["success"],
                NIFI_URL=NIFI_URL
            ),
            # ConvertRecord → UpdateAttribute
            connect_components(
                pg_id=pg_id,
                source_id=convert_proc_id,
                source_type="PROCESSOR",
                destination_id=update_attr_id,
                destination_type="PROCESSOR",
                relationships=["success"],
                NIFI_URL=NIFI_URL
            ),
            # UpdateAttribute → PutFile
            connect_components(
                pg_id=pg_id,
                source_id=update_attr_id,
                source_type="PROCESSOR",
                destination_id=putfile_id,
                destination_type="PROCESSOR",
                relationships=["success"],
                NIFI_URL=NIFI_URL
            )
        ]
        
        # Check if any connection failed
        for conn_result in connections:
            if not conn_result["status"]:
                print("Warning: Failed to create some connections")

        # Start processors if requested
        if start:
            processor_ids = [exec_sql_proc_id, convert_proc_id, update_attr_id, putfile_id]
            for pid in processor_ids:
                proc_result = get_processor_by_id(pid, NIFI_URL)
                if proc_result["status"]:
                    start_result = start_processor(pid, NIFI_URL)
                    if not start_result["status"]:
                        print(f"Warning: Failed to start processor {pid}")

        return {
            "status": True,
            "pg_id": pg_id,
            "processors": {
                "execute_sql": exec_sql_proc_id,
                "convert_record": convert_proc_id,
                "update_attribute": update_attr_id,
                "putfile": putfile_id
            },
            "output": {
                "directory": output_dir,
                "filename": output_filename
            }
        }
    except Exception as e:
        print(f"Error creating SQL to JSON file flow: {str(e)}")
        return {"status": False, "error": str(e)}


def create_and_start_stream_flow(
    parent_pg_id: str,
    child_pg_name: str,
    command: str,
    http_cs_id: str,
    NIFI_URL: str,
    command_arguments: str = "",
    working_dir: str = ""
) -> Dict[str, Any]:
    """
    Creates and starts a complete stream processing flow.
    
    Args:
        parent_pg_id: Parent Process Group ID
        child_pg_name: Child process group name
        command: Command to execute
        http_cs_id: HTTP context map controller service ID
        NIFI_URL: Base URL of the NiFi instance
        command_arguments: Command arguments
        working_dir: Working directory
        
    Returns:
        Flow creation status and component IDs
    """
    try:
        # Create child Process Group
        pg_result = create_process_group_inside_pg(
            parent_pg_id=parent_pg_id,
            name=child_pg_name,
            NIFI_URL=NIFI_URL,
            position=(200, 200),
            fail_if_exists=False
        )
        
        if not pg_result["status"]:
            return pg_result
            
        child_pg_id = pg_result["id"]

        # Create Input Port
        in_port_result = create_input_port(
            pg_id=child_pg_id,
            name="IN",
            NIFI_URL=NIFI_URL,
            position_id=0
        )
        
        if not in_port_result["status"]:
            return in_port_result
            
        in_port = in_port_result

        # Create ExecuteStreamCommand processor
        exec_proc_result = create_execute_stream_command(
            pg_id=child_pg_id,
            NIFI_URL=NIFI_URL,
            name="Execute_Command",
            command=command,
            command_arguments=command_arguments,
            working_dir=working_dir,
            position_id=1
        )
        
        if not exec_proc_result["status"]:
            return exec_proc_result
            
        exec_proc = exec_proc_result

        # Create Output Port
        out_port_result = create_output_port(
            pg_id=child_pg_id,
            name="OUT",
            NIFI_URL=NIFI_URL,
            position_id=2
        )
        
        if not out_port_result["status"]:
            return out_port_result
            
        out_port = out_port_result

        # Create PutWebSocket processor
        ws_out_result = create_put_websocket(
            pg_id=child_pg_id,
            name=child_pg_name + "_WS_out",
            NIFI_URL=NIFI_URL,
            comp={
                "WebSocket Session Id": "${websocket.session.id}",
                "WebSocket Controller Service Id": "${websocket.controller.service.id}",
                "WebSocket Endpoint Id": "${websocket.endpoint.id}",
                "WebSocket Message Type": "TEXT"
            }
        )
        
        if not ws_out_result["status"]:
            return ws_out_result
            
        ws_out = ws_out_result["data"]

        # Create HandleHttpResponse processor
        http_res_result = add_handle_http_response(
            pg_id=child_pg_id,
            processor_name=child_pg_name,
            NIFI_URL=NIFI_URL,
            http_cs_id=http_cs_id
        )
        
        if not http_res_result["status"]:
            return http_res_result
            
        http_res = http_res_result["data"]

        # Create connections
        connections = [
            # Input Port → ExecuteStreamCommand
            connect_components(
                pg_id=child_pg_id,
                source_id=in_port["id"],
                source_type="INPUT_PORT",
                destination_id=exec_proc["id"],
                destination_type="PROCESSOR",
                NIFI_URL=NIFI_URL
            ),
            # ExecuteStreamCommand → Output Port
            connect_components(
                pg_id=child_pg_id,
                source_id=exec_proc["id"],
                source_type="PROCESSOR",
                destination_id=out_port["id"],
                destination_type="OUTPUT_PORT",
                relationships=["output stream"],
                NIFI_URL=NIFI_URL
            ),
            # ExecuteStreamCommand → PutWebSocket
            connect_components(
                pg_id=child_pg_id,
                source_id=exec_proc["id"],
                source_type="PROCESSOR",
                destination_id=ws_out["id"],
                destination_type="PROCESSOR",
                relationships=["output stream"],
                NIFI_URL=NIFI_URL
            ),
            # ExecuteStreamCommand → HandleHttpResponse
            connect_components(
                pg_id=child_pg_id,
                source_id=exec_proc["id"],
                source_type="PROCESSOR",
                destination_id=http_res["id"],
                destination_type="PROCESSOR",
                relationships=["output stream"],
                NIFI_URL=NIFI_URL
            )
        ]
        
        # Check connection results
        for conn_result in connections:
            if not conn_result["status"]:
                print("Warning: Failed to create some connections")

        # Start processors
        time.sleep(4)
        start_results = [
            start_processor(exec_proc['id'], NIFI_URL),
            start_processor(ws_out['id'], NIFI_URL),
            start_processor(http_res['id'], NIFI_URL)
        ]
        
        for start_result in start_results:
            if not start_result["status"]:
                print("Warning: Failed to start some processors")

        print("✅ Flow created, connected, and started successfully")

        return {
            "status": True,
            "process_group_id": child_pg_id,
            "input_port": in_port,
            "processor": exec_proc,
            "output_port": out_port,
            "websocket_out": ws_out,
            "http_response": http_res
        }
    except Exception as e:
        print(f"Error creating and starting stream flow: {str(e)}")
        return {"status": False, "error": str(e)}


def remove_agent(
    parent_pg_id: str,
    agent_pg_id: str,
    router_id: str,
    rule_name: str,
    NIFI_URL: str
) -> Dict[str, Any]:
    """
    Removes an agent from the flow by stopping components and deleting connections.
    
    Args:
        parent_pg_id: Parent Process Group ID
        agent_pg_id: Agent Process Group ID to remove
        router_id: Router processor ID
        rule_name: RouteOnAttribute rule name to remove
        NIFI_URL: Base URL of the NiFi instance
        
    Returns:
        Operation status
    """
    try:
        # Stop the agent process group
        stop_pg_result = stop_process_group(agent_pg_id, NIFI_URL)
        if not stop_pg_result["status"]:
            print(f"Warning: Failed to stop process group {agent_pg_id}")

        # Stop the router processor
        stop_router_result = stop_processor(router_id, NIFI_URL)
        if not stop_router_result["status"]:
            print(f"Warning: Failed to stop router processor {router_id}")

        # Remove the route rule
        remove_rule_result = remove_route_on_attribute_rule(
            route_proc_id=router_id,
            rule_name=rule_name,
            NIFI_URL=NIFI_URL
        )
        if not remove_rule_result["status"]:
            print(f"Warning: Failed to remove rule {rule_name}")

        # Delete all connections to the agent PG
        delete_conns_result = delete_all_connections_to_pg(agent_pg_id, NIFI_URL)
        if not delete_conns_result["status"]:
            print(f"Warning: Failed to delete some connections to PG {agent_pg_id}")

        # Delete specific processor to child PG connection
        delete_proc_conn_result = delete_processor_to_child_pg_connection(
            parent_pg_id=parent_pg_id,
            processor_id=router_id,
            child_pg_id=agent_pg_id,
            NIFI_URL=NIFI_URL
        )
        if not delete_proc_conn_result["status"]:
            print(f"Warning: Failed to delete processor to child PG connection")

        # Delete the agent process group
        delete_pg_result = delete_process_group(agent_pg_id, NIFI_URL)
        if not delete_pg_result["status"]:
            return delete_pg_result

        # Restart the router processor
        start_router_result = start_processor(router_id, NIFI_URL)
        if not start_router_result["status"]:
            print(f"Warning: Failed to restart router processor {router_id}")

        return {"status": True, "message": f"Agent {agent_pg_id} removed successfully"}
    except Exception as e:
        print(f"Error removing agent: {str(e)}")
        return {"status": False, "error": str(e)}