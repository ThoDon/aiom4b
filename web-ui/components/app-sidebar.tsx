"use client";

import {
  BarChartIcon,
  Download,
  FolderIcon,
  HelpCircleIcon,
  History,
  LayoutDashboardIcon,
  ListIcon,
  Music,
  Play,
  SettingsIcon,
  Tag,
} from "lucide-react";
import * as React from "react";

import { NavDocuments } from "@/components/nav-documents";
import { NavMain } from "@/components/nav-main";
import { NavSecondary } from "@/components/nav-secondary";
import { NavUser } from "@/components/nav-user";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import Link from "next/link";

const data = {
  user: {
    name: "User",
    email: "user@example.com",
    avatar: "/avatars/user.jpg",
  },
  navMain: [
    {
      title: "Home",
      url: "/",
      icon: Play,
    },
    {
      title: "Jobs",
      url: "/jobs",
      icon: ListIcon,
    },
  ],
  navClouds: [
    {
      title: "Source Folders",
      icon: FolderIcon,
      isActive: true,
      url: "/",
      items: [
        {
          title: "Available Folders",
          url: "/",
        },
        {
          title: "Recent Conversions",
          url: "/jobs",
        },
      ],
    },
    {
      title: "Output Files",
      icon: Download,
      url: "/jobs",
      items: [
        {
          title: "Completed Jobs",
          url: "/jobs",
        },
        {
          title: "Download History",
          url: "/jobs",
        },
      ],
    },
    {
      title: "Analytics",
      icon: BarChartIcon,
      url: "/dashboard",
      items: [
        {
          title: "Conversion Stats",
          url: "/dashboard",
        },
        {
          title: "Performance",
          url: "/dashboard",
        },
      ],
    },
  ],
  navSecondary: [
    {
      title: "Settings",
      url: "#",
      icon: SettingsIcon,
    },
    // {
    //   title: "Help",
    //   url: "#",
    //   icon: HelpCircleIcon,
    // },
  ],
  documents: [
    {
      name: "Source Files",
      url: "/",
      icon: FolderIcon,
    },
    {
      name: "Conversion Logs",
      url: "/jobs",
      icon: History,
    },
    {
      name: "Output Directory",
      url: "/jobs",
      icon: FolderIcon,
    },
  ],
};

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              className="data-[slot=sidebar-menu-button]:!p-1.5"
            >
              <Link href="/">
                <Music className="h-5 w-5" />
                <span className="text-base font-semibold">AIOM4B</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={data.navMain} />
        {/* <NavDocuments items={data.documents} /> */}
      </SidebarContent>
      <SidebarFooter>
        {/* <NavUser user={data.user} /> */}
        <NavSecondary items={data.navSecondary} className="mt-auto" />
      </SidebarFooter>
    </Sidebar>
  );
}
