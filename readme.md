## OCPP Relay

A web-based tool designed to act as a relay or proxy between a charge point (CP) and a central system (CSMS)
implementing the Open Charge Point Protocol (OCPP). The tool provides a simple user-interface for displaying 
OCPP JSON messages relayed between the two parties. It also provides additional functionality to inject new OCPP Call 
messages (requests) in either direction and it's response is not relayed back to the other party.

#### Example Use Cases:

* Debugging communication issues between charge point and central system
* Inspecting OCPP messages & flow between charge point and central system


#### Demo:

**Main UI**:

<img src="docs/demo_main_ui.png" alt="Main UI" width="900"/>

**OCPP Event Viewer**:

<img src="docs/demo_ocpp_event_viewer.png" alt="OCPP Event Viewer" width="900"/>
