"use client"

import ReactMarkdown from "react-markdown"

export function LlmMarkdown({ text }: { text: string }) {
  if (!text.trim()) return null
  return (
    <ReactMarkdown
      components={{
        p: ({ children }) => (
          <p className="text-[13px] text-muted-foreground leading-relaxed mb-2 last:mb-0">
            {children}
          </p>
        ),
        ul: ({ children }) => (
          <ul className="list-disc pl-5 space-y-1 text-[13px] text-muted-foreground">
            {children}
          </ul>
        ),
        ol: ({ children }) => (
          <ol className="list-decimal pl-5 space-y-1 text-[13px] text-muted-foreground">
            {children}
          </ol>
        ),
        li: ({ children }) => (
          <li className="leading-relaxed">
            {children}
          </li>
        ),
        strong: ({ children }) => (
          <strong className="text-foreground/90 font-semibold">{children}</strong>
        ),
        em: ({ children }) => (
          <em className="italic">{children}</em>
        ),
        a: ({ children, href }) => (
          <a className="text-blue-600 underline underline-offset-2" href={href} target="_blank" rel="noreferrer">
            {children}
          </a>
        ),
      }}
    >
      {text}
    </ReactMarkdown>
  )
}

export function InsightCard({ title, body }: { title: string; body: string }) {
  if (!body.trim()) return null
  return (
    <div className="rounded-xl border border-border/40 bg-card p-4">
      <p className="text-[11px] font-medium uppercase tracking-[.07em] text-muted-foreground/60 mb-2">{title}</p>
      <LlmMarkdown text={body} />
    </div>
  )
}
