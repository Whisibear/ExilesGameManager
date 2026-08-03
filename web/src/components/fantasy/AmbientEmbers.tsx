import { useMemo } from "react";

interface Node {
  id: number;
  left: string;
  size: number;
  duration: number;
  delay: number;
  tone: "cyan" | "lime" | "purple";
}

const COLORS: Record<Node["tone"], string> = {
  cyan: "rgba(0,212,255,0.42)",
  lime: "rgba(124,252,0,0.34)",
  purple: "rgba(139,92,246,0.3)",
};

export function AmbientEmbers({ count = 14 }: { count?: number }) {
  const nodes = useMemo<Node[]>(
    () => Array.from({ length: count }, (_, i) => ({
      id: i,
      left: `${Math.round(Math.random() * 100)}%`,
      size: 1 + Math.random() * 2.4,
      duration: 18 + Math.random() * 18,
      delay: -Math.random() * 24,
      tone: (["cyan", "lime", "purple"] as const)[Math.floor(Math.random() * 3)],
    })),
    [count]
  );

  return (
    <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden" aria-hidden="true">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_12%_22%,rgba(124,252,0,0.035),transparent_30%),radial-gradient(circle_at_88%_18%,rgba(0,212,255,0.05),transparent_34%),radial-gradient(circle_at_72%_86%,rgba(139,92,246,0.035),transparent_32%)]" />
      {nodes.map((node) => (
        <span
          key={node.id}
          className="absolute bottom-[-10px] rounded-full animate-drift"
          style={{
            left: node.left,
            width: node.size,
            height: node.size,
            background: COLORS[node.tone],
            boxShadow: `0 0 9px 2px ${COLORS[node.tone]}`,
            animationDuration: `${node.duration}s`,
            animationDelay: `${node.delay}s`,
          }}
        />
      ))}
    </div>
  );
}
