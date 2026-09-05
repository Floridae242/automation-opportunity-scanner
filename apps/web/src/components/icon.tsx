import type { CSSProperties } from "react";

const paths = {
  grid: "M3 3h6v6H3z M15 3h6v6h-6z M3 15h6v6H3z M15 15h6v6h-6z",
  book: "M12 5v16 M12 5C8 2 4 3 2 4v15c4-1 7-1 10 2 3-3 6-3 10-2V4c-2-1-6-2-10 1Z",
  pulse: "M2 12h5l3-8 4 16 3-8h5",
  arrow: "M4 12h16 M14 6l6 6-6 6",
  file: "M14 2H5v20h14V7l-5-5Z M14 2v6h5 M8 12h8 M8 16h6",
  check: "m5 12 4 4L19 6",
  layers: "m12 3 10 5-10 5L2 8l10-5Z M2 12l10 5 10-5 M2 16l10 5 10-5",
  chart: "M4 3v17h17 M8 15l4-5 4 2 5-7",
  refresh:
    "M20 7v5h-5 M4 17v-5h5 M5 7a8 8 0 0 1 13-2l2 3 M4 16l2 3a8 8 0 0 0 13-2",
  shield: "m12 2 8 3v7c0 5-8 10-8 10S4 17 4 12V5l8-3Z m-4 10 3 3 5-6",
  folder: "M3 5h7l2 3h9v12H3V5Z",
} as const;

export function Icon({
  name,
  size = 20,
  style,
}: {
  name: keyof typeof paths;
  size?: number;
  style?: CSSProperties;
}) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      style={style}
    >
      <path d={paths[name]} />
    </svg>
  );
}
