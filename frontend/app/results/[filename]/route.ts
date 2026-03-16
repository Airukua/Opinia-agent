import { NextResponse } from "next/server"

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ filename: string }> }
) {
  const { filename } = await params
  const apiBase = process.env.API_URL
  if (!apiBase) {
    return NextResponse.json({ error: "API_URL is not set" }, { status: 500 })
  }

  const url = new URL(`/results/${filename}`, apiBase)
  const res = await fetch(url, { cache: "no-store" })
  const contentType = res.headers.get("content-type") ?? "application/json"

  if (!res.ok) {
    return NextResponse.json({ error: "Upstream error" }, { status: res.status })
  }

  const data = await res.text()
  return new NextResponse(data, {
    status: 200,
    headers: {
      "content-type": contentType,
    },
  })
}
