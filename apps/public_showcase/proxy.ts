import { NextResponse, type NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  if (request.nextUrl.pathname === "/reimagining-alberta-ed-flow-intelligence") {
    return NextResponse.redirect(new URL("/Reimagining-Alberta-ED-Flow-Intelligence", request.url), 308);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/reimagining-alberta-ed-flow-intelligence"]
};
