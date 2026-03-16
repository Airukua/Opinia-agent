import type { Metadata } from "next";
import { Geist, Geist_Mono, Inter } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AppSidebar } from "@/components/app-sidebar";
import {
  SidebarInset,
  SidebarProvider,
} from "@/components/ui/sidebar";
import { ThemeProvider } from "@/components/theme-provider";

const inter = Inter({subsets:['latin'],variable:'--font-sans'});

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Opinia AI Agent — Analisis Komen YouTube",
    template: "%s — Opinia AI Agent",
  },
  description:
    "Opinia AI Agent membantu menganalisis komentar YouTube: sentimen, toksisitas, kata kunci, topik utama, dan insight konten.",
  applicationName: "Opinia AI Agent",
  icons: {
    icon: "/favicon.svg",
  },
  openGraph: {
    title: "Opinia AI Agent — Analisis Komen YouTube",
    description:
      "Analisa komentar YouTube secara otomatis: sentimen, toksisitas, kata kunci, topik utama, dan insight konten.",
    type: "website",
    images: ["/og-images.png"],
  },
  twitter: {
    card: "summary_large_image",
    title: "Opinia AI Agent — Analisis Komen YouTube",
    description:
      "Analisa komentar YouTube secara otomatis: sentimen, toksisitas, kata kunci, topik utama, dan insight konten.",
    images: ["/og-images.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="id" className={cn("font-sans", inter.variable)} suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ThemeProvider>
          <TooltipProvider>
            <SidebarProvider>
              <AppSidebar />
              <SidebarInset>{children}</SidebarInset>
            </SidebarProvider>
          </TooltipProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
