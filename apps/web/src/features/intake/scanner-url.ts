export function scannerUpstreamUrl(
  base: string,
  path: string,
  requestUrl: string,
): URL {
  const upstream = new URL(`${base.replace(/\/$/, "")}/${path}`);
  upstream.search = new URL(requestUrl).search;
  return upstream;
}
