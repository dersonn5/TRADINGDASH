import { NextResponse } from "next/server";
import { DEFAULT_STRATEGIES } from "@/data/strategies";

export async function GET() {
  return NextResponse.json(DEFAULT_STRATEGIES);
}
