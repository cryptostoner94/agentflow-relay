export const metadata = { title: "AgentFlow Relay", description: "Universal agent relay infrastructure" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="en"><body>{children}</body></html>;
}
