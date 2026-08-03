import * as React from "react";
import { universityApi } from "@/api";
import { UNIVERSITY_UPDATED } from "@/lib/questCompletion";
import type { UniversityCatalog, UniversityCourse, UniversityStep } from "@/types/models";

type Listener = () => void;

let cachedCatalog: UniversityCatalog | null = null;
let inFlightRequest: Promise<UniversityCatalog | null> | null = null;
let universityEventBound = false;
const listeners = new Set<Listener>();

function emitChange(): void {
  for (const listener of listeners) listener();
}

function getSnapshot(): UniversityCatalog | null {
  return cachedCatalog;
}

function subscribe(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function loadCatalog(force = false): Promise<UniversityCatalog | null> {
  if (!force && cachedCatalog) return Promise.resolve(cachedCatalog);
  if (inFlightRequest) return inFlightRequest;

  inFlightRequest = universityApi
    .getCatalog()
    .then((catalog) => {
      cachedCatalog = catalog;
      emitChange();
      return catalog;
    })
    .catch(() => cachedCatalog)
    .finally(() => {
      inFlightRequest = null;
    });

  return inFlightRequest;
}

function bindUniversityUpdateEvent(): void {
  if (universityEventBound || typeof window === "undefined") return;
  universityEventBound = true;
  window.addEventListener(UNIVERSITY_UPDATED, () => {
    void loadCatalog(true);
  });
}

/**
 * Shared cached read side for the active University course and next step.
 * The catalog is loaded once per browser session and refreshed only after a
 * real University progress event. This prevents every mounted quest prompt
 * from polling /api/university independently.
 */
export function useActiveQuestStep(): {
  catalog: UniversityCatalog | null;
  activeCourse: UniversityCourse | null;
  nextStep: UniversityStep | null;
} {
  bindUniversityUpdateEvent();
  const catalog = React.useSyncExternalStore(subscribe, getSnapshot, getSnapshot);

  React.useEffect(() => {
    void loadCatalog(false);
  }, []);

  const activeCourse = catalog?.courses.find((course) => course.id === catalog.activeCourse) ?? null;
  const nextStep = activeCourse?.steps.find((step) => !step.completed && !step.locked) ?? null;

  return { catalog, activeCourse, nextStep };
}
