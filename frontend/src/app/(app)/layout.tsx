import { AppSidebar } from "@/components/app-sidebar"
import { SidebarInset, SidebarProvider } from "@/components/ui/sidebar"
import { TooltipProvider } from "@/components/ui/tooltip"

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <SidebarProvider defaultOpen>
      <TooltipProvider>
        <AppSidebar />
        <SidebarInset className="h-svh overflow-hidden">
          {children}
        </SidebarInset>
      </TooltipProvider>
    </SidebarProvider>
  )
}
