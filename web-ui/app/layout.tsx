import { AppSidebar } from "@/components/app-sidebar";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { SiteHeader } from "@/components/site-header";
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AIOM4B - MP3 to M4B Converter",
  description: "Convert MP3 files to M4B format with ease",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          <ThemeProvider
            attribute="class"
            defaultTheme="system"
            enableSystem
            disableTransitionOnChange
          >
            <SidebarProvider>
              <AppSidebar variant="inset" />
              <SidebarInset className="max-h-screen">
                <SiteHeader />
                <div className="container mx-auto flex flex-1 flex-col gap-4 py-4 md:gap-6 md:py-6 min-h-0">
                  {children}
                </div>
              </SidebarInset>
            </SidebarProvider>
          </ThemeProvider>
        </Providers>
      </body>
    </html>
  );
}
