import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { InlineScript } from "@/components/InlineScript";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "ARIA — Automated Requirements Intelligence Agent",
  description:
    "Capture a requirement once. Watch a multi-agent pipeline turn it into a Notion BRD, GitHub tech doc, and Jira backlog item.",
};

// Runs synchronously before first paint: picks dark theme between 7pm-7am local
// time, light otherwise, unless the user has manually overridden it this session.
const THEME_SCRIPT = `(function(){try{
  var override=localStorage.getItem("aria-theme-override");
  var theme;
  if(override==="light"||override==="dark"){theme=override;}
  else{var h=new Date().getHours();theme=(h>=19||h<7)?"dark":"light";}
  document.documentElement.setAttribute("data-theme",theme);
}catch(e){}})()`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      data-theme="light"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        <InlineScript html={THEME_SCRIPT} />
      </head>
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
