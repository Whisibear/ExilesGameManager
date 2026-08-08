import type { ReactNode } from "react";
import type { ServerStatus } from "@/types/models";
import type { GameCapability } from "@/lib/gameCapabilities";
import {
  supportsAnyCapability,
  supportsCapability,
} from "@/lib/gameCapabilities";

interface CapabilityBoundaryProps {
  status: ServerStatus | null | undefined;
  capability?: GameCapability;
  anyOf?: readonly GameCapability[];
  children: ReactNode;
  fallback?: ReactNode;
}

export function CapabilityBoundary({
  status,
  capability,
  anyOf,
  children,
  fallback = null,
}: CapabilityBoundaryProps) {
  const supported = capability
    ? supportsCapability(status, capability)
    : supportsAnyCapability(status, anyOf ?? []);

  return supported ? children : fallback;
}
