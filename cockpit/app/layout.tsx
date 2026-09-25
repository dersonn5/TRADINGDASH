import type { Metadata } from "next";
import { Sora, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { DashboardHeader } from "@/components/layout/dashboard-header";
import { AuthGate } from "@/components/auth-gate";

const sora = Sora({
  variable: "--font-sans",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

export const metadata: Metadata = {
  title: "Cognitive Trading",
  description: "Pré-sessão, checklist e resultados do operacional WIN",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html
      lang="pt-BR"
      className={`${sora.variable} ${plexMono.variable} dark h-full antialiased`}
    >
      <body className="min-h-full">
        <AuthGate>
          <SidebarProvider>
            <AppSidebar />
            <SidebarInset>
              <DashboardHeader />
              <div className="flex flex-1 flex-col gap-4 p-4 md:p-6">{children}</div>
            </SidebarInset>
          </SidebarProvider>
        </AuthGate>
      </body>
    </html>
  );
}
