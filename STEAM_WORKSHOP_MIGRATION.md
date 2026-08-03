# Nexus-to-Steam Workshop Migration

The Nexus integration has been removed from the active application routing and user interface. Existing historical source files and ticket records remain in the repository solely for attribution, migration reference, and audit history.

New installations use the official Palworld Workshop layout:

`<PalServer>/Mods/Workshop/<WorkshopId>/Info.json`

Activation is managed in:

`<PalServer>/Pal/Saved/Config/WindowsServer/PalModSettings.ini`

Existing manually installed UE4SS and PAK mods continue to be supported by the manual installer. Nexus credentials, Nexus Premium, Nexus OAuth, and Nexus API keys are not required by the active Steam Workshop workflow.
