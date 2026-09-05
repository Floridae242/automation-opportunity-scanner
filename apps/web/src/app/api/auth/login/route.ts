import { proxyAuthEndpoint } from "@/features/auth/proxy";

export const dynamic = "force-dynamic";

export async function POST(request: Request) {
  return proxyAuthEndpoint(request, "POST", "login");
}
