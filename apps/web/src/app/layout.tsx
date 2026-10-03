import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";

import { Providers } from "./providers";
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
  title: "Dragon Academy",
  description:
    "Find the dragon that chooses you, then train it, talk to it and adventure together.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col">
        <Providers>
          <header className="border-line border-b">
            <nav className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-4 py-3">
              <Link href="/" className="font-semibold tracking-tight">
                Dragon Academy
              </Link>
              <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
                <Link href="/dragon-book" className="text-muted hover:text-foreground">
                  Dragon Book
                </Link>
                <Link href="/academy/quiz" className="text-muted hover:text-foreground">
                  Find your dragon
                </Link>
                <Link href="/dragon" className="text-muted hover:text-foreground">
                  My dragon
                </Link>
                <Link href="/train" className="text-muted hover:text-foreground">
                  Train
                </Link>
                <Link href="/chat" className="text-muted hover:text-foreground">
                  Chat
                </Link>
                <Link href="/adventure" className="text-muted hover:text-foreground">
                  Adventures
                </Link>
                <Link href="/island" className="text-muted hover:text-foreground">
                  Island
                </Link>
                <Link href="/login" className="text-muted hover:text-foreground">
                  Sign in
                </Link>
              </div>
            </nav>
          </header>
          <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-10">{children}</main>
          <footer className="border-line text-muted border-t">
            <p className="mx-auto max-w-5xl px-4 py-6 text-xs">
              Fan project. Not affiliated with or endorsed by DreamWorks Animation or Universal
              Pictures. How to Train Your Dragon names and characters belong to their owners.
            </p>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
