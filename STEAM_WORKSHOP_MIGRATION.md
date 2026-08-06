# Steam Workshop and Nexus Mods Integration

Exiles Game Manager supports Steam Workshop, Nexus Mods and manual mod installation as separate workflows. This document replaces the obsolete statement that Nexus integration had been removed.

## Steam Workshop

Steam Workshop metadata is obtained from Steam services. Downloads and dedicated-server operations are performed through the locally installed SteamCMD client. Anonymous access is used where Steam permits it; temporary authenticated SteamCMD access is available only when explicitly initiated by the super administrator.

## Nexus Mods

Public Nexus browsing uses Nexus public metadata APIs. OAuth 2.0 with PKCE is used for connected-account functionality. Direct automatic downloads require the permissions and membership level required by Nexus Mods. The user's OAuth record remains on the local Windows machine and is protected using Windows DPAPI.

## Manual files

A super administrator may select a local `.zip` or `.7z` mod archive. EGM stages the archive locally, computes its MD5 digest and may submit that digest to Nexus Mods for catalog matching. The complete archive is not sent by the hash-lookup step. Unmatched files may still be installed as unverified local files after the administrator confirms the operation.

## Platform rules

All Steam, Nexus Mods, game, mod-author and copyright terms continue to apply. EGM does not bypass Premium requirements, access controls, rate limits or content restrictions.
