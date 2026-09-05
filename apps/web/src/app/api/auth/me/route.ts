import { proxyAuthEndpoint } from "@/features/auth/proxy";

export const dynamic = "force-dynamic";

export async function GET(request: Request) {
  return proxyAuthEndpoint(request, "GET", "me");
}
