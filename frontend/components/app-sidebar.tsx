"use client"

import * as React from "react"
import { usePathname } from "next/navigation"

import { NavMain } from "@/components/nav-main"
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar"
import { TerminalSquareIcon, BookOpenIcon, BookIcon } from "lucide-react"

// This is sample data.
const data = {
  navMain: [
    {
      label: "Main Workflow",
      items: [
        {
          title: "Overview",
          url: "/dashboard/overview",
          icon: (
            <TerminalSquareIcon
            />
          ),
          isActive: true,
        },
        {
          title: "Tutorial",
          url: "/dashboard/tutorial",
          icon: (
            <BookOpenIcon
            />
          ),
        },
        {
          title: "License",
          url: "/dashboard/license",
          icon: (
            <BookIcon
            />
          ),
        },
      ],
    },
  ],
  projects: [],
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const pathname = usePathname()

  const isActiveUrl = React.useCallback(
    (url: string) => {
      if (url === "/dashboard/overview" && (pathname === "/" || pathname === "/dashboard/overview")) {
        return true
      }

      return pathname === url
    },
    [pathname]
  )

  const navGroups = React.useMemo(
    () =>
      data.navMain.map((group) => ({
        ...group,
        items: group.items.map((item) => ({
          ...item,
          isActive: isActiveUrl(item.url),
        })),
      })),
    [isActiveUrl]
  )

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <div className="flex items-center gap-3 px-2 py-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-md border border-border/50 bg-muted/30">
            <img
              src="/favicon.svg"
              alt="Opinia AI Agent"
              className="h-5 w-5"
            />
          </div>
          <div className="min-w-0">
            <p className="text-[13px] font-semibold leading-tight text-foreground">
              Opinia AI Agent
            </p>
            <p className="text-[11px] text-muted-foreground/60">
              Analisis Komen YouTube
            </p>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <NavMain groups={navGroups} />
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  )
}
